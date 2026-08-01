"""
Celery application instance for background/async work: batch answer-script
evaluation, bulk OCR, report generation, and ML model retraining.
"""
from celery import Celery

from config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "aeval",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["services.celery_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
