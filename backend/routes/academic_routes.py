"""
CRUD endpoints for Semesters, Schemes, Faculty, Subjects, and Students —
each with search, filtering, and pagination for Students/Subjects.
"""
import io

import pandas as pd
from fastapi import APIRouter, Depends, HTTPException, Query, UploadFile, File, status
from fastapi.responses import StreamingResponse
from sqlalchemy import or_
from sqlalchemy.orm import Session

from api.schemas_academic import (
    SemesterCreate, SemesterOut, SchemeCreate, SchemeOut, FacultyCreate, FacultyOut,
    SubjectCreate, SubjectUpdate, SubjectOut, StudentCreate, StudentUpdate, StudentOut,
)
from api.schemas_results import StudentResultOut
from auth.dependencies import get_current_user, require_admin
from database.session import get_db
from models.academic import Semester, Scheme, Faculty, Subject, Student
from models.exam import Examination, AnswerScript, Evaluation
from models.user import User

router = APIRouter(tags=["Academic"])


# ---------------------------------------------------------------- Semester
@router.get("/semesters", response_model=list[SemesterOut])
def list_semesters(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Semester).order_by(Semester.number).all()


@router.post("/semesters", response_model=SemesterOut, status_code=status.HTTP_201_CREATED)
def create_semester(payload: SemesterCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    semester = Semester(**payload.model_dump())
    db.add(semester)
    db.commit()
    db.refresh(semester)
    return semester


@router.delete("/semesters/{semester_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_semester(semester_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    semester = db.get(Semester, semester_id)
    if not semester:
        raise HTTPException(status_code=404, detail="Semester not found")
    db.delete(semester)
    db.commit()


# ------------------------------------------------------------------ Scheme
@router.get("/schemes", response_model=list[SchemeOut])
def list_schemes(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Scheme).order_by(Scheme.year.desc()).all()


@router.post("/schemes", response_model=SchemeOut, status_code=status.HTTP_201_CREATED)
def create_scheme(payload: SchemeCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    scheme = Scheme(**payload.model_dump())
    db.add(scheme)
    db.commit()
    db.refresh(scheme)
    return scheme


@router.delete("/schemes/{scheme_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_scheme(scheme_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    scheme = db.get(Scheme, scheme_id)
    if not scheme:
        raise HTTPException(status_code=404, detail="Scheme not found")
    db.delete(scheme)
    db.commit()


# ----------------------------------------------------------------- Faculty
@router.get("/faculty", response_model=list[FacultyOut])
def list_faculty(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return db.query(Faculty).order_by(Faculty.name).all()


@router.post("/faculty", response_model=FacultyOut, status_code=status.HTTP_201_CREATED)
def create_faculty(payload: FacultyCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    faculty = Faculty(**payload.model_dump())
    db.add(faculty)
    db.commit()
    db.refresh(faculty)
    return faculty


@router.delete("/faculty/{faculty_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_faculty(faculty_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    faculty = db.get(Faculty, faculty_id)
    if not faculty:
        raise HTTPException(status_code=404, detail="Faculty not found")
    db.delete(faculty)
    db.commit()


# ----------------------------------------------------------------- Subject
@router.get("/subjects")
def list_subjects(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    search: str | None = None,
    semester_id: int | None = None,
    scheme_id: int | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Subject)
    if search:
        query = query.filter(or_(Subject.name.ilike(f"%{search}%"), Subject.code.ilike(f"%{search}%")))
    if semester_id:
        query = query.filter(Subject.semester_id == semester_id)
    if scheme_id:
        query = query.filter(Subject.scheme_id == scheme_id)

    total = query.count()
    items = query.order_by(Subject.name).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [SubjectOut.model_validate(i) for i in items],
    }


@router.post("/subjects", response_model=SubjectOut, status_code=status.HTTP_201_CREATED)
def create_subject(payload: SubjectCreate, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    subject = Subject(**payload.model_dump())
    db.add(subject)
    db.commit()
    db.refresh(subject)
    return subject


@router.put("/subjects/{subject_id}", response_model=SubjectOut)
def update_subject(
    subject_id: int, payload: SubjectUpdate, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(subject, field, value)
    db.commit()
    db.refresh(subject)
    return subject


@router.delete("/subjects/{subject_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_subject(subject_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    subject = db.get(Subject, subject_id)
    if not subject:
        raise HTTPException(status_code=404, detail="Subject not found")
    db.delete(subject)
    db.commit()


# ----------------------------------------------------------------- Student
@router.get("/students")
def list_students(
    db: Session = Depends(get_db),
    _: User = Depends(get_current_user),
    search: str | None = None,
    semester_id: int | None = None,
    section: str | None = None,
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
):
    query = db.query(Student)
    if search:
        query = query.filter(or_(Student.name.ilike(f"%{search}%"), Student.usn.ilike(f"%{search}%")))
    if semester_id:
        query = query.filter(Student.semester_id == semester_id)
    if section:
        query = query.filter(Student.section == section)

    total = query.count()
    items = query.order_by(Student.usn).offset((page - 1) * page_size).limit(page_size).all()
    return {
        "total": total, "page": page, "page_size": page_size,
        "items": [StudentOut.model_validate(i) for i in items],
    }


@router.post("/students", response_model=StudentOut, status_code=status.HTTP_201_CREATED)
def create_student(payload: StudentCreate, db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    existing = db.query(Student).filter(Student.usn == payload.usn).first()
    if existing:
        raise HTTPException(status_code=400, detail="A student with this USN already exists")
    student = Student(**payload.model_dump())
    db.add(student)
    db.commit()
    db.refresh(student)
    return student


@router.put("/students/{student_id}", response_model=StudentOut)
def update_student(
    student_id: int, payload: StudentUpdate, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    for field, value in payload.model_dump(exclude_unset=True).items():
        setattr(student, field, value)
    db.commit()
    db.refresh(student)
    return student


@router.delete("/students/{student_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_student(student_id: int, db: Session = Depends(get_db), _: User = Depends(require_admin)):
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    db.delete(student)
    db.commit()


@router.get("/students/{student_id}/results", response_model=list[StudentResultOut])
def get_student_results(
    student_id: int, db: Session = Depends(get_db), _: User = Depends(get_current_user)
):
    """Per-examination result card for one student: script, evaluation status,
    AI marks, final (teacher-approved) marks, and confidence. `final_marks`
    follows the teacher-precedence rule implemented on the Evaluation model."""
    student = db.get(Student, student_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")

    scripts = (
        db.query(AnswerScript)
        .filter(AnswerScript.student_id == student_id)
        .order_by(AnswerScript.created_at.desc())
        .all()
    )
    results: list[dict] = []
    for script in scripts:
        exam = db.get(Examination, script.examination_id)
        evaluation: Evaluation | None = script.evaluation
        results.append(
            {
                "examination_id": exam.id if exam else None,
                "examination_name": exam.name if exam else "Unknown examination",
                "exam_date": exam.exam_date if exam else None,
                "answer_script_id": script.id,
                "evaluation_id": evaluation.id if evaluation else None,
                "evaluation_status": evaluation.status.value if evaluation else "not_evaluated",
                "ai_marks": evaluation.total_ai_marks if evaluation else None,
                "max_marks": evaluation.total_max_marks if evaluation else None,
                "final_marks": evaluation.final_marks if evaluation else None,
                "confidence": evaluation.confidence_score if evaluation else None,
                "evaluated_at": evaluation.updated_at if evaluation else None,
            }
        )
    return results


@router.post("/students/import-excel")
def import_students_excel(
    file: UploadFile = File(...), db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    """Bulk-import students from an .xlsx file with columns:
    usn, name, section, department, semester_id, email, phone"""
    if not file.filename.endswith((".xlsx", ".xls")):
        raise HTTPException(status_code=400, detail="Please upload an Excel (.xlsx) file")

    df = pd.read_excel(io.BytesIO(file.file.read()))
    required_cols = {"usn", "name", "section", "department", "semester_id"}
    missing = required_cols - set(df.columns.str.lower())
    if missing:
        raise HTTPException(status_code=400, detail=f"Missing required columns: {', '.join(missing)}")

    df.columns = [c.lower() for c in df.columns]
    created, skipped = 0, 0
    for _, row in df.iterrows():
        if db.query(Student).filter(Student.usn == str(row["usn"])).first():
            skipped += 1
            continue
        student = Student(
            usn=str(row["usn"]),
            name=str(row["name"]),
            section=str(row["section"]),
            department=str(row["department"]),
            semester_id=int(row["semester_id"]),
            email=str(row["email"]) if "email" in df.columns and pd.notna(row.get("email")) else None,
            phone=str(row["phone"]) if "phone" in df.columns and pd.notna(row.get("phone")) else None,
        )
        db.add(student)
        created += 1

    db.commit()
    return {"created": created, "skipped_duplicates": skipped}


@router.get("/students/export-excel")
def export_students_excel(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    students = db.query(Student).order_by(Student.usn).all()
    df = pd.DataFrame(
        [
            {
                "usn": s.usn, "name": s.name, "section": s.section, "department": s.department,
                "semester_id": s.semester_id, "email": s.email, "phone": s.phone,
            }
            for s in students
        ]
    )
    buffer = io.BytesIO()
    df.to_excel(buffer, index=False, sheet_name="Students")
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        headers={"Content-Disposition": "attachment; filename=students_export.xlsx"},
    )
