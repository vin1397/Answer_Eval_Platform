"""
Dashboard summary cards, charts, and analytics endpoints.
"""
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends
from sqlalchemy import func
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models.academic import Subject, Student
from models.enums import EvaluationStatus
from models.exam import Examination, Evaluation, AnswerScript
from models.user import User

router = APIRouter(tags=["Dashboard & Analytics"])


@router.get("/dashboard/summary")
def dashboard_summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    total_subjects = db.query(func.count(Subject.id)).scalar() or 0
    total_exams = db.query(func.count(Examination.id)).scalar() or 0
    students_evaluated = (
        db.query(func.count(func.distinct(AnswerScript.student_id)))
        .join(Evaluation, Evaluation.answer_script_id == AnswerScript.id)
        .filter(Evaluation.status.in_([EvaluationStatus.APPROVED, EvaluationStatus.AI_EVALUATED]))
        .scalar()
        or 0
    )
    pending_evaluations = (
        db.query(func.count(Evaluation.id))
        .filter(Evaluation.status.in_([EvaluationStatus.PENDING, EvaluationStatus.UNDER_REVIEW]))
        .scalar()
        or 0
    )
    avg_marks_row = db.query(func.avg(Evaluation.total_ai_marks)).scalar()
    average_marks = round(float(avg_marks_row), 2) if avg_marks_row else 0.0

    today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
    todays_evaluations = (
        db.query(func.count(Evaluation.id)).filter(Evaluation.updated_at >= today_start).scalar() or 0
    )

    return {
        "total_subjects": total_subjects,
        "total_exams": total_exams,
        "students_evaluated": students_evaluated,
        "pending_evaluations": pending_evaluations,
        "average_marks": average_marks,
        "todays_evaluations": todays_evaluations,
    }


@router.get("/dashboard/charts")
def dashboard_charts(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    # Bar: evaluations grouped by status
    status_counts = (
        db.query(Evaluation.status, func.count(Evaluation.id)).group_by(Evaluation.status).all()
    )
    bar_chart = [{"status": s.value, "count": c} for s, c in status_counts]

    # Pie: answer scripts by file type
    type_counts = (
        db.query(AnswerScript.file_type, func.count(AnswerScript.id))
        .group_by(AnswerScript.file_type)
        .all()
    )
    pie_chart = [{"type": t, "count": c} for t, c in type_counts]

    # Line: evaluations completed per day, last 14 days
    fourteen_days_ago = datetime.utcnow() - timedelta(days=14)
    daily_counts = (
        db.query(func.date(Evaluation.updated_at), func.count(Evaluation.id))
        .filter(Evaluation.updated_at >= fourteen_days_ago)
        .group_by(func.date(Evaluation.updated_at))
        .order_by(func.date(Evaluation.updated_at))
        .all()
    )
    line_chart = [{"date": str(d), "count": c} for d, c in daily_counts]

    return {"bar_chart": bar_chart, "pie_chart": pie_chart, "line_chart": line_chart}


@router.get("/dashboard/recent-activity")
def recent_activity(limit: int = 10, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evaluations = (
        db.query(Evaluation).order_by(Evaluation.updated_at.desc()).limit(limit).all()
    )
    return [
        {
            "evaluation_id": e.id,
            "status": e.status.value,
            "total_ai_marks": e.total_ai_marks,
            "confidence_score": e.confidence_score,
            "updated_at": e.updated_at,
        }
        for e in evaluations
    ]


@router.get("/analytics/question-wise/{examination_id}")
def question_wise_performance(examination_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    scripts = (
        db.query(AnswerScript)
        .filter(AnswerScript.examination_id == examination_id)
        .all()
    )
    per_question: dict[str, list[float]] = {}
    for script in scripts:
        if not script.evaluation or not script.evaluation.extracted_answers:
            continue
        for answer in script.evaluation.extracted_answers:
            per_question.setdefault(answer["question_number"], []).append(answer["ai_marks"])

    return [
        {
            "question_number": q,
            "average_marks": round(sum(v) / len(v), 2),
            "attempts": len(v),
        }
        for q, v in sorted(per_question.items())
    ]


@router.get("/analytics/class-performance/{examination_id}")
def class_performance(examination_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    evaluations = (
        db.query(Evaluation)
        .join(AnswerScript, AnswerScript.id == Evaluation.answer_script_id)
        .filter(AnswerScript.examination_id == examination_id)
        .filter(Evaluation.total_ai_marks.isnot(None))
        .all()
    )
    if not evaluations:
        return {"class_average": 0, "highest": 0, "lowest": 0, "pass_percentage": 0, "count": 0}

    marks = [e.total_ai_marks for e in evaluations]
    max_marks = evaluations[0].total_max_marks or 100
    pass_mark = max_marks * 0.4
    passed = sum(1 for m in marks if m >= pass_mark)

    return {
        "class_average": round(sum(marks) / len(marks), 2),
        "highest": max(marks),
        "lowest": min(marks),
        "pass_percentage": round((passed / len(marks)) * 100, 2),
        "count": len(marks),
    }
