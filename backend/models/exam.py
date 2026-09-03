"""
Examination pipeline entities: QuestionPaper -> Question -> ModelAnswer,
Examination -> AnswerScript -> Evaluation -> TeacherReview.
"""
from datetime import datetime

from sqlalchemy import (
    String, Integer, Float, Text, ForeignKey, DateTime, Enum as SAEnum, JSON, Index
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base
from models.enums import DifficultyLevel, BloomTaxonomy, EvaluationStatus, ReviewDecision, QuestionType


class QuestionPaper(Base):
    __tablename__ = "question_papers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | docx
    total_marks: Mapped[int] = mapped_column(Integer, default=100)

    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="question_papers")
    questions = relationship("Question", back_populates="question_paper", cascade="all, delete-orphan")


class Question(Base):
    __tablename__ = "questions"
    __table_args__ = (Index("ix_question_paper", "question_paper_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    question_number: Mapped[str] = mapped_column(String(16), nullable=False)  # "1a", "2b"...
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    max_marks: Mapped[float] = mapped_column(Float, default=10.0)
    difficulty: Mapped[DifficultyLevel] = mapped_column(
        SAEnum(DifficultyLevel), default=DifficultyLevel.MEDIUM
    )
    bloom_level: Mapped[BloomTaxonomy] = mapped_column(
        SAEnum(BloomTaxonomy), default=BloomTaxonomy.UNDERSTAND
    )
    question_type: Mapped[QuestionType] = mapped_column(
        SAEnum(QuestionType), default=QuestionType.SHORT_ANSWER, nullable=False
    )
    options: Mapped[list | None] = mapped_column(JSON, nullable=True)  # MCQ choices, e.g. ["Cats", "Dogs", ...]

    question_paper_id: Mapped[int] = mapped_column(ForeignKey("question_papers.id", ondelete="CASCADE"))

    question_paper = relationship("QuestionPaper", back_populates="questions")
    model_answer = relationship(
        "ModelAnswer", back_populates="question", uselist=False, cascade="all, delete-orphan"
    )


class ModelAnswer(Base):
    __tablename__ = "model_answers"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE"), unique=True
    )
    answer_text: Mapped[str | None] = mapped_column(Text, nullable=True)  # descriptive reference answer
    correct_option: Mapped[str | None] = mapped_column(String(8), nullable=True)  # MCQ correct choice, e.g. "B"
    keywords: Mapped[list] = mapped_column(JSON, default=list)  # ["mitosis", "cell division", ...]
    expected_concepts: Mapped[list] = mapped_column(JSON, default=list)
    rubric: Mapped[list] = mapped_column(JSON, default=list)  # [{"criterion": "...", "marks": 2}, ...]
    source_file_path: Mapped[str | None] = mapped_column(String(500), nullable=True)
    embedding: Mapped[list | None] = mapped_column(JSON, nullable=True)  # cached sentence embedding

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    question = relationship("Question", back_populates="model_answer")


class Examination(Base):
    __tablename__ = "examinations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(160), nullable=False)  # "CIE-1", "SEE" ...
    exam_date: Mapped[datetime] = mapped_column(DateTime, nullable=False)
    subject_id: Mapped[int] = mapped_column(ForeignKey("subjects.id", ondelete="CASCADE"))
    question_paper_id: Mapped[int | None] = mapped_column(
        ForeignKey("question_papers.id", ondelete="SET NULL"), nullable=True
    )

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subject = relationship("Subject", back_populates="examinations")
    answer_scripts = relationship("AnswerScript", back_populates="examination")


class AnswerScript(Base):
    __tablename__ = "answer_scripts"
    __table_args__ = (Index("ix_script_exam_student", "examination_id", "student_id"),)

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    file_path: Mapped[str] = mapped_column(String(500), nullable=False)
    file_type: Mapped[str] = mapped_column(String(10), nullable=False)  # pdf | jpg | png
    page_count: Mapped[int] = mapped_column(Integer, default=1)
    upload_status: Mapped[str] = mapped_column(String(32), default="uploaded")

    examination_id: Mapped[int] = mapped_column(ForeignKey("examinations.id", ondelete="CASCADE"))
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    examination = relationship("Examination", back_populates="answer_scripts")
    student = relationship("Student", back_populates="answer_scripts")
    evaluation = relationship(
        "Evaluation", back_populates="answer_script", uselist=False, cascade="all, delete-orphan"
    )


class Evaluation(Base):
    __tablename__ = "evaluations"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    answer_script_id: Mapped[int] = mapped_column(
        ForeignKey("answer_scripts.id", ondelete="CASCADE"), unique=True
    )

    status: Mapped[EvaluationStatus] = mapped_column(
        SAEnum(EvaluationStatus), default=EvaluationStatus.PENDING
    )
    status_detail: Mapped[str | None] = mapped_column(String(120), nullable=True)
    # Human-readable current step, e.g. "Running handwriting OCR" — updated live
    # during the pipeline so the UI can show granular progress beyond the enum.

    ocr_raw_text: Mapped[str | None] = mapped_column(Text, nullable=True)
    extracted_answers: Mapped[list | None] = mapped_column(JSON, nullable=True)
    # [{"question_number": "1a", "answer_text": "...", "semantic_score": 0.82,
    #   "keyword_score": 0.7, "ai_marks": 7.5, "max_marks": 10, "uncertain": false}]

    has_uncertain_segments: Mapped[bool] = mapped_column(default=False)
    # True if any answer segment's question-number association could not be
    # confidently determined — forces teacher review rather than guessing.

    total_ai_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_max_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    total_teacher_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    confidence_score: Mapped[float | None] = mapped_column(Float, nullable=True)

    ai_model_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    answer_script = relationship("AnswerScript", back_populates="evaluation")
    review = relationship(
        "TeacherReview", back_populates="evaluation", uselist=False, cascade="all, delete-orphan"
    )

    @property
    def final_marks(self) -> float | None:
        """Teacher-approved marks take precedence; falls back to the AI marks
        until a teacher has reviewed. Reports must always use this, never
        `total_ai_marks` directly, once a review exists."""
        return self.total_teacher_marks if self.total_teacher_marks is not None else self.total_ai_marks


class TeacherReview(Base):
    __tablename__ = "teacher_reviews"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    evaluation_id: Mapped[int] = mapped_column(
        ForeignKey("evaluations.id", ondelete="CASCADE"), unique=True
    )
    reviewer_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True)

    decision: Mapped[ReviewDecision | None] = mapped_column(SAEnum(ReviewDecision), nullable=True)
    adjusted_marks: Mapped[float | None] = mapped_column(Float, nullable=True)
    reason: Mapped[str | None] = mapped_column(Text, nullable=True)
    comments: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    evaluation = relationship("Evaluation", back_populates="review")
    reviewer = relationship("User", back_populates="reviews")
