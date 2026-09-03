"""
Parses uploaded question-paper documents (PDF/DOCX) into structured
Question rows: number, text, max marks (when the paper lists marks in
brackets, e.g. "Explain OSI model. [10]"), and — generically, without
hardcoding any question range — MCQ options when a question body contains
option lines such as "A) ...", "(b) ...", "C. ...".

A question is only classified as MCQ if at least two option lines are
detected under it; otherwise it's treated as a short/descriptive answer.
This works for any paper layout (some MCQ, some descriptive, in any order)
rather than assuming a fixed split like "1-20 MCQ, 21-35 descriptive".
"""
from __future__ import annotations

import re

NUMBER_RE = re.compile(r"^\s*(\d{1,2})\s*(?:([a-dA-D])(?![a-zA-Z])\s*)?[.)]\s*")
MARKS_RE = re.compile(r"\[(\d{1,3})\s*(?:marks?|m)?\]", re.IGNORECASE)
# "A) text", "(b) text", "C. text", "d: text" — requires content after the marker
# so a stray "A." mid-sentence isn't mistaken for an option line.
OPTION_LINE_RE = re.compile(r"^\s*\(?([A-Da-d])\)?[.):]\s+(\S.*)$")

MIN_OPTIONS_FOR_MCQ = 2


def _extract_text_pdf(file_path: str) -> str:
    from pypdf import PdfReader  # lazy import

    reader = PdfReader(file_path)
    return "\n".join(page.extract_text() or "" for page in reader.pages)


def _extract_text_docx(file_path: str) -> str:
    import docx  # lazy import (python-docx)

    document = docx.Document(file_path)
    return "\n".join(p.text for p in document.paragraphs)


def extract_questions_from_file(file_path: str, suffix: str) -> list[dict]:
    """
    Returns a list of dicts shaped like QuestionCreate, ready to be
    persisted as `Question` rows: question_number, question_text, max_marks,
    question_type ("mcq" | "short_answer"), and options (list[str] | None).
    """
    if suffix == ".pdf":
        text = _extract_text_pdf(file_path)
    elif suffix == ".docx":
        text = _extract_text_docx(file_path)
    else:
        return []
    return parse_questions_from_text(text)


def parse_questions_from_text(text: str) -> list[dict]:
    """
    Pure text -> structured-questions parser, factored out of
    `extract_questions_from_file` so it can be unit-tested directly
    without needing real PDF/DOCX files on disk.
    """
    questions: list[dict] = []
    current_number = None
    body_lines: list[str] = []
    option_lines: list[str] = []

    def flush():
        if current_number is None:
            return
        body = " ".join(body_lines).strip()
        marks_match = MARKS_RE.search(body)
        max_marks = float(marks_match.group(1)) if marks_match else 10.0
        clean_text = MARKS_RE.sub("", body).strip()
        if not clean_text:
            return

        is_mcq = len(option_lines) >= MIN_OPTIONS_FOR_MCQ
        questions.append(
            {
                "question_number": current_number,
                "question_text": clean_text,
                "max_marks": max_marks,
                "question_type": "mcq" if is_mcq else "short_answer",
                "options": list(option_lines) if is_mcq else None,
            }
        )

    for line in text.splitlines():
        number_match = NUMBER_RE.match(line)
        option_match = OPTION_LINE_RE.match(line) if not number_match else None

        if number_match:
            flush()
            number, sub = number_match.group(1), number_match.group(2)
            current_number = f"{number}{sub.lower()}" if sub else number
            body_lines = [line[number_match.end():]]
            option_lines = []
        elif option_match and current_number is not None:
            option_lines.append(option_match.group(2).strip())
        else:
            if current_number is not None and line.strip():
                body_lines.append(line.strip())

    flush()
    return questions
