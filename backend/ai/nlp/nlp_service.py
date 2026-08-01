"""
NLP service: semantic similarity + keyword/concept matching between a
student's OCR-extracted answer and the faculty-authored model answer.

Uses Sentence-Transformers (all-MiniLM-L6-v2 by default) for dense
sentence embeddings and cosine similarity, combined with a lightweight
lexical keyword-overlap score. The two scores are blended into a single
per-question mark using weights from application settings.
"""
from __future__ import annotations

import re
import logging
from dataclasses import dataclass
from functools import lru_cache

import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

from config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

_TOKEN_RE = re.compile(r"[a-zA-Z][a-zA-Z\-]{2,}")
_STOPWORDS = {
    "the", "and", "for", "are", "with", "that", "this", "from", "have",
    "has", "was", "were", "will", "can", "not", "but", "which", "their",
    "into", "than", "then", "also", "such", "these", "those", "when",
}


@dataclass
class QuestionScore:
    question_number: str
    semantic_score: float  # 0..1
    keyword_score: float  # 0..1
    combined_score: float  # 0..1
    ai_marks: float
    max_marks: float
    matched_keywords: list[str]
    missing_keywords: list[str]


@lru_cache(maxsize=1)
def _get_embedder():
    from sentence_transformers import SentenceTransformer  # heavy, lazy import

    return SentenceTransformer(settings.SENTENCE_TRANSFORMER_MODEL)


def embed_text(text: str) -> np.ndarray:
    model = _get_embedder()
    return model.encode([text], normalize_embeddings=True)[0]


def embed_texts(texts: list[str]) -> np.ndarray:
    model = _get_embedder()
    return model.encode(texts, normalize_embeddings=True)


def semantic_similarity(student_answer: str, model_answer: str) -> float:
    """Cosine similarity between the two answers' sentence embeddings, clamped to [0, 1]."""
    if not student_answer.strip() or not model_answer.strip():
        return 0.0
    embeddings = embed_texts([student_answer, model_answer])
    score = float(cosine_similarity([embeddings[0]], [embeddings[1]])[0][0])
    return max(0.0, min(1.0, score))


def _tokenize(text: str) -> set[str]:
    tokens = {t.lower() for t in _TOKEN_RE.findall(text)}
    return tokens - _STOPWORDS


def keyword_match_score(student_answer: str, keywords: list[str]) -> tuple[float, list[str], list[str]]:
    """
    Fraction of the model answer's rubric keywords/expected concepts that
    also appear (as a substring or exact token) in the student's answer.
    """
    if not keywords:
        return 1.0, [], []  # no rubric keywords defined -> don't penalise

    answer_lower = student_answer.lower()
    answer_tokens = _tokenize(student_answer)

    matched, missing = [], []
    for kw in keywords:
        kw_lower = kw.lower().strip()
        if not kw_lower:
            continue
        hit = kw_lower in answer_lower or any(
            kw_lower == tok or kw_lower in tok for tok in answer_tokens
        )
        (matched if hit else missing).append(kw)

    score = len(matched) / max(len(matched) + len(missing), 1)
    return score, matched, missing


def detect_paraphrase(student_answer: str, model_answer: str, threshold: float = 0.55) -> bool:
    """
    Heuristic paraphrase flag: high semantic similarity but low lexical
    (word) overlap implies the student re-expressed the concept in their
    own words rather than copying verbatim.
    """
    sem = semantic_similarity(student_answer, model_answer)
    student_tokens = _tokenize(student_answer)
    model_tokens = _tokenize(model_answer)
    if not student_tokens or not model_tokens:
        return False
    lexical_overlap = len(student_tokens & model_tokens) / len(model_tokens)
    return sem >= threshold and lexical_overlap < 0.3


def score_question(
    question_number: str,
    student_answer: str,
    model_answer: str,
    keywords: list[str],
    max_marks: float,
) -> QuestionScore:
    semantic = semantic_similarity(student_answer, model_answer)
    keyword_score, matched, missing = keyword_match_score(student_answer, keywords)

    combined = (
        settings.SIMILARITY_WEIGHT * semantic + settings.KEYWORD_WEIGHT * keyword_score
    )
    combined = max(0.0, min(1.0, combined))
    ai_marks = round(combined * max_marks, 2)

    return QuestionScore(
        question_number=question_number,
        semantic_score=round(semantic, 4),
        keyword_score=round(keyword_score, 4),
        combined_score=round(combined, 4),
        ai_marks=ai_marks,
        max_marks=max_marks,
        matched_keywords=matched,
        missing_keywords=missing,
    )
