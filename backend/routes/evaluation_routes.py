"""
Examinations, answer script uploads, and the AI evaluation queue.
"""
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session

from api.schemas_exam import (
    ExaminationCreate, ExaminationOut, AnswerScriptOut, EvaluationOut,
    TeacherReviewCreate, TeacherReviewOut,
)
from models.exam import Question
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

MEDIA_TYPES = {"pdf": "application/pdf", "jpg": "image/jpeg", "jpeg": "image/jpeg", "png": "image/png"}


def _with_question_context(db: Session, evaluation: Evaluation) -> dict:
    """Attaches per-question context (question text + faculty reference) to an
    evaluation response so the UI can render a meaningful side-by-side review
    instead of a bare OCR string."""
    data = EvaluationOut.model_validate(evaluation).model_dump()
    script = evaluation.answer_script
    student = script.student if script else None
    exam = script.examination if script else None
    data["student_name"] = student.name if student else None
    data["student_usn"] = student.usn if student else None
    data["examination_name"] = exam.name if exam else None
    data["answer_script_file_type"] = script.file_type if script else None

    context: dict[str, dict] = {}
    if exam and exam.question_paper_id:
        questions = (
            db.query(Question)
            .filter(Question.question_paper_id == exam.question_paper_id)
            .all()
        )
        for q in questions:
            model_answer = q.model_answer
            context[str(q.question_number)] = {
                "question_text": q.question_text,
                "max_marks": q.max_marks,
                "question_type": q.question_type.value,
                "reference_answer": model_answer.answer_text if model_answer else None,
                "correct_option": model_answer.correct_option if model_answer else None,
                "keywords": model_answer.keywords if model_answer else [],
            }
    data["question_context"] = context
    return data


@router.get("/answer-scripts/{script_id}/file")
def get_answer_script_file(
    script_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """Serves the stored answer-sheet file (inline) so the UI can display the
    actual scanned/typed script in a viewer. Requires authentication; the
    stored path never leaks to the client response."""
    script = db.get(AnswerScript, script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Answer script not found")

    path = Path(storage_service.resolve_local_path(script.file_path))
    if not path.is_file():
        raise HTTPException(status_code=404, detail="Stored file is missing on the server")

    media_type = MEDIA_TYPES.get(script.file_type, "application/octet-stream")
    return FileResponse(path, media_type=media_type, headers={"Content-Disposition": "inline"})


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
    scripts = query.order_by(AnswerScript.created_at.desc()).all()

    items = []
    for script in scripts:
        out = AnswerScriptOut.model_validate(script).model_dump()
        evaluation = script.evaluation
        student = script.student
        exam = script.examination
        out["student_name"] = student.name if student else None
        out["student_usn"] = student.usn if student else None
        out["examination_name"] = exam.name if exam else None
        out["evaluation_status"] = evaluation.status.value if evaluation else "not_evaluated"
        out["final_marks"] = evaluation.final_marks if evaluation else None
        out["total_max_marks"] = evaluation.total_max_marks if evaluation else None
        out["evaluation_id"] = evaluation.id if evaluation else None
        items.append(out)
    return items


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
    db.refresh(evaluation)
    return _with_question_context(db, evaluation)


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
    evaluations = query.order_by(Evaluation.updated_at.desc()).all()
    return [_with_question_context(db, ev) for ev in evaluations]


@router.get("/evaluations/{evaluation_id}", response_model=EvaluationOut)
def get_evaluation(evaluation_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evaluation = db.get(Evaluation, evaluation_id)
    if not evaluation:
        raise HTTPException(status_code=404, detail="Evaluation not found")
    return _with_question_context(db, evaluation)


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
