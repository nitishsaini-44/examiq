"""
ExamIQ Planner API
Study planner and practice question endpoints.
"""
import logging
from fastapi import APIRouter, HTTPException
from app.api.analysis import get_results
from app.models.schemas import StudyPlan

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["planner"])


@router.get("/planner")
async def get_study_plan():
    """Get the generated study plan (STEP 7)."""
    result = await get_results()
    return result.study_plan


@router.get("/practice")
async def get_practice_questions():
    """Get practice questions (STEP 8)."""
    result = await get_results()
    return result.practice_questions


@router.get("/topics")
async def get_topic_rankings():
    """Get ranked topic analysis table."""
    result = await get_results()
    return result.topic_rankings


@router.get("/coverage")
async def get_syllabus_coverage():
    """Get syllabus coverage report."""
    result = await get_results()
    return result.syllabus_coverage
