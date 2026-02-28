from sqlmodel import Session, select

from app.core.exceptions import NotFoundError
from app.models.celery_job import CeleryJob


def create_celery_job(celery_job: CeleryJob, session: Session) -> CeleryJob:
    session.add(celery_job)
    session.commit()
    session.refresh(celery_job)
    return celery_job


def get_celery_job(job_id: str, user_id: int, session: Session) -> CeleryJob:
    job = session.exec(
        select(CeleryJob)
        .where(CeleryJob.id == job_id)
        .where(CeleryJob.user_id == user_id)
    ).first()
    if not job:
        raise NotFoundError(f"Celery job with id {job_id} not found")
    return job
