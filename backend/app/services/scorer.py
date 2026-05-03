"""
ExamIQ Importance Scorer
STEP 4: Smart importance scoring for each topic.
"""
import logging
from app.models.schemas import TopicAnalysis, Priority

logger = logging.getLogger(__name__)


def compute_importance_scores(analyses: list[TopicAnalysis]) -> list[TopicAnalysis]:
    if not analyses:
        return []

    frequencies = [a.frequency for a in analyses]
    marks_weights = [a.total_marks for a in analyses]
    trend_scores = [a.trend_score for a in analyses]

    diff_scores = []
    for a in analyses:
        dist = a.difficulty_distribution
        diff_scores.append(dist.get("Hard", 0) * 3 + dist.get("Medium", 0) * 2 + dist.get("Easy", 0))

    norm_freq = _normalize(frequencies)
    norm_marks = _normalize(marks_weights)
    norm_trend = _normalize(trend_scores)
    norm_diff = _normalize(diff_scores)

    for i, analysis in enumerate(analyses):
        score = norm_freq[i] * 0.4 + norm_marks[i] * 0.3 + norm_trend[i] * 0.2 + norm_diff[i] * 0.1
        analysis.importance_score = round(score, 1)

        if score >= 75:
            analysis.priority = Priority.CRITICAL
        elif score >= 50:
            analysis.priority = Priority.HIGH
        elif score >= 25:
            analysis.priority = Priority.MEDIUM
        else:
            analysis.priority = Priority.LOW

    analyses.sort(key=lambda a: a.importance_score, reverse=True)
    for i, analysis in enumerate(analyses):
        analysis.rank = i + 1

    return analyses


def _normalize(values: list[float]) -> list[float]:
    if not values:
        return []
    min_val, max_val = min(values), max(values)
    range_val = max_val - min_val
    if range_val == 0:
        return [50.0] * len(values)
    return [((v - min_val) / range_val) * 100 for v in values]
