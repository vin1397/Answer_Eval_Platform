"""
Institute-level settings (name, logo, departments) and admin profile
management. Institute settings are stored as a single-row JSON config
table for simplicity.
"""
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy import JSON, Integer
from sqlalchemy.orm import Mapped, mapped_column, Session

from auth.dependencies import require_admin, get_current_user
from database.session import Base, get_db
from models.user import User

router = APIRouter(tags=["Settings"])


class InstituteSettings(Base):
    __tablename__ = "institute_settings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, default=1)
    data: Mapped[dict] = mapped_column(JSON, default=dict)


class InstituteSettingsPayload(BaseModel):
    institute_name: str
    logo_url: str | None = None
    departments: list[str] = []
    default_pass_percentage: float = 40.0


@router.get("/settings/institute")
def get_institute_settings(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    row = db.get(InstituteSettings, 1)
    if not row:
        return InstituteSettingsPayload(institute_name="", departments=[]).model_dump()
    return row.data


@router.put("/settings/institute")
def update_institute_settings(
    payload: InstituteSettingsPayload, db: Session = Depends(get_db), _: User = Depends(require_admin)
):
    row = db.get(InstituteSettings, 1)
    if not row:
        row = InstituteSettings(id=1, data=payload.model_dump())
        db.add(row)
    else:
        row.data = payload.model_dump()
    db.commit()
    return row.data
