"""
ExamIQ Study Planner
STEP 7: Generate personalized day-wise study plan.
"""
import logging
from datetime import datetime, timedelta
from app.models.schemas import TopicAnalysis, StudyPlan, StudySession, Priority

logger = logging.getLogger(__name__)


def generate_study_plan(analyses: list[TopicAnalysis], total_days: int = 30, hours_per_day: float = 6) -> StudyPlan:
    if not analyses:
        return StudyPlan(total_days=total_days, total_hours=0)

    sorted_topics = sorted(analyses, key=lambda a: a.importance_score, reverse=True)
    total_importance = sum(a.importance_score for a in sorted_topics)
    total_hours = total_days * hours_per_day

    # Reserve time: 70% study, 15% revision, 10% practice, 5% buffer
    study_hours = total_hours * 0.70
    revision_hours = total_hours * 0.15
    practice_hours = total_hours * 0.10
    buffer_hours = total_hours * 0.05

    sessions = []
    day = 1
    hours_today = 0
    start_date = datetime.now()

    # Phase 1: Study sessions (proportional to importance)
    for analysis in sorted_topics:
        if total_importance == 0:
            break
        topic_hours = max(1, (analysis.importance_score / total_importance) * study_hours)
        remaining = topic_hours

        while remaining > 0 and day <= total_days:
            available = hours_per_day - hours_today
            session_hours = min(remaining, available, 3)  # Max 3hr sessions

            if session_hours < 0.5:
                day += 1
                hours_today = 0
                continue

            session_date = (start_date + timedelta(days=day - 1)).strftime("%Y-%m-%d")
            sessions.append(StudySession(day=day, date=session_date, topic=analysis.topic, subtopics=[], duration_hours=round(session_hours, 1), session_type="study", priority=analysis.priority, importance_score=analysis.importance_score))

            hours_today += session_hours
            remaining -= session_hours

            if hours_today >= hours_per_day:
                day += 1
                hours_today = 0

    # Phase 2: Revision sessions (top topics)
    revision_topics = sorted_topics[:max(3, len(sorted_topics) // 3)]
    rev_per_topic = revision_hours / len(revision_topics) if revision_topics else 0
    revision_days = []

    for analysis in revision_topics:
        if day > total_days:
            break
        session_date = (start_date + timedelta(days=day - 1)).strftime("%Y-%m-%d")
        sessions.append(StudySession(day=day, date=session_date, topic=analysis.topic, duration_hours=round(min(rev_per_topic, hours_per_day), 1), session_type="revision", priority=analysis.priority, importance_score=analysis.importance_score))
        revision_days.append(day)
        hours_today += rev_per_topic
        if hours_today >= hours_per_day:
            day += 1
            hours_today = 0

    # Phase 3: Practice sessions
    practice_topics = sorted_topics[:5]
    prac_per_topic = practice_hours / len(practice_topics) if practice_topics else 0

    for analysis in practice_topics:
        if day > total_days:
            break
        session_date = (start_date + timedelta(days=day - 1)).strftime("%Y-%m-%d")
        sessions.append(StudySession(day=day, date=session_date, topic=analysis.topic, duration_hours=round(min(prac_per_topic, hours_per_day), 1), session_type="practice", priority=analysis.priority, importance_score=analysis.importance_score))
        hours_today += prac_per_topic
        if hours_today >= hours_per_day:
            day += 1
            hours_today = 0

    # Buffer days
    buffer_days_list = []
    buffer_day_count = max(1, int(buffer_hours / hours_per_day))
    for i in range(buffer_day_count):
        bd = min(day + i, total_days)
        buffer_days_list.append(bd)
        session_date = (start_date + timedelta(days=bd - 1)).strftime("%Y-%m-%d")
        sessions.append(StudySession(day=bd, date=session_date, topic="Buffer / Catch-up", duration_hours=hours_per_day, session_type="buffer", priority=Priority.LOW))

    actual_hours = sum(s.duration_hours for s in sessions)

    return StudyPlan(total_days=total_days, total_hours=round(actual_hours, 1), sessions=sessions, revision_days=revision_days, buffer_days=buffer_days_list)
