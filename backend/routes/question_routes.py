"""
Question paper upload/parsing and model-answer authoring endpoints.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from api.schemas_exam import (
    QuestionPaperOut, QuestionCreate, QuestionOut, ModelAnswerCreate, ModelAnswerOut,
)
from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import UserRole
from models.exam import QuestionPaper, Question, ModelAnswer
from models.academic import Subject
from models.user import User
from services.storage_service import storage_service
from services.document_parser import extract_questions_from_file

router = APIRouter(tags=["Question Papers"])

ALLOWED_QP_TYPES = {".pdf", ".docx"}


@router.get("/question-papers", response_model=list[QuestionPaperOut])
def list_question_papers(
    subject_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    query = db.query(QuestionPaper)
    if subject_id:
        query = query.filter(QuestionPaper.subject_id == subject_id)
    return query.order_by(QuestionPaper.created_at.desc()).all()


@router.post("/question-papers/upload", response_model=QuestionPaperOut, status_code=status.HTTP_201_CREATED)
def upload_question_paper(
    title: str = Form(...),
    subject_id: int = Form(...),
    total_marks: int = Form(100),
    auto_extract: bool = Form(True),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_QP_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF and DOCX question papers are supported")

    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")

    stored_path = storage_service.save(file, subfolder="question-papers")
    paper = QuestionPaper(
        title=title, file_path=stored_path, file_type=suffix.lstrip("."),
        total_marks=total_marks, subject_id=subject_id,
    )
    db.add(paper)
    db.flush()

    if auto_extract:
        extracted = extract_questions_from_file(stored_path, suffix)
        for q in extracted:
            db.add(Question(question_paper_id=paper.id, **q))

    db.commit()
    db.refresh(paper)
    return paper


@router.post("/question-papers/{paper_id}/questions", response_model=QuestionOut, status_code=201)
def add_question(
    paper_id: int, payload: QuestionCreate, db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    paper = db.get(QuestionPaper, paper_id)
    if not paper:
        raise HTTPException(status_code=404, detail="Question paper not found")
    question = Question(question_paper_id=paper_id, **payload.model_dump())
    db.add(question)
    db.commit()
    db.refresh(question)
    return question


@router.delete("/questions/{question_id}", status_code=204)
def delete_question(
    question_id: int, db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    question = db.get(Question, question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    db.delete(question)
    db.commit()


# ------------------------------------------------------------- Model answers
@router.post("/model-answers", response_model=ModelAnswerOut, status_code=201)
def create_model_answer(
    payload: ModelAnswerCreate, db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    question = db.get(Question, payload.question_id)
    if not question:
        raise HTTPException(status_code=404, detail="Question not found")
    if question.model_answer is not None:
        raise HTTPException(status_code=400, detail="Model answer already exists for this question")

    model_answer = ModelAnswer(**payload.model_dump())
    db.add(model_answer)
    db.commit()
    db.refresh(model_answer)
    return model_answer


@router.put("/model-answers/{model_answer_id}", response_model=ModelAnswerOut)
def update_model_answer(
    model_answer_id: int, payload: ModelAnswerCreate, db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    model_answer = db.get(ModelAnswer, model_answer_id)
    if not model_answer:
        raise HTTPException(status_code=404, detail="Model answer not found")
    for field, value in payload.model_dump(exclude={"question_id"}).items():
        setattr(model_answer, field, value)
    db.commit()
    db.refresh(model_answer)
    return model_answer


@router.get("/model-answers/{model_answer_id}", response_model=ModelAnswerOut)
def get_model_answer(model_answer_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    model_answer = db.get(ModelAnswer, model_answer_id)
    if not model_answer:
        raise HTTPException(status_code=404, detail="Model answer not found")
    return model_answer
