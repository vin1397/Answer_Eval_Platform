"""
Shared enumerations for model fields.
"""
import enum


class UserRole(str, enum.Enum):
    ADMIN = "admin"
    TEACHER = "teacher"


class DifficultyLevel(str, enum.Enum):
    EASY = "easy"
    MEDIUM = "medium"
    HARD = "hard"


class BloomTaxonomy(str, enum.Enum):
    REMEMBER = "remember"
    UNDERSTAND = "understand"
    APPLY = "apply"
    ANALYZE = "analyze"
    EVALUATE = "evaluate"
    CREATE = "create"


class EvaluationStatus(str, enum.Enum):
    PENDING = "pending"
    OCR_IN_PROGRESS = "ocr_in_progress"
    NLP_IN_PROGRESS = "nlp_in_progress"
    AI_EVALUATED = "ai_evaluated"
    UNDER_REVIEW = "under_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    RE_EVALUATION_REQUESTED = "re_evaluation_requested"
    FAILED = "failed"


class ReviewDecision(str, enum.Enum):
    APPROVE = "approve"
    REJECT = "reject"
    RE_EVALUATE = "re_evaluate"
