"""
Examinations, answer script uploads, and the AI evaluation queue.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session

from api.schemas_exam import (
    ExaminationCreate, ExaminationOut, AnswerScriptOut, EvaluationOut,
    TeacherReviewCreate, TeacherReviewOut,
)
from auth.dependencies import get_current_user, require_roles
from database.session import get_db
from models.enums import UserRole, EvaluationStatus, ReviewDecision
from models.exam import Examination, AnswerScript, Evaluation, TeacherReview
from models.academic import Student
from models.user import User
from services.storage_service import storage_service
from services.evaluation_pipeline import run_pipeline

router = APIRouter(tags=["Evaluation"])

ALLOWED_SCRIPT_TYPES = {".pdf", ".jpg", ".jpeg", ".png"}


# ------------------------------------------------------------- Examinations
@router.get("/examinations", response_model=list[ExaminationOut])
def list_examinations(
    subject_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    query = db.query(Examination)
    if subject_id:
        query = query.filter(Examination.subject_id == subject_id)
    return query.order_by(Examination.exam_date.desc()).all()


@router.post("/examinations", response_model=ExaminationOut, status_code=201)
def create_examination(
    payload: ExaminationCreate, db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    exam = Examination(**payload.model_dump())
    db.add(exam)
    db.commit()
    db.refresh(exam)
    return exam


# ------------------------------------------------------------ Answer scripts
@router.post("/answer-scripts/upload", response_model=AnswerScriptOut, status_code=201)
def upload_answer_script(
    examination_id: int = Form(...),
    student_id: int = Form(...),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    suffix = Path(file.filename or "").suffix.lower()
    if suffix not in ALLOWED_SCRIPT_TYPES:
        raise HTTPException(status_code=400, detail="Only PDF/JPG/PNG answer scripts are supported")

    if not db.get(Examination, examination_id):
        raise HTTPException(status_code=404, detail="Examination not found")
    if not db.get(Student, student_id):
        raise HTTPException(status_code=404, detail="Student not found")

    stored_path = storage_service.save(file, subfolder="answer-scripts")
    script = AnswerScript(
        file_path=stored_path, file_type=suffix.lstrip("."),
        examination_id=examination_id, student_id=student_id, upload_status="uploaded",
    )
    db.add(script)
    db.commit()
    db.refresh(script)
    return script


@router.post("/answer-scripts/bulk-upload")
def bulk_upload_answer_scripts(
    examination_id: int = Form(...),
    student_ids: str = Form(..., description="Comma-separated student IDs, aligned with file order"),
    files: list[UploadFile] = File(...),
    db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    ids = [int(x) for x in student_ids.split(",") if x.strip()]
    if len(ids) != len(files):
        raise HTTPException(status_code=400, detail="student_ids count must match number of files")

    if not db.get(Examination, examination_id):
        raise HTTPException(status_code=404, detail="Examination not found")

    created_ids = []
    for student_id, file in zip(ids, files):
        suffix = Path(file.filename or "").suffix.lower()
        if suffix not in ALLOWED_SCRIPT_TYPES:
            continue
        stored_path = storage_service.save(file, subfolder="answer-scripts")
        script = AnswerScript(
            file_path=stored_path, file_type=suffix.lstrip("."),
            examination_id=examination_id, student_id=student_id, upload_status="uploaded",
        )
        db.add(script)
        db.flush()
        created_ids.append(script.id)

    db.commit()
    return {"created_answer_script_ids": created_ids, "count": len(created_ids)}


@router.get("/answer-scripts", response_model=list[AnswerScriptOut])
def list_answer_scripts(
    examination_id: int | None = None, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    query = db.query(AnswerScript)
    if examination_id:
        query = query.filter(AnswerScript.examination_id == examination_id)
    return query.order_by(AnswerScript.created_at.desc()).all()


# --------------------------------------------------------------- Evaluation
@router.post("/evaluations/run/{answer_script_id}", response_model=EvaluationOut)
def run_evaluation_sync(
    answer_script_id: int, db: Session = Depends(get_db),
    _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    """Runs the OCR->NLP->ML pipeline synchronously (good for a single script / demo)."""
    try:
        evaluation = run_pipeline(db, answer_script_id)
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc)) from exc
    return evaluation


@router.post("/evaluations/queue/{answer_script_id}")
def queue_evaluation(
    answer_script_id: int, _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER))
):
    """Enqueues the evaluation as a background Celery task (recommended for production).
    Requires Celery/Redis to be installed and running — not needed for the
    synchronous /evaluations/run/{id} endpoint above."""
    try:
        from services.celery_tasks import evaluate_answer_script_task
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Background evaluation requires Celery/Redis, which aren't installed in this "
            "environment. Use POST /evaluations/run/{answer_script_id} instead, or install the "
            "full requirements (`pip install celery redis`) and run a Celery worker.",
        ) from exc

    task = evaluate_answer_script_task.delay(answer_script_id)
    return {"task_id": task.id, "answer_script_id": answer_script_id, "status": "queued"}


@router.post("/evaluations/queue-batch")
def queue_batch_evaluation(
    answer_script_ids: list[int], _: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER))
):
    try:
        from services.celery_tasks import evaluate_batch_task
    except ModuleNotFoundError as exc:
        raise HTTPException(
            status_code=503,
            detail="Background evaluation requires Celery/Redis, which aren't installed in this "
            "environment. Use POST /evaluations/run/{answer_script_id} per script instead.",
        ) from exc

    task = evaluate_batch_task.delay(answer_script_ids)
    return {"task_id": task.id, "count": len(answer_script_ids), "status": "queued"}


@router.get("/evaluations", response_model=list[EvaluationOut])
def list_evaluations(
    status_filter: EvaluationStatus | None = None,
    db: Session = Depends(get_db), _: User = Depends(get_current_user),
):
    query = db.query(Evaluation)
    if status_filter:
        query = query.filter(Evaluation.status == status_filter)
    return query.order_by(Evaluation.updated_at.desc()).all()


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationOut)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return evaluation


# ----------------------------------------------------------- Teacher review
@router.post("/evaluations/{evaluation_id}/review", response_model=TeacherReviewOut)
def submit_review(
    evaluation_id: int, payload: TeacherReviewCreate, db: Session = Depends(get_db),
    current_user: User = Depends(require_roles(UserRole.ADMIN, UserRole.TEACHER)),
):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")

    review = evaluation.review or TeacherReview(evaluation_id=evaluation_id)
    review.reviewer_id = current_user.id
    review.decision = payload.decision
    review.adjusted_marks = payload.adjusted_marks
    review.reason = payload.reason
    review.comments = payload.comments
    db.add(review)

    if payload.decision == ReviewDecision.APPROVE:
        evaluation.status = EvaluationStatus.APPROVED
        evaluation.total_teacher_marks = (
            payload.adjusted_marks if payload.adjusted_marks is not None else evaluation.total_ai_marks
        )
    elif payload.decision == ReviewDecision.REJECT:
        evaluation.status = EvaluationStatus.REJECTED
        evaluation.total_teacher_marks = payload.adjusted_marks
    elif payload.decision == ReviewDecision.RE_EVALUATE:
        evaluation.status = EvaluationStatus.RE_EVALUATION_REQUESTED

    db.commit()
    db.refresh(review)
    return review


@router.get("/evaluations/{evaluation_id}/review", response_model=TeacherReviewOut)
def get_review(evaluation_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation or not evaluation.review:
        raise HTTPException(status_code=404, detail="Review not found")
    return evaluation.review
