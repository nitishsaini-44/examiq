"""
ExamIQ Frequency & Trend Analyzer
STEP 2 + STEP 3: Frequency analysis, trend detection, syllabus cross-reference.
"""
import numpy as np
import logging
from collections import defaultdict
from app.models.schemas import (
    Question, TopicAnalysis, SyllabusCoverage, SyllabusItem,
    FrequencyChartData, HeatmapData, DifficultyPieData, DashboardData
)

logger = logging.getLogger(__name__)


def analyze_topics(questions: list[Question]) -> list[TopicAnalysis]:
    """
    Compute comprehensive topic-level analytics.
    """
    # Group questions by topic
    topic_questions = defaultdict(list)
    for q in questions:
        topic = q.topic if q.topic else "Uncategorized"
        topic_questions[topic].append(q)

    analyses = []

    for topic, qs in topic_questions.items():
        # Frequency
        frequency = len(qs)

        # Marks
        total_marks = sum(q.marks for q in qs)
        avg_marks = total_marks / frequency if frequency > 0 else 0

        # Years
        years = sorted(set(q.year for q in qs if q.year > 0))

        # Difficulty distribution
        diff_dist = defaultdict(int)
        for q in qs:
            diff_dist[q.difficulty.value] += 1

        # Question types
        type_dist = defaultdict(int)
        for q in qs:
            type_dist[q.question_type.value] += 1

        # Trend analysis
        trend, trend_score = _compute_trend(qs, years)

        analysis = TopicAnalysis(
            topic=topic,
            frequency=frequency,
            total_marks=round(total_marks, 1),
            avg_marks=round(avg_marks, 1),
            years_appeared=years,
            trend=trend,
            trend_score=round(trend_score, 3),
            difficulty_distribution=dict(diff_dist),
            question_types=dict(type_dist),
        )
        analyses.append(analysis)

    return sorted(analyses, key=lambda a: a.frequency, reverse=True)


def _compute_trend(questions: list[Question], years: list[int]) -> tuple[str, float]:
    """
    Compute trend using linear regression on year-frequency data.
    Returns (trend_label, trend_score).
    """
    if len(years) < 2:
        return "stable", 0.0

    # Count questions per year
    year_counts = defaultdict(int)
    for q in questions:
        if q.year > 0:
            year_counts[q.year] += 1

    x = np.array(sorted(year_counts.keys()), dtype=float)
    y = np.array([year_counts[yr] for yr in sorted(year_counts.keys())], dtype=float)

    # Normalize x
    if len(x) > 1:
        x_norm = (x - x.mean()) / (x.std() if x.std() > 0 else 1)
    else:
        return "stable", 0.0

    # Linear regression slope
    try:
        slope = np.polyfit(x_norm, y, 1)[0]
    except Exception:
        slope = 0.0

    # Classify trend
    if slope > 0.3:
        return "increasing", slope
    elif slope < -0.3:
        return "decreasing", slope
    else:
        return "stable", slope


def compute_syllabus_coverage(
    topic_analyses: list[TopicAnalysis],
    syllabus_items: list[SyllabusItem]
) -> SyllabusCoverage:
    """
    Cross-reference analyzed topics with syllabus.
    STEP 3: Identify covered / partially covered / never asked topics.
    """
    if not syllabus_items:
        return SyllabusCoverage(
            fully_covered=[t.topic for t in topic_analyses if t.frequency >= 3],
            partially_covered=[t.topic for t in topic_analyses if 0 < t.frequency < 3],
            never_asked=[],
            coverage_percentage=100.0
        )

    analyzed_topics = {a.topic.lower(): a for a in topic_analyses}
    syllabus_topics = [item.topic for item in syllabus_items]

    fully_covered = []
    partially_covered = []
    never_asked = []

    for item in syllabus_items:
        topic_lower = item.topic.lower()

        # Check direct match
        matched = analyzed_topics.get(topic_lower)

        # Check fuzzy match
        if not matched:
            for key, analysis in analyzed_topics.items():
                if _fuzzy_match(topic_lower, key):
                    matched = analysis
                    break

        if matched:
            if matched.frequency >= 3 and len(matched.years_appeared) >= 2:
                fully_covered.append(item.topic)
            else:
                partially_covered.append(item.topic)
        else:
            never_asked.append(item.topic)

    total = len(syllabus_topics)
    covered = len(fully_covered) + len(partially_covered)
    coverage_pct = (covered / total * 100) if total > 0 else 0

    return SyllabusCoverage(
        fully_covered=fully_covered,
        partially_covered=partially_covered,
        never_asked=never_asked,
        coverage_percentage=round(coverage_pct, 1)
    )


def _fuzzy_match(s1: str, s2: str) -> bool:
    """Simple fuzzy matching: check if significant words overlap."""
    words1 = set(w for w in s1.split() if len(w) > 3)
    words2 = set(w for w in s2.split() if len(w) > 3)
    if not words1 or not words2:
        return False
    overlap = words1 & words2
    return len(overlap) / min(len(words1), len(words2)) >= 0.5


def build_dashboard_data(
    questions: list[Question],
    topic_analyses: list[TopicAnalysis],
    coverage: SyllabusCoverage
) -> DashboardData:
    """
    Build STEP 6: Dashboard-ready chart data.
    """
    # Frequency chart
    freq_chart = FrequencyChartData(
        labels=[a.topic for a in topic_analyses[:20]],
        values=[a.frequency for a in topic_analyses[:20]]
    )

    # Heatmap (Topic vs Year)
    all_years = sorted(set(q.year for q in questions if q.year > 0))
    top_topics = [a.topic for a in topic_analyses[:15]]

    matrix = []
    for topic in top_topics:
        row = []
        for year in all_years:
            count = sum(
                1 for q in questions
                if q.topic == topic and q.year == year
            )
            row.append(count)
        matrix.append(row)

    heatmap = HeatmapData(
        topics=top_topics,
        years=all_years,
        matrix=matrix
    )

    # Difficulty pie
    diff_pie = DifficultyPieData(
        easy=sum(1 for q in questions if q.difficulty.value == "Easy"),
        medium=sum(1 for q in questions if q.difficulty.value == "Medium"),
        hard=sum(1 for q in questions if q.difficulty.value == "Hard")
    )

    # Summary stats
    avg_importance = (
        sum(a.importance_score for a in topic_analyses) / len(topic_analyses)
        if topic_analyses else 0
    )

    return DashboardData(
        frequency_chart=freq_chart,
        heatmap=heatmap,
        difficulty_pie=diff_pie,
        total_questions=len(questions),
        total_topics=len(topic_analyses),
        total_years=len(all_years),
        avg_importance=round(avg_importance, 1),
        coverage_percentage=coverage.coverage_percentage
    )
