"""
ExamIQ Practice Question Generator
STEP 8: Generate exam-style practice questions.
"""
import random
import logging
from app.models.schemas import TopicAnalysis, Question, PracticeQuestion, QuestionType, Difficulty

logger = logging.getLogger(__name__)

# Templates for different question types
TEMPLATES = {
    QuestionType.SHORT: [
        "Define {topic} and explain its significance.",
        "What is {topic}? List its key characteristics.",
        "State the main principles of {topic}.",
        "Differentiate between the key concepts in {topic}.",
        "Write a short note on {topic}.",
        "Enumerate the advantages of {topic}.",
        "What are the applications of {topic}?",
    ],
    QuestionType.LONG: [
        "Explain {topic} in detail with suitable examples.",
        "Discuss the principles and applications of {topic}.",
        "Describe the working mechanism of {topic} with a diagram.",
        "Compare and contrast different approaches in {topic}.",
        "Analyze the role of {topic} in modern applications.",
        "Critically evaluate the importance of {topic}.",
        "Elaborate on {topic} with real-world use cases.",
    ],
    QuestionType.MCQ: [
        "Which of the following best describes {topic}?\na) Option A\nb) Option B\nc) Option C\nd) Option D",
        "The primary purpose of {topic} is:\na) Option A\nb) Option B\nc) Option C\nd) Option D",
    ],
    QuestionType.NUMERICAL: [
        "Calculate the output for {topic} given the following parameters.",
        "Solve the following problem related to {topic}.",
        "Find the value using the {topic} formula.",
        "Compute the result for the given {topic} scenario.",
    ],
    QuestionType.CASE_BASED: [
        "Read the following case study about {topic} and answer the questions below.",
        "Based on the scenario involving {topic}, analyze and provide solutions.",
    ],
}


def generate_practice_questions(
    analyses: list[TopicAnalysis],
    questions: list[Question],
    num_per_topic: int = 3
) -> list[PracticeQuestion]:
    practice = []
    top_topics = [a for a in analyses if a.importance_score >= 25][:10]

    for analysis in top_topics:
        # Determine dominant question types for this topic
        type_dist = analysis.question_types
        dominant_types = sorted(type_dist.items(), key=lambda x: x[1], reverse=True)

        # Determine difficulty distribution
        diff_dist = analysis.difficulty_distribution

        for i in range(num_per_topic):
            # Pick question type
            if dominant_types:
                try:
                    qt = QuestionType(dominant_types[i % len(dominant_types)][0])
                except (ValueError, IndexError):
                    qt = QuestionType.SHORT
            else:
                qt = random.choice([QuestionType.SHORT, QuestionType.LONG])

            # Pick difficulty
            if diff_dist:
                diff_options = list(diff_dist.keys())
                try:
                    diff = Difficulty(random.choice(diff_options))
                except ValueError:
                    diff = Difficulty.MEDIUM
            else:
                diff = Difficulty.MEDIUM

            # Pick marks
            if qt == QuestionType.SHORT:
                marks = random.choice([2, 3, 5])
            elif qt == QuestionType.LONG:
                marks = random.choice([5, 8, 10])
            elif qt == QuestionType.MCQ:
                marks = random.choice([1, 2])
            elif qt == QuestionType.NUMERICAL:
                marks = random.choice([3, 5, 8])
            else:
                marks = 5

            # Generate question text
            templates = TEMPLATES.get(qt, TEMPLATES[QuestionType.SHORT])
            template = templates[i % len(templates)]
            text = template.format(topic=analysis.topic)

            practice.append(PracticeQuestion(
                topic=analysis.topic,
                question_text=text,
                question_type=qt,
                marks=marks,
                difficulty=diff,
                hint=f"Focus on key concepts of {analysis.topic}"
            ))

    return practice
