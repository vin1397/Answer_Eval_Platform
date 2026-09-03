"""
Tests for Evaluation.final_marks — the property reports must use so that a
teacher's manual correction always overrides the raw AI marks (spec items
11, 12).
"""
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parent.parent))

from models.exam import Evaluation  # noqa: E402


def test_final_marks_uses_ai_marks_before_review():
    evaluation = Evaluation(answer_script_id=1, total_ai_marks=7.5, total_teacher_marks=None)
    assert evaluation.final_marks == 7.5


def test_final_marks_prefers_teacher_marks_after_review():
    evaluation = Evaluation(answer_script_id=1, total_ai_marks=7.5, total_teacher_marks=9.0)
    assert evaluation.final_marks == 9.0


def test_final_marks_respects_teacher_marking_down_to_zero():
    """A teacher lowering marks to 0 must not be treated as 'no override'
    just because 0 is falsy."""
    evaluation = Evaluation(answer_script_id=1, total_ai_marks=7.5, total_teacher_marks=0.0)
    assert evaluation.final_marks == 0.0


def test_final_marks_none_when_never_evaluated():
    evaluation = Evaluation(answer_script_id=1, total_ai_marks=None, total_teacher_marks=None)
    assert evaluation.final_marks is None
