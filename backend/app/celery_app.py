import os

from celery import Celery

redis_url = os.getenv("REDIS_URL", "redis://localhost:6379/0")

celery_app: Celery = Celery(
    "chrono_guide",
    broker=redis_url,
    backend=redis_url,
    include=["app.tasks.ingestion_tasks", "app.tasks.periodic_sync"],
)

celery_app.conf.beat_schedule = {
    "periodic-sync-every-15-minutes": {
        "task": "app.tasks.periodic_sync.periodic_sync",
        "schedule": 900.0,  # every 15 minutes
    },
}

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
)
