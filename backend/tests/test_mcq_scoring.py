"""
Tests for MCQ normalization/scoring in ai/nlp/nlp_service.py (spec item 9).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from ai.nlp.nlp_service import normalize_mcq_option, score_mcq  # noqa: E402


def test_normalize_plain_letter():
    assert normalize_mcq_option("D") == "D"
    assert normalize_mcq_option("d") == "D"


def test_normalize_bracketed_and_punctuated_forms():
    assert normalize_mcq_option("(B)") == "B"
    assert normalize_mcq_option("B.") == "B"
    assert normalize_mcq_option("B)") == "B"
    assert normalize_mcq_option("Option C") == "C"


def test_normalize_returns_none_for_long_descriptive_text():
    """A long answer should never be misread as an MCQ letter, even if it
    happens to contain an A/B/C/D somewhere."""
    text = "A supervised learning model uses labeled training data to learn."
    assert normalize_mcq_option(text) is None


def test_normalize_returns_none_for_empty():
    assert normalize_mcq_option("") is None
    assert normalize_mcq_option(None) is None


def test_score_mcq_correct_answer_gets_full_marks():
    result = score_mcq("1", student_answer="D", correct_option="D", max_marks=1.0)
    assert result.ai_marks == 1.0
    assert result.extra["is_correct"] is True


def test_score_mcq_incorrect_answer_gets_zero():
    result = score_mcq("1", student_answer="D", correct_option="B", max_marks=1.0)
    assert result.ai_marks == 0.0
    assert result.extra["is_correct"] is False


def test_score_mcq_case_and_format_insensitive():
    result = score_mcq("1", student_answer="(b)", correct_option="B", max_marks=1.0)
    assert result.extra["is_correct"] is True


def test_score_mcq_undetected_option_is_not_silently_correct():
    """If OCR produced garbage that can't be normalized to a letter, the
    question must not be marked correct by accident."""
    result = score_mcq("1", student_answer="???", correct_option="B", max_marks=1.0)
    assert result.ai_marks == 0.0
    assert result.extra["option_detected"] is False
