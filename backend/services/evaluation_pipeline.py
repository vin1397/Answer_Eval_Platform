"""
Orchestrates the end-to-end AI evaluation pipeline for a single answer
script, matching the flow specified in the project brief:

  Answer Script -> OCR -> Answer Segmentation -> Semantic Similarity
  -> Keyword Matching -> ML Confidence -> Final Marks -> (Teacher Review)

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
from models.enums import EvaluationStatus
from models.exam import AnswerScript, Evaluation, Question, ModelAnswer

logger = logging.getLogger(__name__)

AI_MODEL_VERSION = "eval-pipeline-1.0"


def run_pipeline(db: Session, answer_script_id: int) -> Evaluation:
    script = db.query(AnswerScript).filter(AnswerScript.id == answer_script_id).first()
    if script is None:
        raise ValueError(f"AnswerScript {answer_script_id} not found")

    evaluation = script.evaluation
    if evaluation is None:
        evaluation = Evaluation(answer_script_id=script.id, status=EvaluationStatus.PENDING)
        db.add(evaluation)
        db.flush()

    try:
        # 1. OCR ---------------------------------------------------------
        evaluation.status = EvaluationStatus.OCR_IN_PROGRESS
        db.commit()

        ocr_result = ocr_service.extract_document(script.file_path)
        evaluation.ocr_raw_text = ocr_result.full_text

        # 2. Fetch questions + model answers for this script's exam ------
        exam = script.examination
        questions: list[Question] = []
        if exam.question_paper_id:
            questions = (
                db.query(Question)
                .filter(Question.question_paper_id == exam.question_paper_id)
                .all()
            )

        # 3. NLP scoring per question -------------------------------------
        evaluation.status = EvaluationStatus.NLP_IN_PROGRESS
        db.commit()

        extracted_answers = []
        total_ai_marks = 0.0
        total_max_marks = 0.0
        confidences = []

        for question in questions:
            model_answer: ModelAnswer | None = question.model_answer
            student_answer_text = ocr_result.question_segments.get(
                question.question_number, ""
            )

            if model_answer is None or not student_answer_text.strip():
                extracted_answers.append(
                    {
                        "question_number": question.question_number,
                        "answer_text": student_answer_text,
                        "semantic_score": 0.0,
                        "keyword_score": 0.0,
                        "ai_marks": 0.0,
                        "max_marks": question.max_marks,
                        "confidence": 0.0,
                        "note": "No model answer configured or no answer detected",
                    }
                )
                total_max_marks += question.max_marks
                continue

            question_score = nlp_service.score_question(
                question_number=question.question_number,
                student_answer=student_answer_text,
                model_answer=model_answer.answer_text,
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

            extracted_answers.append(
                {
                    "question_number": question_score.question_number,
                    "answer_text": student_answer_text,
                    "semantic_score": question_score.semantic_score,
                    "keyword_score": question_score.keyword_score,
                    "ai_marks": question_score.ai_marks,
                    "max_marks": question_score.max_marks,
                    "confidence": confidence,
                    "matched_keywords": question_score.matched_keywords,
                    "missing_keywords": question_score.missing_keywords,
                }
            )
            total_ai_marks += question_score.ai_marks
            total_max_marks += question_score.max_marks

        evaluation.extracted_answers = extracted_answers
        evaluation.total_ai_marks = round(total_ai_marks, 2)
        evaluation.total_max_marks = round(total_max_marks, 2)
        evaluation.confidence_score = (
            round(sum(confidences) / len(confidences), 4) if confidences else 0.0
        )
        evaluation.ai_model_version = AI_MODEL_VERSION
        evaluation.status = EvaluationStatus.AI_EVALUATED
        evaluation.updated_at = datetime.utcnow()

        # Route to teacher review only when the AI is not confident enough
        if ml_service.needs_teacher_review(evaluation.confidence_score or 0.0):
            evaluation.status = EvaluationStatus.UNDER_REVIEW

        db.commit()
        db.refresh(evaluation)
        return evaluation

    except Exception as exc:  # noqa: BLE001
        logger.exception("Evaluation pipeline failed for answer_script_id=%s", answer_script_id)
        evaluation.status = EvaluationStatus.FAILED
        evaluation.error_message = str(exc)
        db.commit()
        raise
