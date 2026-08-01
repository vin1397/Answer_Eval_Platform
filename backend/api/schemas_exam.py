"""
Pydantic schemas for the examination / evaluation pipeline.
"""
from datetime import datetime

from pydantic import BaseModel, Field

from models.enums import DifficultyLevel, BloomTaxonomy, EvaluationStatus, ReviewDecision


class QuestionBase(BaseModel):
    question_number: str
    question_text: str
    max_marks: float = 10.0
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    bloom_level: BloomTaxonomy = BloomTaxonomy.UNDERSTAND


class QuestionCreate(QuestionBase):
    pass


class QuestionOut(QuestionBase):
    id: int
    question_paper_id: int
    model_config = {"from_attributes": True}


class QuestionPaperOut(BaseModel):
    id: int
    title: str
    file_path: str
    file_type: str
    total_marks: int
    subject_id: int
    created_at: datetime
    questions: list[QuestionOut] = []
    model_config = {"from_attributes": True}


class ModelAnswerCreate(BaseModel):
    question_id: int
    answer_text: str
    keywords: list[str] = Field(default_factory=list)
    expected_concepts: list[str] = Field(default_factory=list)
    rubric: list[dict] = Field(default_factory=list)


class ModelAnswerOut(BaseModel):
    id: int
    question_id: int
    answer_text: str
    keywords: list[str]
    expected_concepts: list[str]
    rubric: list[dict]
    model_config = {"from_attributes": True}


class ExaminationCreate(BaseModel):
    name: str
    exam_date: datetime
    subject_id: int
    question_paper_id: int | None = None


class ExaminationOut(ExaminationCreate):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class AnswerScriptOut(BaseModel):
    id: int
    file_path: str
    file_type: str
    page_count: int
    upload_status: str
    examination_id: int
    student_id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class ExtractedAnswer(BaseModel):
    question_number: str
    answer_text: str
    semantic_score: float
    keyword_score: float
    ai_marks: float
    max_marks: float


class EvaluationOut(BaseModel):
    id: int
    answer_script_id: int
    status: EvaluationStatus
    ocr_raw_text: str | None = None
    extracted_answers: list[dict] | None = None
    total_ai_marks: float | None = None
    total_max_marks: float | None = None
    total_teacher_marks: float | None = None
    confidence_score: float | None = None
    ai_model_version: str | None = None
    created_at: datetime
    model_config = {"from_attributes": True}


class TeacherReviewCreate(BaseModel):
    decision: ReviewDecision
    adjusted_marks: float | None = None
    reason: str | None = None
    comments: str | None = None


class TeacherReviewOut(BaseModel):
    id: int
    evaluation_id: int
    reviewer_id: int | None
    decision: ReviewDecision | None
    adjusted_marks: float | None
    reason: str | None
    comments: str | None
    created_at: datetime
    model_config = {"from_attributes": True}
