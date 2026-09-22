"""
Response schemas for student-facing result summaries.
"""
from datetime import datetime

from pydantic import BaseModel


class StudentResultOut(BaseModel):
    examination_id: int | None
    examination_name: str
    exam_date: datetime | None
    answer_script_id: int
    evaluation_id: int | None
    evaluation_status: str
    ai_marks: float | None
    max_marks: float | None
    final_marks: float | None
    confidence: float | None
    evaluated_at: datetime | None
