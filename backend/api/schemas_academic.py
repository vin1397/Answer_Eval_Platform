"""
Pydantic schemas for Semester, Scheme, Faculty, Subject, Student.
"""
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class SemesterBase(BaseModel):
    name: str
    number: int = Field(..., ge=1, le=8)


class SemesterCreate(SemesterBase):
    pass


class SemesterOut(SemesterBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class SchemeBase(BaseModel):
    name: str
    year: int
    is_active: bool = True


class SchemeCreate(SchemeBase):
    pass


class SchemeOut(SchemeBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class FacultyBase(BaseModel):
    name: str
    designation: str | None = None
    department: str
    email: EmailStr
    phone: str | None = None


class FacultyCreate(FacultyBase):
    pass


class FacultyOut(FacultyBase):
    id: int
    model_config = {"from_attributes": True}


class SubjectBase(BaseModel):
    code: str
    name: str
    credits: int = 4
    department: str
    semester_id: int
    scheme_id: int
    faculty_id: int | None = None


class SubjectCreate(SubjectBase):
    pass


class SubjectUpdate(BaseModel):
    code: str | None = None
    name: str | None = None
    credits: int | None = None
    department: str | None = None
    semester_id: int | None = None
    scheme_id: int | None = None
    faculty_id: int | None = None


class SubjectOut(SubjectBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class StudentBase(BaseModel):
    usn: str
    name: str
    section: str
    department: str
    semester_id: int
    email: EmailStr | None = None
    phone: str | None = None


class StudentCreate(StudentBase):
    pass


class StudentUpdate(BaseModel):
    name: str | None = None
    section: str | None = None
    department: str | None = None
    semester_id: int | None = None
    email: EmailStr | None = None
    phone: str | None = None


class StudentOut(StudentBase):
    id: int
    created_at: datetime
    model_config = {"from_attributes": True}


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list
