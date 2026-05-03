"""
ExamIQ Question Extractor
Parses raw OCR text into structured Question objects.
STEP 1: Question Understanding
"""
import re
import uuid
import logging
from app.models.schemas import (
    Question, QuestionType, Difficulty, SyllabusItem
)

logger = logging.getLogger(__name__)

# ─── Boilerplate / Header Patterns to Filter Out ───
BOILERPLATE_PATTERNS = [
    # Course code, subject code, paper code
    r'(?i)\b(?:course|subject|paper)\s*(?:code|id|no\.?)\s*[:\-]?\s*[A-Z]{2,5}\s*\d{2,5}',
    # Credit / semester lines
    r'(?i)\b(?:course\s*credit|credit\s*hours?|semester|sem)\s*[:\-]?\s*\d',
    # University / college / exam names
    r'(?i)\b(?:university|college|institute|examination|exam\b|affiliated)',
    # Instruction lines
    r'(?i)\b(?:figures?\s+(?:to\s+the\s+)?right\s+indicate)',
    r'(?i)\b(?:answer\s+(?:any|all)\s+\w+\s+questions?\b)',
    r'(?i)\b(?:attempt\s+(?:any|all)\b)',
    r'(?i)\b(?:time\s*[:\-]?\s*\d+\s*(?:hours?|hrs?|minutes?|mins?))',
    r'(?i)\b(?:max(?:imum)?\s*marks?\s*[:\-]?\s*\d+)',
    r'(?i)\b(?:total\s*marks?\s*[:\-]?\s*\d+)',
    r'(?i)\b(?:duration\s*[:\-]?\s*\d+)',
    r'(?i)\b(?:instructions?\s*(?:to\s+(?:the\s+)?candidates?|for\s+(?:the\s+)?students?))',
    r'(?i)\b(?:note\s*:\s*)',
    r'(?i)\b(?:reg(?:istration)?\.?\s*no\.?\s*[:\-])',
    r'(?i)\b(?:roll\s*no\.?\s*[:\-])',
    r'(?i)\b(?:date\s*[:\-]\s*\d)',
    r'(?i)\b(?:module|scheme|syllabus)\s*(?:code|no\.?|id)\b',
    # "Write anything" / generic instructions
    r'(?i)\b(?:write\s+(?:anything|neatly|clearly|legibly)\b)',
    r'(?i)\b(?:use\s+(?:only|black|blue)\s+(?:pen|ink)\b)',
    r'(?i)\b(?:do\s+not\s+write\b)',
    r'(?i)\b(?:assume\s+suitable\s+data\b)',
    r'(?i)\b(?:draw\s+neat\s+(?:diagrams?|sketches?|figures?)\b)',
]


def _is_boilerplate(text: str) -> bool:
    """Check if a text block is exam paper boilerplate (header/instruction) rather than a question."""
    text_stripped = text.strip()

    # Very short blocks are likely headers
    if len(text_stripped) < 20:
        return True

    # Count how many boilerplate patterns match
    matches = sum(1 for p in BOILERPLATE_PATTERNS if re.search(p, text_stripped))

    # If most of the block is boilerplate, skip it
    lines = [l.strip() for l in text_stripped.split('\n') if l.strip()]
    if len(lines) <= 3 and matches >= 1:
        return True
    if matches >= 2:
        return True

    return False


# ─── Question Boundary Patterns ───
QUESTION_PATTERNS = [
    # "Q1.", "Q.1", "Q 1.", "Question 1"
    r'(?:^|\n)\s*(?:Q(?:uestion)?[\s.]*(\d+)[\s.:)]+)',
    # "1.", "1)", "1:" at line start
    r'(?:^|\n)\s*(\d{1,3})\s*[.):\]]\s+',
    # "(a)", "a)", "a."
    r'(?:^|\n)\s*\(?([a-zA-Z])\)\s+',
    # "Section A", "PART I"
    r'(?:^|\n)\s*(?:Section|SECTION|Part|PART)\s+([A-Z]|[IVX]+)',
]

# ─── Marks Extraction Patterns ───
MARKS_PATTERNS = [
    r'\[(\d+)\s*(?:marks?|M)\]',
    r'\((\d+)\s*(?:marks?|M)\)',
    r'(\d+)\s*(?:marks?|Marks)',
    r'\[(\d+)\]',
    r'(?:marks?|Marks)\s*[:=]\s*(\d+)',
]

# ─── Question Type Keywords ───
TYPE_INDICATORS = {
    QuestionType.MCQ: [
        r'\b(?:choose|select|correct\s+(?:option|answer))\b',
        r'\([abcd]\)',
        r'\b(?:option|options)\b',
        r'\b[ABCD]\)',
    ],
    QuestionType.NUMERICAL: [
        r'\bcalculate\b', r'\bcompute\b', r'\bfind\s+the\s+value\b',
        r'\bsolve\b', r'\bevaluate\b', r'\bdetermine\b',
        r'\bhow\s+(?:many|much)\b',
    ],
    QuestionType.CASE_BASED: [
        r'\bcase\s+study\b', r'\bscenario\b', r'\bread\s+the\s+(?:passage|following)\b',
        r'\bcomprehension\b',
    ],
    QuestionType.LONG: [
        r'\bexplain\s+in\s+detail\b', r'\bdiscuss\b', r'\belaborate\b',
        r'\bdescribe\b', r'\banalyze\b', r'\bcritically\b',
        r'\bcompare\s+and\s+contrast\b', r'\bwrite\s+an?\s+essay\b',
    ],
    QuestionType.SHORT: [
        r'\bdefine\b', r'\blist\b', r'\bstate\b', r'\bname\b',
        r'\bwhat\s+is\b', r'\bwhat\s+are\b', r'\bmention\b',
        r'\bwrite\s+short\s+note\b', r'\benumerate\b',
    ],
}


def _clean_raw_text(raw_text: str) -> str:
    """Remove boilerplate lines (headers, instructions, metadata) from raw OCR text."""
    cleaned_lines = []
    for line in raw_text.split('\n'):
        stripped = line.strip()
        if not stripped:
            cleaned_lines.append('')
            continue
        # Check each line against boilerplate patterns
        is_junk = False
        for p in BOILERPLATE_PATTERNS:
            if re.search(p, stripped):
                is_junk = True
                break
        if not is_junk:
            cleaned_lines.append(line)
    return '\n'.join(cleaned_lines)


def extract_questions(raw_text: str, year: int = 0, subject: str = "") -> list[Question]:
    """
    Parse raw OCR text into structured Question objects.
    Uses regex-based question boundary detection and classification.
    """
    questions = []

    # Pre-clean: strip boilerplate lines from raw text
    cleaned_text = _clean_raw_text(raw_text)

    # Split into potential question blocks
    blocks = _split_into_blocks(cleaned_text)

    for i, block in enumerate(blocks):
        if len(block.strip()) < 10:
            continue
        # Skip exam paper boilerplate (headers, instructions, metadata)
        if _is_boilerplate(block):
            logger.debug(f"Skipping boilerplate block: {block[:60]}...")
            continue

        q = Question(
            id=str(uuid.uuid4())[:8],
            text=block.strip(),
            year=year,
            subject=subject,
            marks=_extract_marks(block),
            question_type=_classify_type(block),
            difficulty=_estimate_difficulty(block),
        )
        questions.append(q)

    logger.info(f"Extracted {len(questions)} questions from text (year={year})")
    return questions


def _split_into_blocks(text: str) -> list[str]:
    """Split raw text into individual question blocks."""
    # Try structured splitting first
    pattern = r'(?:^|\n)\s*(?:Q(?:uestion)?[\s.]*\d+[\s.:)]+|\d{1,2}\s*[.)]\s+)'
    splits = re.split(pattern, text, flags=re.IGNORECASE | re.MULTILINE)

    # Filter out empty blocks
    blocks = [s.strip() for s in splits if s and len(s.strip()) > 15]

    # If splitting produced too few results, try line-based approach
    if len(blocks) < 3:
        lines = text.split('\n')
        blocks = []
        current_block = []

        for line in lines:
            line = line.strip()
            if not line:
                if current_block:
                    blocks.append('\n'.join(current_block))
                    current_block = []
            else:
                current_block.append(line)

        if current_block:
            blocks.append('\n'.join(current_block))

    return blocks


def _extract_marks(text: str) -> float:
    """Extract marks value from question text."""
    for pattern in MARKS_PATTERNS:
        match = re.search(pattern, text, re.IGNORECASE)
        if match:
            return float(match.group(1))

    # Estimate marks based on question length and type
    word_count = len(text.split())
    if word_count < 20:
        return 2.0
    elif word_count < 50:
        return 5.0
    else:
        return 10.0


def _classify_type(text: str) -> QuestionType:
    """Classify question type based on keyword analysis."""
    text_lower = text.lower()

    # Check each type's indicators
    type_scores = {}
    for qtype, patterns in TYPE_INDICATORS.items():
        score = sum(1 for p in patterns if re.search(p, text_lower))
        if score > 0:
            type_scores[qtype] = score

    if type_scores:
        return max(type_scores, key=type_scores.get)

    # Default based on marks
    marks = _extract_marks(text)
    if marks <= 2:
        return QuestionType.SHORT
    elif marks <= 5:
        return QuestionType.SHORT
    else:
        return QuestionType.LONG


def _estimate_difficulty(text: str) -> Difficulty:
    """Estimate difficulty based on question complexity indicators."""
    text_lower = text.lower()
    word_count = len(text.split())

    hard_indicators = [
        'prove', 'derive', 'analyze critically', 'compare and contrast',
        'design', 'implement', 'optimize', 'complex', 'advanced',
        'evaluate', 'justify', 'synthesize',
    ]
    easy_indicators = [
        'define', 'list', 'state', 'name', 'what is', 'what are',
        'mention', 'enumerate', 'true or false', 'fill in',
    ]

    hard_score = sum(1 for ind in hard_indicators if ind in text_lower)
    easy_score = sum(1 for ind in easy_indicators if ind in text_lower)

    marks = _extract_marks(text)

    if hard_score > easy_score or marks >= 10 or word_count > 80:
        return Difficulty.HARD
    elif easy_score > hard_score or marks <= 2 or word_count < 25:
        return Difficulty.EASY
    else:
        return Difficulty.MEDIUM


def map_to_syllabus(questions: list[Question], syllabus_items: list[SyllabusItem]) -> list[Question]:
    """
    Map extracted questions to syllabus topics using keyword matching.
    For advanced mapping, use the embeddings service.
    """
    if not syllabus_items:
        return questions

    for q in questions:
        best_match = None
        best_score = 0

        q_text = q.text.lower()

        for item in syllabus_items:
            # Check topic name match
            topic_words = item.topic.lower().split()
            score = sum(1 for w in topic_words if w in q_text and len(w) > 3)

            # Check subtopic matches
            for sub in item.subtopics:
                sub_words = sub.lower().split()
                sub_score = sum(1 for w in sub_words if w in q_text and len(w) > 3)
                if sub_score > 0:
                    score += sub_score
                    if sub_score > best_score:
                        q.subtopic = sub

            if score > best_score:
                best_score = score
                best_match = item

        if best_match and best_score > 0:
            q.topic = best_match.topic
            if not q.subtopic and best_match.subtopics:
                q.subtopic = best_match.subtopics[0]

    return questions


def parse_syllabus_text(raw_text: str) -> list[SyllabusItem]:
    """
    Parse raw syllabus text into structured SyllabusItem objects.
    Expects format like:
    Unit 1: Topic Name
    - Subtopic 1
    - Subtopic 2
    """
    items = []
    current_topic = None
    current_subtopics = []
    current_unit = None

    lines = raw_text.strip().split('\n')

    for line in lines:
        line = line.strip()
        if not line:
            continue

        # Check for unit/module header
        unit_match = re.match(
            r'(?:Unit|Module|Chapter|UNIT|MODULE|CHAPTER)\s*[\d.:]+\s*[:\-–]?\s*(.*)',
            line, re.IGNORECASE
        )

        if unit_match:
            # Save previous topic
            if current_topic:
                items.append(SyllabusItem(
                    topic=current_topic,
                    subtopics=current_subtopics,
                    unit=current_unit
                ))

            current_topic = unit_match.group(1).strip()
            current_unit = line.split(':')[0].strip() if ':' in line else line.split('-')[0].strip()
            current_subtopics = []

        elif line.startswith(('-', '•', '*', '–')) or re.match(r'^\d+\.\d+', line):
            # Subtopic
            subtopic = re.sub(r'^[-•*–\d.]+\s*', '', line).strip()
            if subtopic and current_topic:
                current_subtopics.append(subtopic)

        elif not current_topic:
            # First line might be a topic without unit prefix
            current_topic = line
            current_subtopics = []

    # Save last topic
    if current_topic:
        items.append(SyllabusItem(
            topic=current_topic,
            subtopics=current_subtopics,
            unit=current_unit
        ))

    logger.info(f"Parsed {len(items)} syllabus topics")
    return items
