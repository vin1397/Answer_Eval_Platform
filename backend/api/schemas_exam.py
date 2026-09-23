"""
Pydantic schemas for the examination / evaluation pipeline.
"""
from datetime import datetime

from pydantic import BaseModel, Field, field_validator

from models.enums import DifficultyLevel, BloomTaxonomy, EvaluationStatus, ReviewDecision, QuestionType


class QuestionBase(BaseModel):
    question_number: str
    question_text: str
    max_marks: float = 10.0
    difficulty: DifficultyLevel = DifficultyLevel.MEDIUM
    bloom_level: BloomTaxonomy = BloomTaxonomy.UNDERSTAND
    question_type: QuestionType = QuestionType.SHORT_ANSWER
    options: list[str] | None = None  # required (>=2) when question_type == "mcq"

    @field_validator("options")
    @classmethod
    def _validate_options(cls, v, info):
        question_type = info.data.get("question_type")
        if question_type == QuestionType.MCQ and (not v or len(v) < 2):
            raise ValueError("MCQ questions require at least 2 options")
        return v


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
    answer_text: str | None = None  # descriptive reference answer (short-answer questions)
    correct_option: str | None = None  # e.g. "B" (MCQ questions)
    keywords: list[str] = Field(default_factory=list)
    expected_concepts: list[str] = Field(default_factory=list)
    rubric: list[dict] = Field(default_factory=list)

    @field_validator("correct_option")
    @classmethod
    def _uppercase_option(cls, v):
        return v.strip().upper() if v else v


class ModelAnswerOut(BaseModel):
    id: int
    question_id: int
    answer_text: str | None
    correct_option: str | None
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


class ExaminationPipelineStatus(ExaminationOut):
    """Examination enriched with live pipeline counters so the UI can show
    where each exam stands (Setup -> Examine -> Evaluate -> Review)."""
    question_paper_title: str | None = None
    scripts_uploaded: int = 0
    evaluations_completed: int = 0
    evaluations_approved: int = 0
    awaiting_evaluation: int = 0
    awaiting_review: int = 0
    # Contextual guidance for the next action on this exam, e.g.
    # "Link a question paper" or "Evaluate 3 scripts".
    next_action: str | None = None
    next_action_route: str | None = None


class AnswerScriptOut(BaseModel):
    id: int
    file_path: str
    file_type: str
    page_count: int
    upload_status: str
    examination_id: int
    student_id: int
    created_at: datetime
    # Enrichment added by the list endpoint (never exposes file_path itself):
    student_name: str | None = None
    student_usn: str | None = None
    examination_name: str | None = None
    evaluation_status: str = "not_evaluated"
    final_marks: float | None = None
    total_max_marks: float | None = None
    evaluation_id: int | None = None
    model_config = {"from_attributes": True}


class ExtractedAnswer(BaseModel):
    question_number: str
    answer_text: str
    semantic_score: float
    keyword_score: float
    ai_marks: float
    max_marks: float
    uncertain: bool = False
    question_type: str = "short_answer"


class EvaluationOut(BaseModel):
    id: int
    answer_script_id: int
    status: EvaluationStatus
    status_detail: str | None = None
    ocr_raw_text: str | None = None
    extracted_answers: list[dict] | None = None
    has_uncertain_segments: bool = False
    total_ai_marks: float | None = None
    total_max_marks: float | None = None
    total_teacher_marks: float | None = None
    final_marks: float | None = None
    confidence_score: float | None = None
    ai_model_version: str | None = None
    created_at: datetime
    # question_number -> {question_text, reference_answer, correct_option} —
    # lets the UI show what was asked and the faculty reference side-by-side.
    question_context: dict[str, dict] | None = None
    # file type of the underlying answer script (pdf | jpg | png) for the viewer.
    answer_script_file_type: str | None = None
    student_name: str | None = None
    student_usn: str | None = None
    examination_name: str | None = None
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
