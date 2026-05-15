"""
ExamIQ Analysis API
Main analysis pipeline endpoint + dashboard data.
"""
import json
import logging
from fastapi import APIRouter, HTTPException
from app.core.config import DATA_DIR
from app.models.schemas import AnalyzeRequest, AnalyzeResponse, AnalysisResult
from app.api.upload import get_uploaded_data
from app.services.hf_topic_extractor import extract_topics_from_hf_space
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
    """Run the full analysis pipeline. Uses HF Space for topic extraction."""
    global _latest_result

    data = get_uploaded_data()
    if not data["papers"]:
        raise HTTPException(status_code=400, detail="No papers uploaded. Please upload exam papers first.")

    try:
        # ─── HF Space Topic Extraction ───
        # Collect file paths for papers that have been saved to disk
        file_paths = [p["path"] for p in data["papers"] if p.get("path")]

        # Filter to HF-Space-supported formats (PDF, DOCX, DOC, TXT)
        supported_exts = (".pdf", ".docx", ".doc", ".txt")
        hf_file_paths = [fp for fp in file_paths if fp.lower().endswith(supported_exts)]

        if not hf_file_paths:
            raise HTTPException(
                status_code=400,
                detail="No supported files found. Please upload PDF, DOCX, DOC, or TXT files."
            )

        logger.info(f"Sending {len(hf_file_paths)} files to HF Space for topic extraction")
        hf_result = extract_topics_from_hf_space(hf_file_paths)

        if not hf_result or not hf_result.get("questions"):
            raise HTTPException(
                status_code=400,
                detail="Could not extract questions from uploaded papers. "
                       "The HF Space may be unavailable or the files may be unreadable."
            )

        all_questions = hf_result["questions"]
        topic_analyses_from_hf = hf_result.get("topic_analyses", [])
        logger.info(f"HF Space extracted {len(all_questions)} questions, {len(topic_analyses_from_hf)} topics")

        # Assign subject to all questions
        for q in all_questions:
            if not q.subject:
                q.subject = request.subject

        # ─── Topic Analysis ───
        if topic_analyses_from_hf:
            topic_analyses = topic_analyses_from_hf
        else:
            topic_analyses = analyze_topics(all_questions)

        # Syllabus coverage (defaulted since syllabus upload is removed)
        coverage = compute_syllabus_coverage(topic_analyses, [])

        # Importance scoring — always run to ensure 0-100 scale for downstream consumers
        topic_analyses = compute_importance_scores(topic_analyses)

        # Predictive intelligence
        all_years = sorted(set(q.year for q in all_questions if q.year > 0))
        predictions = generate_predictions(topic_analyses, all_years)

        # Dashboard data
        dashboard = build_dashboard_data(all_questions, topic_analyses, coverage)

        # Study plan
        study_plan = generate_study_plan(topic_analyses, total_days=request.exam_days, hours_per_day=request.hours_per_day)

        # Practice questions
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

        return AnalyzeResponse(
            success=True,
            message=f"Analysis complete (HF Space): {len(all_questions)} questions, {len(topic_analyses)} topics",
            result=_latest_result
        )

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


