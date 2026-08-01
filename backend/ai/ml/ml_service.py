"""
Machine Learning service.

On top of the raw NLP similarity/keyword scores, this module trains and
serves a lightweight scikit-learn model (Gradient Boosting Regressor)
that learns from *teacher-corrected* marks to predict a calibrated
confidence score for each AI-generated mark, and flags evaluations that
likely need human review (low confidence / high predicted deviation).

Training data comes from `TeacherReview` records: (semantic_score,
keyword_score, question_difficulty, answer_length) -> abs(ai_marks -
teacher_marks). Models are versioned and persisted to ML_MODEL_DIR.
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import joblib
import numpy as np
from sklearn.ensemble import GradientBoostingRegressor
from sklearn.metrics import mean_absolute_error, r2_score
from sklearn.model_selection import train_test_split

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

FEATURE_NAMES = ["semantic_score", "keyword_score", "answer_length_norm", "difficulty_weight"]
DIFFICULTY_WEIGHTS = {"easy": 0.3, "medium": 0.6, "hard": 1.0}


@dataclass
class TrainingMetrics:
    mae: float
    r2: float
    n_samples: int
    trained_at: str
    model_version: str


def _model_dir() -> Path:
    d = Path(settings.ML_MODEL_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def build_feature_vector(
    semantic_score: float, keyword_score: float, answer_length: int, difficulty: str
) -> np.ndarray:
    answer_length_norm = min(answer_length / 500.0, 1.0)
    difficulty_weight = DIFFICULTY_WEIGHTS.get(difficulty, 0.6)
    return np.array([[semantic_score, keyword_score, answer_length_norm, difficulty_weight]])


def train_deviation_model(training_rows: list[dict]) -> TrainingMetrics:
    """
    training_rows: list of dicts with keys
      semantic_score, keyword_score, answer_length, difficulty, deviation
    (deviation = abs(ai_marks - teacher_marks) / max_marks, in [0, 1])
    """
    if len(training_rows) < 20:
        raise ValueError("Need at least 20 reviewed evaluations to train a reliable model")

    X = np.vstack(
        [
            build_feature_vector(
                r["semantic_score"], r["keyword_score"], r["answer_length"], r["difficulty"]
            )[0]
            for r in training_rows
        ]
    )
    y = np.array([r["deviation"] for r in training_rows])

    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

    model = GradientBoostingRegressor(
        n_estimators=200, max_depth=3, learning_rate=0.05, random_state=42
    )
    model.fit(X_train, y_train)

    predictions = model.predict(X_test)
    mae = float(mean_absolute_error(y_test, predictions))
    r2 = float(r2_score(y_test, predictions)) if len(y_test) > 1 else 0.0

    version = datetime.utcnow().strftime("v%Y%m%d_%H%M%S")
    joblib.dump(model, _model_dir() / f"deviation_model_{version}.joblib")
    joblib.dump(model, _model_dir() / "deviation_model_latest.joblib")

    metrics = TrainingMetrics(
        mae=round(mae, 4), r2=round(r2, 4), n_samples=len(training_rows),
        trained_at=datetime.utcnow().isoformat(), model_version=version,
    )
    (_model_dir() / f"deviation_model_{version}_metrics.json").write_text(
        json.dumps(metrics.__dict__, indent=2)
    )
    return metrics


def _load_latest_model():
    path = _model_dir() / "deviation_model_latest.joblib"
    if not path.exists():
        return None
    return joblib.load(path)


def predict_confidence(
    semantic_score: float, keyword_score: float, answer_length: int, difficulty: str
) -> float:
    """
    Returns a confidence score in [0, 1] for an AI-generated mark.
    Falls back to a rule-based heuristic when no trained model exists yet
    (e.g. a brand-new deployment with no teacher review history).
    """
    model = _load_latest_model()
    if model is None:
        # Heuristic fallback: confidence is high when semantic + keyword
        # scores agree closely (low variance between the two signals).
        agreement = 1.0 - abs(semantic_score - keyword_score)
        base = 0.5 * semantic_score + 0.5 * agreement
        return round(max(0.0, min(1.0, base)), 4)

    features = build_feature_vector(semantic_score, keyword_score, answer_length, difficulty)
    predicted_deviation = float(model.predict(features)[0])
    confidence = 1.0 - min(max(predicted_deviation, 0.0), 1.0)
    return round(confidence, 4)


def needs_teacher_review(confidence: float) -> bool:
    return confidence < settings.AUTO_APPROVE_CONFIDENCE_THRESHOLD
