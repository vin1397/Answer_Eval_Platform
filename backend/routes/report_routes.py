"""
Report generation: student/exam reports as PDF (ReportLab) or Excel.
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from sqlalchemy.orm import Session

from auth.dependencies import get_current_user
from database.session import get_db
from models.exam import Examination, AnswerScript, Evaluation
from models.academic import Student
from models.user import User

router = APIRouter(tags=["Reports"])


@router.get("/reports/exam/{examination_id}/pdf")
def exam_report_pdf(examination_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = db.get(Examination, examination_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    scripts = db.query(AnswerScript).filter(AnswerScript.examination_id == examination_id).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Examination Report — {exam.name}", styles["Title"]),
        Spacer(1, 12),
    ]

    data = [["USN", "Student", "AI Marks", "Teacher Marks", "Final Marks", "Status", "Confidence"]]
    for script in scripts:
        student = db.get(Student, script.student_id)
        evaluation = script.evaluation
        data.append(
            [
                student.usn if student else "-",
                student.name if student else "-",
                evaluation.total_ai_marks if evaluation else "-",
                evaluation.total_teacher_marks if evaluation else "-",
                evaluation.final_marks if evaluation else "-",
                evaluation.status.value if evaluation else "not evaluated",
                evaluation.confidence_score if evaluation else "-",
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#9C8CD4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("FONTSIZE", (0, 0), (-1, -1), 9),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
                ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F7F5FF")]),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=exam_{examination_id}_report.pdf"},
    )


@router.get("/reports/exam/{examination_id}/excel")
def exam_report_excel(examination_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    exam = db.get(Examination, examination_id)
    if not exam:
        raise HTTPException(status_code=404, detail="Examination not found")

    scripts = db.query(AnswerScript).filter(AnswerScript.examination_id == examination_id).all()
    rows = []
    for script in scripts:
        student = db.get(Student, script.student_id)
        evaluation = script.evaluation
        rows.append(
            {
                "USN": student.usn if student else "-",
                "Student": student.name if student else "-",
                "AI Marks": evaluation.total_ai_marks if evaluation else None,
                "Teacher Marks": evaluation.total_teacher_marks if evaluation else None,
                "Final Marks": evaluation.final_marks if evaluation else None,
                "Status": evaluation.status.value if evaluation else "not evaluated",
                "Confidence": evaluation.confidence_score if evaluation else None,
            }
        )

    df = pd.DataFrame(rows)
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, sheet_name="Exam Report")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": f"attachment; filename=exam_{examination_id}_report.xlsx"},
    )


@router.get("/reports/student/{student_id}/pdf")
def student_report_pdf(student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    scripts = db.query(AnswerScript).filter(AnswerScript.student_id == student_id).all()

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    styles = getSampleStyleSheet()
    elements = [
        Paragraph(f"Student Report — {student.name} ({student.usn})", styles["Title"]),
        Spacer(1, 12),
    ]

    data = [["Examination", "AI Marks", "Teacher Marks", "Final Marks", "Status"]]
    for script in scripts:
        exam = db.get(Examination, script.examination_id)
        evaluation = script.evaluation
        data.append(
            [
                exam.name if exam else "-",
                evaluation.total_ai_marks if evaluation else "-",
                evaluation.total_teacher_marks if evaluation else "-",
                evaluation.final_marks if evaluation else "-",
                evaluation.status.value if evaluation else "not evaluated",
            ]
        )

    table = Table(data, repeatRows=1)
    table.setStyle(
        TableStyle(
            [
                ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#9C8CD4")),
                ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
                ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
            ]
        )
    )
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)

    return StreamingResponse(
        buffer, media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename=student_{student_id}_report.pdf"},
    )
