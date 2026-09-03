"""
Orchestrates the end-to-end AI evaluation pipeline for a single answer
script, matching the flow specified in the project brief:

  Answer Script -> PDF/page extraction -> handwriting line segmentation
  -> local TrOCR -> question-number association -> per-question scoring
  (MCQ exact-match OR descriptive semantic+keyword) -> ML confidence
  -> Final Marks -> (Teacher Review)

This module is intentionally transport-agnostic: it is called directly by
the synchronous API route for small/interactive runs, and by the Celery
task (services/celery_tasks.py) for background/batch runs.
"""
from __future__ import annotations

import logging
from datetime import datetime

from sqlalchemy.orm import Session

from ai.ml import ml_service
from ai.nlp import nlp_service
from ai.ocr import ocr_service
from ai.ocr.trocr_service import TrOCRModelNotFoundError
from models.enums import EvaluationStatus, QuestionType
from models.exam import AnswerScript, Evaluation, Question, ModelAnswer

logger = logging.getLogger(__name__)

AI_MODEL_VERSION = "eval-pipeline-2.0-trocr"


def run_pipeline(db: Session, answer_script_id: int) -> Evaluation:
    script = db.query(AnswerScript).filter(AnswerScript.id == answer_script_id).first()
    if script is None:
        raise ValueError(f"AnswerScript {answer_script_id} not found")

    evaluation = script.evaluation
    if evaluation is None:
        evaluation = Evaluation(answer_script_id=script.id, status=EvaluationStatus.PENDING)
        db.add(evaluation)
        db.flush()

    def set_progress(status: EvaluationStatus, detail: str) -> None:
        evaluation.status = status
        evaluation.status_detail = detail
        db.commit()

    try:
        # 1. OCR -----------------------------------------------------------
        set_progress(EvaluationStatus.OCR_IN_PROGRESS, "Processing PDF and detecting answer regions")

        try:
            ocr_result = ocr_service.extract_document(script.file_path)
        except TrOCRModelNotFoundError as exc:
            # Distinct, actionable error — never silently falls back to a
            # different engine or produces a fabricated result.
            raise RuntimeError(
                f"Local handwriting OCR model is not installed correctly: {exc}"
            ) from exc
        except FileNotFoundError as exc:
            raise RuntimeError(f"Could not read the uploaded answer script file: {exc}") from exc

        evaluation.ocr_raw_text = ocr_result.full_text
        evaluation.has_uncertain_segments = ocr_result.has_uncertain_segments
        set_progress(EvaluationStatus.OCR_IN_PROGRESS, "Running handwriting OCR")

        # 2. Fetch questions + model answers for this script's exam --------
        exam = script.examination
        questions: list[Question] = []
        if exam.question_paper_id:
            questions = (
                db.query(Question)
                .filter(Question.question_paper_id == exam.question_paper_id)
                .all()
            )

        # 3. Scoring per question -------------------------------------------
        set_progress(EvaluationStatus.NLP_IN_PROGRESS, "Evaluating answers")

        extracted_answers = []
        total_ai_marks = 0.0
        total_max_marks = 0.0
        confidences = []
        any_uncertain = ocr_result.has_uncertain_segments

        for question in questions:
            model_answer: ModelAnswer | None = question.model_answer
            student_answer_text = ocr_result.question_segments.get(question.question_number, "")
            segment_meta = ocr_result.structured_answers.get(question.question_number, {})

            if not student_answer_text.strip():
                # Question-number segment wasn't found at all for this
                # student — never guess; record it plainly as unanswered.
                extracted_answers.append(
                    {
                        "question_number": question.question_number,
                        "answer_text": "",
                        "semantic_score": 0.0,
                        "keyword_score": 0.0,
                        "ai_marks": 0.0,
                        "max_marks": question.max_marks,
                        "confidence": 0.0,
                        "uncertain": True,
                        "question_type": question.question_type.value,
                        "note": "No answer detected for this question number",
                    }
                )
                total_max_marks += question.max_marks
                any_uncertain = True
                continue

            if model_answer is None:
                extracted_answers.append(
                    {
                        "question_number": question.question_number,
                        "answer_text": student_answer_text,
                        "semantic_score": 0.0,
                        "keyword_score": 0.0,
                        "ai_marks": 0.0,
                        "max_marks": question.max_marks,
                        "confidence": 0.0,
                        "uncertain": True,
                        "question_type": question.question_type.value,
                        "note": "No reference/model answer configured for this question",
                    }
                )
                total_max_marks += question.max_marks
                any_uncertain = True
                continue

            # ---- MCQ: exact-match scoring, no semantic model involved ----
            if question.question_type == QuestionType.MCQ:
                question_score = nlp_service.score_mcq(
                    question_number=question.question_number,
                    student_answer=student_answer_text,
                    correct_option=model_answer.correct_option or "",
                    max_marks=question.max_marks,
                )
                option_detected = question_score.extra.get("option_detected", False)
                confidence = 1.0 if option_detected else 0.3
            else:
                # ---- Descriptive: existing semantic + keyword pipeline ----
                question_score = nlp_service.score_question(
                    question_number=question.question_number,
                    student_answer=student_answer_text,
                    model_answer=model_answer.answer_text or "",
                    keywords=model_answer.keywords or [],
                    max_marks=question.max_marks,
                )
                confidence = ml_service.predict_confidence(
                    semantic_score=question_score.semantic_score,
                    keyword_score=question_score.keyword_score,
                    answer_length=len(student_answer_text),
                    difficulty=question.difficulty.value,
                )

            confidences.append(confidence)
            segment_uncertain = bool(segment_meta.get("uncertain", False))

            extracted_answers.append(
                {
                    "question_number": question_score.question_number,
                    "answer_text": student_answer_text,
                    "semantic_score": question_score.semantic_score,
                    "keyword_score": question_score.keyword_score,
                    "ai_marks": question_score.ai_marks,
                    "max_marks": question_score.max_marks,
                    "confidence": confidence,
                    "uncertain": segment_uncertain,
                    "question_type": question.question_type.value,
                    "matched_keywords": question_score.matched_keywords,
                    "missing_keywords": question_score.missing_keywords,
                    **({"mcq": question_score.extra} if question_score.extra else {}),
                }
            )
            total_ai_marks += question_score.ai_marks
            total_max_marks += question_score.max_marks
            any_uncertain = any_uncertain or segment_uncertain

        evaluation.extracted_answers = extracted_answers
        evaluation.total_ai_marks = round(total_ai_marks, 2)
        evaluation.total_max_marks = round(total_max_marks, 2)
        evaluation.has_uncertain_segments = any_uncertain
        evaluation.confidence_score = (
            round(sum(confidences) / len(confidences), 4) if confidences else 0.0
        )
        evaluation.ai_model_version = AI_MODEL_VERSION
        evaluation.status = EvaluationStatus.AI_EVALUATED
        evaluation.status_detail = "Completed"
        evaluation.updated_at = datetime.utcnow()

        # Route to teacher review when the AI is not confident enough, OR
        # when any segment's question-number association was uncertain —
        # never silently finalize a guess.
        if any_uncertain or ml_service.needs_teacher_review(evaluation.confidence_score or 0.0):
            evaluation.status = EvaluationStatus.UNDER_REVIEW
            evaluation.status_detail = "Needs Review"

        db.commit()
        db.refresh(evaluation)
        return evaluation

    except Exception as exc:  # noqa: BLE001
        logger.exception("Evaluation pipeline failed for answer_script_id=%s", answer_script_id)
        evaluation.status = EvaluationStatus.FAILED
        evaluation.status_detail = "Failed"
        evaluation.error_message = str(exc)
        db.commit()
        raise
