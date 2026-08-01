"""
Celery tasks. Each task opens its own short-lived DB session since Celery
workers are separate processes from the FastAPI app.
"""
import logging

from database.session import SessionLocal
from services.celery_app import celery_app
from services.evaluation_pipeline import run_pipeline

logger = logging.getLogger(__name__)


@celery_app.task(name="evaluate_answer_script", bind=True, max_retries=2)
def evaluate_answer_script_task(self, answer_script_id: int):
    db = SessionLocal()
    try:
        evaluation = run_pipeline(db, answer_script_id)
        return {"evaluation_id": evaluation.id, "status": evaluation.status.value}
    except Exception as exc:  # noqa: BLE001
        logger.exception("Task failed for answer_script_id=%s", answer_script_id)
        raise self.retry(exc=exc, countdown=30)
    finally:
        db.close()


@celery_app.task(name="evaluate_batch")
def evaluate_batch_task(answer_script_ids: list[int]):
    results = []
    for script_id in answer_script_ids:
        results.append(evaluate_answer_script_task.delay(script_id).id)
    return {"queued_task_ids": results, "count": len(results)}
