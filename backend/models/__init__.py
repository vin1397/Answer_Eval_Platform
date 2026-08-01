"""
Import every model module here so that `Base.metadata` is fully populated
when `database.session.Base` is imported anywhere (e.g. by Alembic env.py
or `create_all` in dev bootstrap).
"""
from models.user import User  # noqa: F401
from models.academic import Semester, Scheme, Faculty, Subject, Student  # noqa: F401
from models.exam import (  # noqa: F401
    QuestionPaper,
    Question,
    ModelAnswer,
    Examination,
    AnswerScript,
    Evaluation,
    TeacherReview,
)
from models.enums import (  # noqa: F401
    UserRole,
    DifficultyLevel,
    BloomTaxonomy,
    EvaluationStatus,
    ReviewDecision,
)
