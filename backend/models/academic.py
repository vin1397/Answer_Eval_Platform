"""
Core academic entities: Semester, Scheme, Subject, Student.
"""
from datetime import datetime

from sqlalchemy import String, Integer, ForeignKey, DateTime, UniqueConstraint, Index
from sqlalchemy.orm import Mapped, mapped_column, relationship

from database.session import Base


class Semester(Base):
    __tablename__ = "semesters"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(32), nullable=False)  # e.g. "Semester 5"
    number: Mapped[int] = mapped_column(Integer, nullable=False, unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subjects = relationship("Subject", back_populates="semester")
    students = relationship("Student", back_populates="semester")


class Scheme(Base):
    __tablename__ = "schemes"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(64), nullable=False)  # e.g. "2022 Scheme"
    year: Mapped[int] = mapped_column(Integer, nullable=False)
    is_active: Mapped[bool] = mapped_column(default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subjects = relationship("Subject", back_populates="scheme")


class Faculty(Base):
    __tablename__ = "faculty"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    designation: Mapped[str] = mapped_column(String(64), nullable=True)
    department: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str] = mapped_column(String(128), unique=True, nullable=False)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    subjects = relationship("Subject", back_populates="faculty_in_charge")


class Subject(Base):
    __tablename__ = "subjects"
    __table_args__ = (
        UniqueConstraint("code", "scheme_id", name="uq_subject_code_scheme"),
        Index("ix_subject_semester", "semester_id"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    code: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(160), nullable=False)
    credits: Mapped[int] = mapped_column(Integer, default=4)
    department: Mapped[str] = mapped_column(String(128), nullable=False)

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="CASCADE"))
    scheme_id: Mapped[int] = mapped_column(ForeignKey("schemes.id", ondelete="CASCADE"))
    faculty_id: Mapped[int | None] = mapped_column(ForeignKey("faculty.id", ondelete="SET NULL"), nullable=True)

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    semester = relationship("Semester", back_populates="subjects")
    scheme = relationship("Scheme", back_populates="subjects")
    faculty_in_charge = relationship("Faculty", back_populates="subjects")
    question_papers = relationship("QuestionPaper", back_populates="subject")
    examinations = relationship("Examination", back_populates="subject")


class Student(Base):
    __tablename__ = "students"
    __table_args__ = (
        UniqueConstraint("usn", name="uq_student_usn"),
        Index("ix_student_semester_section", "semester_id", "section"),
    )

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    usn: Mapped[str] = mapped_column(String(32), nullable=False)
    name: Mapped[str] = mapped_column(String(128), nullable=False)
    section: Mapped[str] = mapped_column(String(8), nullable=False)
    department: Mapped[str] = mapped_column(String(128), nullable=False)
    email: Mapped[str | None] = mapped_column(String(128), nullable=True)
    phone: Mapped[str | None] = mapped_column(String(20), nullable=True)

    semester_id: Mapped[int] = mapped_column(ForeignKey("semesters.id", ondelete="CASCADE"))

    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    semester = relationship("Semester", back_populates="students")
    answer_scripts = relationship("AnswerScript", back_populates="student")
