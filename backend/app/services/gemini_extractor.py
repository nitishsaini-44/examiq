"""
ExamIQ Gemini-Powered Question Extractor
Uses Google Gemini API for high-accuracy extraction of questions and topics
from raw OCR text of exam papers.
"""
import json
import uuid
import logging
from google import genai
from google.genai import types
from app.core.config import GEMINI_API_KEY
from app.models.schemas import Question, QuestionType, Difficulty

logger = logging.getLogger(__name__)

# Configure Gemini
client = genai.Client(api_key=GEMINI_API_KEY) if GEMINI_API_KEY else None

EXTRACTION_PROMPT = """You are an expert exam paper analyzer. Given the raw OCR text from an exam paper, extract ALL individual questions.

IMPORTANT RULES:
1. IGNORE all headers, instructions, metadata (course code, university name, date, time, marks scheme, "figures to the right indicate marks", etc.)
2. Extract ONLY actual exam questions that students need to answer
3. For each question, identify the ACTUAL ACADEMIC TOPIC (e.g., "Binary Search Trees", "Ohm's Law", "Polymorphism") — NOT the course code or paper metadata
4. Sub-questions (a, b, c) should be treated as separate questions if they cover different topics
5. If a question has multiple parts on the same topic, keep them together

Return a JSON array where each element has:
- "text": The full question text (clean, without question numbers)
- "topic": The specific academic/subject topic this question belongs to (e.g., "Linked Lists", "Thermodynamics", "Normalisation", "Flip-Flops"). Be specific, not generic.
- "subtopic": A more specific subtopic if identifiable (e.g., "Doubly Linked List", "Carnot Cycle")
- "marks": The marks allocated (number, 0 if unknown)
- "question_type": One of "MCQ", "Short Answer", "Long Answer", "Numerical", "Case-Based", "Unknown"
- "difficulty": One of "Easy", "Medium", "Hard"

RESPOND WITH ONLY the JSON array, no markdown formatting, no explanation.

RAW EXAM PAPER TEXT:
---
{text}
---
"""


def extract_questions_with_gemini(raw_text: str, year: int = 0, subject: str = "") -> list[Question]:
    """
    Use Gemini API to extract structured questions from raw OCR text.
    Returns a list of Question objects with accurate topic classification.
    """
    if not client:
        logger.warning("No Gemini API key configured, falling back to regex extractor")
        return []

    try:
        # Truncate very long texts to avoid token limits (keep ~15000 chars)
        text_to_send = raw_text[:15000] if len(raw_text) > 15000 else raw_text

        prompt = EXTRACTION_PROMPT.format(text=text_to_send)

        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=8000,
            )
        )

        response_text = response.text.strip()

        # Clean response — remove markdown code fences if present
        if response_text.startswith("```"):
            # Remove ```json and ``` wrapper
            lines = response_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = '\n'.join(lines)

        # Parse JSON
        extracted = json.loads(response_text)

        if not isinstance(extracted, list):
            logger.error("Gemini response is not a list")
            return []

        questions = []
        for item in extracted:
            # Map question type string to enum
            qtype_map = {
                "MCQ": QuestionType.MCQ,
                "Short Answer": QuestionType.SHORT,
                "Long Answer": QuestionType.LONG,
                "Numerical": QuestionType.NUMERICAL,
                "Case-Based": QuestionType.CASE_BASED,
                "Unknown": QuestionType.UNKNOWN,
            }
            diff_map = {
                "Easy": Difficulty.EASY,
                "Medium": Difficulty.MEDIUM,
                "Hard": Difficulty.HARD,
            }

            q = Question(
                id=str(uuid.uuid4())[:8],
                text=item.get("text", "").strip(),
                topic=item.get("topic", "").strip(),
                subtopic=item.get("subtopic", "").strip(),
                marks=float(item.get("marks", 0)),
                question_type=qtype_map.get(item.get("question_type", "Unknown"), QuestionType.UNKNOWN),
                difficulty=diff_map.get(item.get("difficulty", "Medium"), Difficulty.MEDIUM),
                year=year,
                subject=subject,
            )

            # Skip if question text is too short (likely garbage)
            if len(q.text) < 10:
                continue

            questions.append(q)

        logger.info(f"Gemini extracted {len(questions)} questions (year={year}, subject={subject})")
        return questions

    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse Gemini response as JSON: {e}")
        logger.debug(f"Raw response: {response_text[:500]}")
        return []
    except Exception as e:
        logger.error(f"Gemini extraction failed: {e}", exc_info=True)
        return []


def extract_syllabus_with_gemini(raw_text: str) -> list[dict]:
    """
    Use Gemini API to extract structured syllabus topics from raw OCR text.
    Returns a list of {topic, subtopics, unit} dicts.
    """
    if not client:
        return []

    try:
        prompt = f"""Extract the syllabus structure from this text. Return a JSON array where each element has:
- "topic": Main topic/unit name
- "subtopics": Array of subtopic strings
- "unit": Unit/module identifier (e.g., "Unit 1")

RESPOND WITH ONLY the JSON array, no markdown, no explanation.

TEXT:
---
{raw_text[:8000]}
---
"""
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt,
            config=types.GenerateContentConfig(
                temperature=0.1,
                max_output_tokens=4000,
            )
        )

        response_text = response.text.strip()
        if response_text.startswith("```"):
            lines = response_text.split('\n')
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].strip() == "```":
                lines = lines[:-1]
            response_text = '\n'.join(lines)

        return json.loads(response_text)

    except Exception as e:
        logger.error(f"Gemini syllabus extraction failed: {e}")
        return []
