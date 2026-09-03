"""
Tests for services/document_parser.py — question/answer-key text parsing,
including generic MCQ option detection (spec items 2, 6, 19).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from services.document_parser import parse_questions_from_text  # noqa: E402


def test_short_answer_question_with_marks_bracket():
    text = "21. Define Supervised Learning. [2]"
    questions = parse_questions_from_text(text)
    assert len(questions) == 1
    q = questions[0]
    assert q["question_number"] == "21"
    assert q["question_type"] == "short_answer"
    assert q["options"] is None
    assert q["max_marks"] == 2.0
    assert "Define Supervised Learning" in q["question_text"]


def test_mcq_question_with_four_options():
    text = (
        "1. Which of these is a supervised learning algorithm?\n"
        "A) K-Means\n"
        "B) Linear Regression\n"
        "C) DBSCAN\n"
        "D) PCA\n"
    )
    questions = parse_questions_from_text(text)
    assert len(questions) == 1
    q = questions[0]
    assert q["question_type"] == "mcq"
    assert q["options"] == ["K-Means", "Linear Regression", "DBSCAN", "PCA"]


def test_single_option_line_does_not_trigger_mcq():
    """Fewer than MIN_OPTIONS_FOR_MCQ option-like lines must not misclassify
    a descriptive question (e.g. a line that happens to start with 'A.')."""
    text = "5. Explain the A. Turing test in your own words. [5]"
    questions = parse_questions_from_text(text)
    assert len(questions) == 1
    assert questions[0]["question_type"] == "short_answer"


def test_mixed_mcq_and_descriptive_no_hardcoded_ranges():
    """Confirms MCQ/descriptive classification is per-question, not based
    on any assumed numeric range."""
    text = (
        "1. Pick the odd one out.\n"
        "A) Cat\nB) Dog\nC) Car\nD) Cow\n"
        "2. Explain photosynthesis in detail. [10]\n"
        "3. Pick the prime number.\n"
        "A) 4\nB) 6\nC) 7\nD) 8\n"
    )
    questions = parse_questions_from_text(text)
    assert len(questions) == 3
    assert questions[0]["question_type"] == "mcq"
    assert questions[1]["question_type"] == "short_answer"
    assert questions[2]["question_type"] == "mcq"


def test_question_number_with_subpart():
    text = "12b) Describe the OSI model layers. [8]"
    questions = parse_questions_from_text(text)
    assert questions[0]["question_number"] == "12b"


def test_default_marks_when_no_bracket_given():
    text = "9. What is entropy?"
    questions = parse_questions_from_text(text)
    assert questions[0]["max_marks"] == 10.0
