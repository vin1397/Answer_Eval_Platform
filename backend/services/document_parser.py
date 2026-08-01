"""
Parses uploaded question-paper documents (PDF/DOCX) into structured
Question rows: number, text, and max marks (when the paper lists marks
in brackets, e.g. "Explain OSI model. [10]").
"""
from __future__ import annotations

import re

NUMBER_RE = re.compile(r"^\s*(\d{1,2})\s*[.)]\s*([a-dA-D])?\s*[.)]?\s*")
MARKS_RE = re.compile(r"\[(\d{1,3})\s*(?:marks?|m)?\]", re.IGNORECASE)


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
    persisted as `Question` rows: question_number, question_text, max_marks.
    """
    if suffix == ".pdf":
        text = _extract_text_pdf(file_path)
    elif suffix == ".docx":
        text = _extract_text_docx(file_path)
    else:
        return []

    questions: list[dict] = []
    current_number = None
    buffer: list[str] = []

    def flush():
        if current_number is not None:
            body = " ".join(buffer).strip()
            marks_match = MARKS_RE.search(body)
            max_marks = float(marks_match.group(1)) if marks_match else 10.0
            clean_text = MARKS_RE.sub("", body).strip()
            if clean_text:
                questions.append(
                    {
                        "question_number": current_number,
                        "question_text": clean_text,
                        "max_marks": max_marks,
                    }
                )

    for line in text.splitlines():
        match = NUMBER_RE.match(line)
        if match:
            flush()
            number, sub = match.group(1), match.group(2)
            current_number = f"{number}{sub.lower()}" if sub else number
            buffer = [line[match.end():]]
        else:
            if current_number is not None and line.strip():
                buffer.append(line.strip())

    flush()
    return questions
