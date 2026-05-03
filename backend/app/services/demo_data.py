"""
ExamIQ Demo Data Generator
Creates sample analysis data for demonstration when no real papers are available.
"""
from app.models.schemas import (
    AnalysisResult, Question, QuestionType, Difficulty, Priority,
    TopicAnalysis, SyllabusCoverage, PredictiveInsights,
    DashboardData, FrequencyChartData, HeatmapData, DifficultyPieData,
    StudyPlan, StudySession, PracticeQuestion
)


def generate_demo_data() -> AnalysisResult:
    """Generate realistic demo analysis data."""

    topics_data = [
        ("Data Structures", 18, 85, "increasing", [2019,2020,2021,2022,2023]),
        ("Algorithms", 15, 72, "stable", [2019,2020,2021,2022,2023]),
        ("Database Management", 12, 58, "increasing", [2020,2021,2022,2023]),
        ("Operating Systems", 10, 50, "stable", [2019,2020,2022,2023]),
        ("Computer Networks", 9, 45, "decreasing", [2019,2020,2021]),
        ("Object Oriented Programming", 8, 40, "stable", [2020,2021,2022,2023]),
        ("Software Engineering", 7, 35, "increasing", [2021,2022,2023]),
        ("Compiler Design", 5, 28, "decreasing", [2019,2020]),
        ("Theory of Computation", 6, 30, "stable", [2019,2021,2023]),
        ("Discrete Mathematics", 4, 22, "decreasing", [2019,2020]),
        ("Machine Learning", 3, 18, "increasing", [2022,2023]),
        ("Cloud Computing", 2, 10, "increasing", [2023]),
    ]

    # Build topic analyses
    topic_rankings = []
    scores = [92.5, 85.3, 78.1, 68.4, 55.2, 52.8, 48.6, 32.1, 38.5, 22.3, 45.0, 28.7]
    priorities = [Priority.CRITICAL, Priority.CRITICAL, Priority.CRITICAL, Priority.HIGH,
                  Priority.HIGH, Priority.HIGH, Priority.MEDIUM, Priority.LOW,
                  Priority.MEDIUM, Priority.LOW, Priority.MEDIUM, Priority.MEDIUM]

    for i, (topic, freq, marks, trend, years) in enumerate(topics_data):
        topic_rankings.append(TopicAnalysis(
            topic=topic, frequency=freq, total_marks=marks, avg_marks=round(marks/freq, 1),
            years_appeared=years, trend=trend, trend_score=0.5 if trend == "increasing" else (-0.3 if trend == "decreasing" else 0.1),
            difficulty_distribution={"Easy": freq//3, "Medium": freq//2, "Hard": freq - freq//3 - freq//2},
            question_types={"Short Answer": freq//2, "Long Answer": freq//3, "MCQ": freq - freq//2 - freq//3},
            importance_score=scores[i], priority=priorities[i], rank=i+1
        ))

    # Syllabus coverage
    coverage = SyllabusCoverage(
        fully_covered=["Data Structures", "Algorithms", "Database Management", "Operating Systems", "OOP"],
        partially_covered=["Computer Networks", "Software Engineering", "Theory of Computation", "Machine Learning"],
        never_asked=["Cyber Security", "Blockchain", "IoT"],
        coverage_percentage=75.0
    )

    # Predictions
    predictions = PredictiveInsights(
        predicted_topics=[
            {"topic": "Machine Learning", "frequency": 3, "importance": 45.0, "reason": "Strong increasing trend, gaining importance"},
            {"topic": "Software Engineering", "frequency": 7, "importance": 48.6, "reason": "Increasing trend in recent 3 years"},
            {"topic": "Cloud Computing", "frequency": 2, "importance": 28.7, "reason": "New topic appearing with increasing weight"},
        ],
        ignored_high_weight=[
            {"topic": "Compiler Design", "importance": 32.1, "frequency": 5, "reason": "Historically important but absent recently"},
        ],
        low_roi_topics=[
            {"topic": "Discrete Mathematics", "frequency": 4, "marks": 22, "importance": 22.3, "reason": "Low frequency and low marks contribution"},
        ],
        pareto_topics=[
            {"topic": "Data Structures", "marks_contribution": 85, "cumulative_pct": 17.5, "importance": 92.5},
            {"topic": "Algorithms", "marks_contribution": 72, "cumulative_pct": 32.3, "importance": 85.3},
            {"topic": "Database Management", "marks_contribution": 58, "cumulative_pct": 44.2, "importance": 78.1},
            {"topic": "Operating Systems", "marks_contribution": 50, "cumulative_pct": 54.5, "importance": 68.4},
            {"topic": "Computer Networks", "marks_contribution": 45, "cumulative_pct": 63.8, "importance": 55.2},
            {"topic": "OOP", "marks_contribution": 40, "cumulative_pct": 72.0, "importance": 52.8},
            {"topic": "Software Engineering", "marks_contribution": 35, "cumulative_pct": 79.2, "importance": 48.6},
            {"topic": "Theory of Computation", "marks_contribution": 30, "cumulative_pct": 85.4, "importance": 38.5},
        ],
        key_insights=[
            "🔥 3 topics predicted for next exam based on frequency and absence patterns",
            "🎯 Focus on 8 topics (67% of syllabus) to cover ~80% of marks",
            "⚡ 3 critical-priority topics require immediate attention: Data Structures, Algorithms, DBMS",
            "📈 4 topics showing increasing trend: DBMS, Software Eng, ML, Cloud Computing",
            "📉 3 topics showing decreasing importance: Networks, Compiler Design, Discrete Math",
            "🧠 Concept repetition detected: Sorting algorithms appear in 5/5 years with similar patterns",
        ]
    )

    # Dashboard data
    years = [2019, 2020, 2021, 2022, 2023]
    dashboard = DashboardData(
        frequency_chart=FrequencyChartData(
            labels=[t[0] for t in topics_data],
            values=[t[1] for t in topics_data]
        ),
        heatmap=HeatmapData(
            topics=[t[0] for t in topics_data[:8]],
            years=years,
            matrix=[
                [4, 3, 4, 3, 4], [3, 3, 3, 3, 3], [0, 2, 3, 3, 4],
                [2, 2, 0, 3, 3], [3, 3, 3, 0, 0], [0, 2, 2, 2, 2],
                [0, 0, 2, 2, 3], [3, 2, 0, 0, 0],
            ]
        ),
        difficulty_pie=DifficultyPieData(easy=28, medium=42, hard=29),
        total_questions=99, total_topics=12, total_years=5,
        avg_importance=53.9, coverage_percentage=75.0
    )

    # Study plan (30-day)
    sessions = []
    plan_topics = [
        ("Data Structures", Priority.CRITICAL, 92.5, "study"),
        ("Algorithms", Priority.CRITICAL, 85.3, "study"),
        ("Database Management", Priority.CRITICAL, 78.1, "study"),
        ("Operating Systems", Priority.HIGH, 68.4, "study"),
        ("Computer Networks", Priority.HIGH, 55.2, "study"),
        ("OOP", Priority.HIGH, 52.8, "study"),
        ("Software Engineering", Priority.MEDIUM, 48.6, "study"),
        ("Machine Learning", Priority.MEDIUM, 45.0, "study"),
        ("Theory of Computation", Priority.MEDIUM, 38.5, "study"),
    ]

    day = 1
    for topic, pri, score, stype in plan_topics:
        hrs = max(2, round(score / 20))
        sessions.append(StudySession(day=day, date=f"2026-05-{3+day:02d}", topic=topic,
            duration_hours=min(hrs, 6), session_type="study", priority=pri, importance_score=score))
        day += 1

    # Revision
    for topic, pri, score, _ in plan_topics[:5]:
        sessions.append(StudySession(day=day, date=f"2026-05-{3+day:02d}", topic=topic,
            duration_hours=2, session_type="revision", priority=pri, importance_score=score))
        day += 1

    # Practice
    for topic, pri, score, _ in plan_topics[:3]:
        sessions.append(StudySession(day=day, date=f"2026-05-{3+day:02d}", topic=topic,
            duration_hours=3, session_type="practice", priority=pri, importance_score=score))
        day += 1

    sessions.append(StudySession(day=day, date=f"2026-05-{3+day:02d}", topic="Buffer / Catch-up",
        duration_hours=6, session_type="buffer", priority=Priority.LOW))

    study_plan = StudyPlan(total_days=30, total_hours=round(sum(s.duration_hours for s in sessions), 1),
        sessions=sessions, revision_days=list(range(10, 15)), buffer_days=[day])

    # Practice questions
    practice = []
    pq_data = [
        ("Data Structures", "Explain the implementation of AVL tree rotations with examples.", QuestionType.LONG, 10, Difficulty.HARD),
        ("Data Structures", "What is a hash table? Describe collision resolution techniques.", QuestionType.LONG, 8, Difficulty.MEDIUM),
        ("Data Structures", "Define stack. List applications of stack in computer science.", QuestionType.SHORT, 5, Difficulty.EASY),
        ("Algorithms", "Analyze the time complexity of merge sort using the Master theorem.", QuestionType.LONG, 10, Difficulty.HARD),
        ("Algorithms", "Write Dijkstra's shortest path algorithm and trace it on a graph.", QuestionType.LONG, 8, Difficulty.MEDIUM),
        ("Algorithms", "What is dynamic programming? Give two examples.", QuestionType.SHORT, 5, Difficulty.EASY),
        ("Database Management", "Explain normalization up to BCNF with examples.", QuestionType.LONG, 10, Difficulty.HARD),
        ("Database Management", "Write SQL queries for given relational schema.", QuestionType.NUMERICAL, 5, Difficulty.MEDIUM),
        ("Database Management", "What are ACID properties? Explain each briefly.", QuestionType.SHORT, 5, Difficulty.EASY),
        ("Operating Systems", "Explain process scheduling algorithms with Gantt charts.", QuestionType.LONG, 10, Difficulty.HARD),
        ("Operating Systems", "What is deadlock? State necessary conditions.", QuestionType.SHORT, 5, Difficulty.MEDIUM),
        ("Machine Learning", "Compare supervised and unsupervised learning with examples.", QuestionType.LONG, 8, Difficulty.MEDIUM),
    ]
    for topic, text, qt, marks, diff in pq_data:
        practice.append(PracticeQuestion(topic=topic, question_text=text, question_type=qt,
            marks=marks, difficulty=diff, hint=f"Focus on core concepts of {topic}"))

    return AnalysisResult(
        questions=[], topic_rankings=topic_rankings, syllabus_coverage=coverage,
        predictions=predictions, dashboard_data=dashboard, study_plan=study_plan,
        practice_questions=practice
    )
