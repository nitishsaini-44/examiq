"""
ExamIQ Pydantic Schemas
Data models for the entire analysis pipeline.
"""
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum


class QuestionType(str, Enum):
    MCQ = "MCQ"
    SHORT = "Short Answer"
    LONG = "Long Answer"
    NUMERICAL = "Numerical"
    CASE_BASED = "Case-Based"
    UNKNOWN = "Unknown"


class Difficulty(str, Enum):
    EASY = "Easy"
    MEDIUM = "Medium"
    HARD = "Hard"


class Priority(str, Enum):
    CRITICAL = "Critical"
    HIGH = "High"
    MEDIUM = "Medium"
    LOW = "Low"


# ─── Input Models ───

class SyllabusItem(BaseModel):
    topic: str
    subtopics: list[str] = []
    unit: Optional[str] = None


class Syllabus(BaseModel):
    subject: str
    items: list[SyllabusItem]


# ─── Question Models ───

class Question(BaseModel):
    id: str = ""
    text: str
    subject: str = ""
    topic: str = ""
    subtopic: str = ""
    question_type: QuestionType = QuestionType.UNKNOWN
    marks: float = 0
    difficulty: Difficulty = Difficulty.MEDIUM
    year: int = 0
    page: int = 0
    cluster_id: int = -1


# ─── Analysis Models ───

class TopicAnalysis(BaseModel):
    topic: str
    frequency: int = 0
    total_marks: float = 0
    avg_marks: float = 0
    years_appeared: list[int] = []
    trend: str = "stable"  # increasing / decreasing / stable
    trend_score: float = 0.0
    difficulty_distribution: dict[str, int] = {}
    question_types: dict[str, int] = {}
    importance_score: float = 0.0
    priority: Priority = Priority.MEDIUM
    rank: int = 0


class SyllabusCoverage(BaseModel):
    fully_covered: list[str] = []
    partially_covered: list[str] = []
    never_asked: list[str] = []
    coverage_percentage: float = 0.0


class PredictiveInsights(BaseModel):
    predicted_topics: list[dict] = []       # 🔥 High freq + recent absence
    ignored_high_weight: list[dict] = []    # ⚠️ High importance, low coverage
    low_roi_topics: list[dict] = []         # 📉 Low freq + low marks
    pareto_topics: list[dict] = []          # 🎯 Top 20% → 80% marks
    key_insights: list[str] = []


# ─── Study Plan Models ───

class StudySession(BaseModel):
    day: int
    date: str = ""
    topic: str
    subtopics: list[str] = []
    duration_hours: float
    session_type: str = "study"  # study / revision / practice / buffer
    priority: Priority = Priority.MEDIUM
    importance_score: float = 0.0


class StudyPlan(BaseModel):
    total_days: int
    total_hours: float
    sessions: list[StudySession] = []
    revision_days: list[int] = []
    buffer_days: list[int] = []


# ─── Practice Question Models ───

class PracticeQuestion(BaseModel):
    topic: str
    question_text: str
    question_type: QuestionType
    marks: float
    difficulty: Difficulty
    hint: str = ""


# ─── Dashboard Data Models ───

class FrequencyChartData(BaseModel):
    labels: list[str] = []
    values: list[int] = []


class HeatmapData(BaseModel):
    topics: list[str] = []
    years: list[int] = []
    matrix: list[list[int]] = []


class DifficultyPieData(BaseModel):
    easy: int = 0
    medium: int = 0
    hard: int = 0


class DashboardData(BaseModel):
    frequency_chart: FrequencyChartData = FrequencyChartData()
    heatmap: HeatmapData = HeatmapData()
    difficulty_pie: DifficultyPieData = DifficultyPieData()
    total_questions: int = 0
    total_topics: int = 0
    total_years: int = 0
    avg_importance: float = 0.0
    coverage_percentage: float = 0.0


# ─── Full Analysis Result ───

class AnalysisResult(BaseModel):
    questions: list[Question] = []
    topic_rankings: list[TopicAnalysis] = []
    syllabus_coverage: SyllabusCoverage = SyllabusCoverage()
    predictions: PredictiveInsights = PredictiveInsights()
    dashboard_data: DashboardData = DashboardData()
    study_plan: StudyPlan = StudyPlan(total_days=0, total_hours=0)
    practice_questions: list[PracticeQuestion] = []


# ─── API Request/Response ───

class UploadResponse(BaseModel):
    message: str
    files_processed: int
    total_text_length: int
    years_detected: list[int] = []


class AnalyzeRequest(BaseModel):
    exam_days: int = 30  # Days until exam
    hours_per_day: float = 6  # Study hours per day
    subject: str = "General"


class AnalyzeResponse(BaseModel):
    success: bool
    message: str
    result: Optional[AnalysisResult] = None
