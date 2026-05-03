"""
ExamIQ Analysis API
Main analysis pipeline endpoint + dashboard data.
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from app.core.config import DATA_DIR, GEMINI_API_KEY
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, AnalysisResult
from app.api.upload import get_uploaded_data
from app.services.extractor import extract_questions, map_to_syllabus, parse_syllabus_text
from app.services.gemini_extractor import extract_questions_with_gemini, extract_syllabus_with_gemini
from app.services.embeddings import generate_embeddings, cluster_questions, detect_concept_repetition
from app.services.analyzer import analyze_topics, compute_syllabus_coverage, build_dashboard_data
from app.services.scorer import compute_importance_scores
from app.services.predictor import generate_predictions
from app.services.planner import generate_study_plan
from app.services.generator import generate_practice_questions

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["analysis"])

# Cache latest result
_latest_result: AnalysisResult | None = None


@router.post("/analyze", response_model=AnalyzeResponse)
async def run_analysis(request: AnalyzeRequest):
    """Run the full 8-step analysis pipeline."""
    global _latest_result

    data = get_uploaded_data()
    if not data["papers"]:
        raise HTTPException(status_code=400, detail="No papers uploaded. Please upload exam papers first.")

    try:
        # STEP 1: Extract questions
        all_questions = []
        papers_with_text = [p for p in data["papers"] if p.get("text", "").strip()]

        if not papers_with_text:
            raise HTTPException(
                status_code=400,
                detail="No text could be extracted from uploaded papers. "
                       "This usually means Tesseract OCR is not installed (needed for scanned PDFs). "
                       "Install Tesseract and re-upload, or try the Demo mode."
            )

        # Try Gemini-powered extraction first (much more accurate)
        use_gemini = bool(GEMINI_API_KEY)
        if use_gemini:
            logger.info("Using Gemini API for question extraction")
            for paper in papers_with_text:
                questions = extract_questions_with_gemini(
                    paper["text"], year=paper.get("year", 0), subject=request.subject
                )
                all_questions.extend(questions)

        # Fallback to regex-based extraction if Gemini didn't work
        if not all_questions:
            logger.info("Falling back to regex-based extraction")
            for paper in papers_with_text:
                questions = extract_questions(paper["text"], year=paper.get("year", 0), subject=request.subject)
                all_questions.extend(questions)

        if not all_questions:
            raise HTTPException(status_code=400, detail="Could not extract questions from uploaded papers. The text may be too short or unstructured.")

        # Parse syllabus
        syllabus_items = []
        if data.get("syllabus_text"):
            if use_gemini:
                # Try Gemini for syllabus too
                gemini_syllabus = extract_syllabus_with_gemini(data["syllabus_text"])
                if gemini_syllabus:
                    from app.models.schemas import SyllabusItem
                    syllabus_items = [
                        SyllabusItem(topic=s.get("topic", ""), subtopics=s.get("subtopics", []), unit=s.get("unit"))
                        for s in gemini_syllabus if s.get("topic")
                    ]
            if not syllabus_items:
                syllabus_items = parse_syllabus_text(data["syllabus_text"])
            all_questions = map_to_syllabus(all_questions, syllabus_items)

        # STEP 1 cont. + STEP 2: Embeddings and clustering
        texts = [q.text for q in all_questions]
        embeddings = generate_embeddings(texts)

        if embeddings is not None and len(embeddings) > 2:
            n_clusters = min(10, max(2, len(all_questions) // 3))
            labels = cluster_questions(embeddings, n_clusters=n_clusters)
            for i, q in enumerate(all_questions):
                q.cluster_id = int(labels[i])

            # Assign topic names from clusters if no syllabus mapping
            _assign_cluster_topics(all_questions)

        # STEP 2 + 3: Analyze topics
        topic_analyses = analyze_topics(all_questions)
        coverage = compute_syllabus_coverage(topic_analyses, syllabus_items)

        # STEP 4: Importance scoring
        topic_analyses = compute_importance_scores(topic_analyses)

        # STEP 5: Predictive intelligence
        all_years = sorted(set(q.year for q in all_questions if q.year > 0))
        predictions = generate_predictions(topic_analyses, all_years)

        # STEP 6: Dashboard data
        dashboard = build_dashboard_data(all_questions, topic_analyses, coverage)

        # STEP 7: Study plan
        study_plan = generate_study_plan(topic_analyses, total_days=request.exam_days, hours_per_day=request.hours_per_day)

        # STEP 8: Practice questions
        practice = generate_practice_questions(topic_analyses, all_questions)

        # Build result
        _latest_result = AnalysisResult(
            questions=all_questions,
            topic_rankings=topic_analyses,
            syllabus_coverage=coverage,
            predictions=predictions,
            dashboard_data=dashboard,
            study_plan=study_plan,
            practice_questions=practice
        )

        # Save to disk
        result_file = DATA_DIR / "analysis_result.json"
        with open(result_file, "w", encoding="utf-8") as f:
            f.write(_latest_result.model_dump_json(indent=2))

        return AnalyzeResponse(success=True, message=f"Analysis complete: {len(all_questions)} questions, {len(topic_analyses)} topics", result=_latest_result)

    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Analysis failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")


@router.get("/results")
async def get_results():
    """Get the latest analysis results."""
    global _latest_result

    if _latest_result:
        return _latest_result

    result_file = DATA_DIR / "analysis_result.json"
    if result_file.exists():
        with open(result_file, "r", encoding="utf-8") as f:
            _latest_result = AnalysisResult.model_validate_json(f.read())
        return _latest_result

    raise HTTPException(status_code=404, detail="No analysis results found. Run analysis first.")


@router.get("/dashboard")
async def get_dashboard():
    """Get dashboard-ready chart data (STEP 6)."""
    result = await get_results()
    return result.dashboard_data


@router.get("/predictions")
async def get_predictions():
    """Get predictive insights (STEP 5)."""
    result = await get_results()
    return result.predictions


@router.post("/demo", response_model=AnalyzeResponse)
async def run_demo():
    """Load demo data for testing/demonstration."""
    global _latest_result
    from app.services.demo_data import generate_demo_data
    _latest_result = generate_demo_data()
    return AnalyzeResponse(
        success=True,
        message="Demo data loaded: 99 questions, 12 topics across 5 years",
        result=_latest_result
    )


def _assign_cluster_topics(questions):
    """Assign topic names to questions that don't have syllabus mapping."""
    from collections import Counter

    # Words to exclude from auto-generated topic names
    STOPWORDS = {
        'course', 'code', 'credit', 'marks', 'question', 'answer', 'write',
        'explain', 'describe', 'discuss', 'define', 'state', 'following',
        'given', 'using', 'figure', 'figures', 'right', 'indicate',
        'total', 'maximum', 'attempt', 'paper', 'examination', 'university',
        'college', 'institute', 'semester', 'module', 'scheme', 'subject',
        'branch', 'regular', 'supply', 'supplementary', 'annual',
        'duration', 'hours', 'minutes', 'time', 'note', 'instruction',
        'instructions', 'candidates', 'students', 'compulsory', 'optional',
        'section', 'part', 'number', 'registration', 'roll', 'date',
        'writing', 'anything', 'suitable', 'assume', 'necessary',
        'diagram', 'diagrams', 'sketch', 'sketches', 'neat', 'neatly',
        'clearly', 'legibly', 'brief', 'short', 'detail', 'apply',
        'solve', 'calculate', 'derive', 'prove', 'show', 'obtain',
        'consider', 'example', 'examples', 'different', 'various',
        'types', 'methods', 'method', 'technique', 'techniques',
        'advantage', 'advantages', 'disadvantage', 'disadvantages',
        'compare', 'contrast', 'between', 'mention', 'significance',
        'important', 'importance', 'properties', 'characteristics',
        'applications', 'application', 'referred', 'about',
    }

    cluster_questions_map = {}
    for q in questions:
        if q.cluster_id >= 0:
            cluster_questions_map.setdefault(q.cluster_id, []).append(q)

    for cluster_id, qs in cluster_questions_map.items():
        # Use existing topic if any question has one
        existing = [q.topic for q in qs if q.topic]
        if existing:
            topic = Counter(existing).most_common(1)[0][0]
        else:
            # Generate topic from common meaningful words (excluding stopwords)
            all_words = []
            for q in qs:
                words = [
                    w.lower() for w in q.text.split()
                    if len(w) > 4 and w.isalpha() and w.lower() not in STOPWORDS
                ]
                all_words.extend(words)
            common = Counter(all_words).most_common(3)
            topic = " ".join(w for w, _ in common).title() if common else f"Topic {cluster_id + 1}"

        for q in qs:
            if not q.topic:
                q.topic = topic

