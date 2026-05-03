"""
ExamIQ Predictive Intelligence
STEP 5: Generate predictions, alerts, and 80/20 strategy.
"""
import logging
from app.models.schemas import TopicAnalysis, PredictiveInsights

logger = logging.getLogger(__name__)


def generate_predictions(analyses: list[TopicAnalysis], all_years: list[int]) -> PredictiveInsights:
    if not analyses or not all_years:
        return PredictiveInsights()

    latest_year = max(all_years) if all_years else 0
    predicted = []
    ignored = []
    low_roi = []
    pareto = []
    insights = []

    # Predicted: high frequency + recent absence + trend increase
    for a in analyses:
        if a.frequency >= 2 and latest_year not in a.years_appeared and a.trend != "decreasing":
            predicted.append({"topic": a.topic, "frequency": a.frequency, "last_seen": max(a.years_appeared) if a.years_appeared else 0, "importance": a.importance_score, "reason": "High frequency but absent in recent exam"})

    # Also add increasing trend topics
    for a in analyses:
        if a.trend == "increasing" and a.importance_score >= 40:
            if not any(p["topic"] == a.topic for p in predicted):
                predicted.append({"topic": a.topic, "frequency": a.frequency, "trend": a.trend, "importance": a.importance_score, "reason": "Increasing trend in recent years"})

    # Ignored high-weight topics
    for a in analyses:
        if a.importance_score >= 50 and a.frequency <= 1:
            ignored.append({"topic": a.topic, "importance": a.importance_score, "frequency": a.frequency, "reason": "High marks weight but rarely asked"})

    # Low ROI topics
    for a in analyses:
        if a.frequency <= 1 and a.total_marks <= 5 and a.importance_score < 25:
            low_roi.append({"topic": a.topic, "frequency": a.frequency, "marks": a.total_marks, "importance": a.importance_score, "reason": "Low frequency and low marks contribution"})

    # 80/20 Pareto: top 20% topics contributing ~80% marks
    total_marks = sum(a.total_marks for a in analyses)
    sorted_by_marks = sorted(analyses, key=lambda a: a.total_marks, reverse=True)
    cumulative = 0
    threshold = total_marks * 0.8

    for a in sorted_by_marks:
        cumulative += a.total_marks
        pareto.append({"topic": a.topic, "marks_contribution": a.total_marks, "cumulative_pct": round(cumulative / total_marks * 100, 1) if total_marks > 0 else 0, "importance": a.importance_score})
        if cumulative >= threshold:
            break

    # Key insights
    if predicted:
        insights.append(f"🔥 {len(predicted)} topics predicted for next exam based on frequency and absence patterns")
    if pareto:
        pct = round(len(pareto) / len(analyses) * 100) if analyses else 0
        insights.append(f"🎯 Focus on {len(pareto)} topics ({pct}% of syllabus) to cover ~80% of marks")

    critical = [a for a in analyses if a.priority.value == "Critical"]
    if critical:
        insights.append(f"⚡ {len(critical)} critical-priority topics require immediate attention")

    increasing = [a for a in analyses if a.trend == "increasing"]
    if increasing:
        insights.append(f"📈 {len(increasing)} topics showing increasing trend in recent years")

    decreasing = [a for a in analyses if a.trend == "decreasing"]
    if decreasing:
        insights.append(f"📉 {len(decreasing)} topics showing decreasing importance")

    return PredictiveInsights(predicted_topics=predicted, ignored_high_weight=ignored, low_roi_topics=low_roi, pareto_topics=pareto, key_insights=insights)
