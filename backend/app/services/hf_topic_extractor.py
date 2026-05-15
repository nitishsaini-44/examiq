"""
ExamIQ HF Space Topic Extractor
Calls the Hugging Face Space Gradio API to extract topics from exam papers.
Uses the deployed model at: https://nitishsaini44-exam-topic-analyzer.hf.space
"""
import re
import uuid
import logging
from pathlib import Path
from typing import Optional
from app.core.config import HF_SPACE_URL
from app.models.schemas import Question, QuestionType, Difficulty, TopicAnalysis

logger = logging.getLogger(__name__)


def extract_topics_from_hf_space(file_paths: list[str]) -> Optional[dict]:
    """
    Send files directly to the HF Space Gradio API for topic extraction.
    
    Args:
        file_paths: List of absolute file paths to exam papers (PDF, DOCX, TXT)
    
    Returns:
        dict with keys:
            - "analysis_text": Raw markdown analysis text
            - "topic_scores": List of dicts with topic score data
            - "questions": List of Question objects parsed from the response
            - "topic_analyses": List of TopicAnalysis objects
        Returns None if the API call fails.
    """
    try:
        from gradio_client import Client, handle_file
    except ImportError:
        logger.error("gradio_client not installed. Run: pip install gradio_client")
        return None

    try:
        logger.info(f"Connecting to HF Space: {HF_SPACE_URL}")
        client = Client(HF_SPACE_URL)

        # Wrap file paths for Gradio upload
        file_handles = [handle_file(fp) for fp in file_paths]

        logger.info(f"Sending {len(file_paths)} files to HF Space for analysis...")
        result = client.predict(
            files=file_handles,
            api_name="/analyze_files"
        )

        # Result is a tuple: (analysis_text: str, topic_scores_dataframe: dict)
        if not result or len(result) < 2:
            logger.error(f"Unexpected HF Space response format: {result}")
            return None

        analysis_text = result[0]  # Markdown text with analysis
        topic_scores_df = result[1]  # Dict with 'headers' and 'data' keys

        logger.info(f"HF Space analysis complete. Text length: {len(analysis_text)}")
        logger.debug(f"Topic scores headers: {topic_scores_df.get('headers', [])}")

        # Parse the response into structured data
        parsed = _parse_hf_response(analysis_text, topic_scores_df)
        return parsed

    except Exception as e:
        logger.error(f"HF Space topic extraction failed: {e}", exc_info=True)
        return None


def _parse_hf_response(analysis_text: str, topic_scores_df: dict) -> dict:
    """
    Parse the HF Space Gradio response into structured Question and TopicAnalysis objects.
    """
    questions = []
    topic_analyses = []

    # Parse the dataframe (topic scores table)
    headers = topic_scores_df.get("headers", [])
    data = topic_scores_df.get("data", [])

    if headers and data:
        topic_analyses = _parse_topic_scores_dataframe(headers, data)

    # Parse the analysis text for additional question-level data
    questions = _parse_analysis_text(analysis_text, topic_analyses)

    return {
        "analysis_text": analysis_text,
        "topic_scores": data,
        "questions": questions,
        "topic_analyses": topic_analyses,
    }


def _parse_topic_scores_dataframe(
    headers: list, data: list[list]
) -> list[TopicAnalysis]:
    """
    Parse the Gradio dataframe response into TopicAnalysis objects.
    The dataframe typically has columns like: Topic, Score, Frequency, etc.
    """
    analyses = []

    # Build a column index map (case-insensitive)
    col_map = {}
    for i, h in enumerate(headers):
        col_map[str(h).lower().strip()] = i

    for row in data:
        if not row:
            continue

        # Try to extract topic name from common column names
        topic = _get_col_value(row, col_map, ["topic", "name", "subject", "concept"])
        if not topic:
            # Use first column as topic name
            topic = str(row[0]).strip() if row else "Unknown"

        # Skip empty/header rows
        if not topic or topic.lower() in ("topic", "name", "total", ""):
            continue

        # Extract numeric scores
        score = _get_numeric_col(row, col_map, ["score", "importance", "weight", "importance score", "importance_score"])
        frequency = _get_numeric_col(row, col_map, ["frequency", "count", "freq", "occurrences", "times appeared"])
        marks = _get_numeric_col(row, col_map, ["marks", "total marks", "total_marks", "weightage"])

        # Extract trend if available
        trend = _get_col_value(row, col_map, ["trend", "direction", "pattern"])

        analysis = TopicAnalysis(
            topic=topic,
            frequency=int(frequency) if frequency else max(1, int(score * 10) if score else 1),
            total_marks=marks or 0,
            avg_marks=marks / max(frequency, 1) if marks else 0,
            importance_score=score or 0.0,
            trend=trend if trend and trend.lower() in ("increasing", "decreasing", "stable") else "stable",
        )
        analyses.append(analysis)

    # Sort by importance score descending
    analyses.sort(key=lambda a: a.importance_score, reverse=True)

    # Assign ranks
    for i, a in enumerate(analyses):
        a.rank = i + 1

    logger.info(f"Parsed {len(analyses)} topic analyses from HF Space dataframe")
    return analyses


def _parse_analysis_text(
    analysis_text: str, topic_analyses: list[TopicAnalysis]
) -> list[Question]:
    """
    Parse the analysis markdown text to create Question objects.
    Uses the topic analyses to assign topics to generated questions.
    """
    questions = []

    if not topic_analyses:
        return questions

    # Create questions based on topic analyses
    # Each topic gets synthetic questions proportional to its frequency
    for analysis in topic_analyses:
        freq = max(1, analysis.frequency)
        for i in range(freq):
            q = Question(
                id=str(uuid.uuid4())[:8],
                text=f"{analysis.topic} - Question {i + 1}",
                topic=analysis.topic,
                marks=analysis.avg_marks if analysis.avg_marks > 0 else 5.0,
                question_type=QuestionType.UNKNOWN,
                difficulty=_estimate_difficulty_from_score(analysis.importance_score),
                year=0,
            )
            questions.append(q)

    # Try to extract real questions/topics from the analysis text
    _enrich_questions_from_text(questions, analysis_text)

    logger.info(f"Created {len(questions)} questions from HF Space analysis")
    return questions


def _enrich_questions_from_text(
    questions: list[Question], analysis_text: str
) -> None:
    """
    Try to extract additional details from the analysis markdown text
    and enrich existing questions.
    """
    # Extract year mentions from text
    year_matches = re.findall(r'\b(20\d{2})\b', analysis_text)
    years = sorted(set(int(y) for y in year_matches))

    if years and questions:
        # Distribute years across questions
        for i, q in enumerate(questions):
            if years:
                q.year = years[i % len(years)]

    # Try to extract difficulty mentions
    text_lower = analysis_text.lower()
    if "difficult" in text_lower or "hard" in text_lower or "complex" in text_lower:
        # Mark some questions as hard
        for q in questions[:len(questions) // 3]:
            q.difficulty = Difficulty.HARD


def _estimate_difficulty_from_score(score: float) -> Difficulty:
    """Estimate difficulty based on importance score."""
    if score >= 0.7:
        return Difficulty.HARD
    elif score >= 0.4:
        return Difficulty.MEDIUM
    else:
        return Difficulty.EASY


def _get_col_value(
    row: list, col_map: dict, possible_names: list[str]
) -> Optional[str]:
    """Get a string value from a row by trying multiple possible column names."""
    for name in possible_names:
        if name in col_map:
            idx = col_map[name]
            if idx < len(row) and row[idx] is not None:
                val = str(row[idx]).strip()
                if val:
                    return val
    return None


def _get_numeric_col(
    row: list, col_map: dict, possible_names: list[str]
) -> Optional[float]:
    """Get a numeric value from a row by trying multiple possible column names."""
    for name in possible_names:
        if name in col_map:
            idx = col_map[name]
            if idx < len(row) and row[idx] is not None:
                try:
                    return float(row[idx])
                except (ValueError, TypeError):
                    continue
    return None
