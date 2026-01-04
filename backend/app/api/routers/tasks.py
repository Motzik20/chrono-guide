from typing import Any

from celery.result import AsyncResult
from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.celery_app import celery_app
from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.crud import task_crud, temp_upload_crud
from app.crud.setting_crud import get_user_setting, get_user_timezone
from app.models.task import Task
from app.models.temp_upload import TempUpload
from app.schemas.job import IngestTaskJob, JobStatus
from app.schemas.task import (
    IngestTaskResponse,
    JobResponse,
    TaskCreate,
    TaskCreateResponse,
    TaskRead,
    TasksCreateResponse,
    TasksDelete,
    TaskUpdate,
    TextAnalysisRequest,
)
from app.tasks.ingestion_tasks import ingest_file as ingest_file_task
from app.tasks.ingestion_tasks import ingest_text as ingest_text_task

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> JobResponse:
    assert user_id
    allowed_content_types: list[str] = ["image/jpeg", "image/png", "application/pdf"]
    content_type: str | None = file.content_type
    if content_type is None:
        raise HTTPException(status_code=400, detail="No valid file content type")
    if content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Invalid file content type")

    upload_record = temp_upload_crud.create_upload_record(
        TempUpload(filename=file.filename, data=await file.read()), session
    )
    # Commit here to avoid race condition with celery task
    session.commit()

    language: str = get_user_setting(user_id, "language", session).value

    job = ingest_file_task.delay(
        upload_id=upload_record.id,
        content_type=content_type,
        language=language,
        user_id=user_id,
    )

    return JobResponse(job_id=str(job.id))


@router.post("/ingest/text")
async def ingest_text(
    text_request: TextAnalysisRequest = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> JobResponse:
    assert user_id
    language: str = get_user_setting(user_id, "language", session).value

    job = ingest_text_task.delay(
        text=text_request.text, language=language, user_id=user_id
    )

    return JobResponse(job_id=str(job.id))


@router.post("/", status_code=status.HTTP_201_CREATED)
async def create_task(
    task: TaskCreate = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> TaskCreateResponse:
    created_task: Task = task_crud.create_task(task, user_id, session)
    if created_task.id is None:
        raise HTTPException(status_code=500, detail="Failed to create task")
    return TaskCreateResponse(task_id=created_task.id, created=True)


@router.post("/bulk", status_code=status.HTTP_201_CREATED)
async def create_tasks(
    tasks: list[TaskCreate] = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> TasksCreateResponse:
    created_tasks: list[Task] = task_crud.create_tasks(tasks, user_id, session)
    if len(created_tasks) != len(tasks):
        raise HTTPException(status_code=500, detail="Failed to create tasks")
    return TasksCreateResponse(
        task_ids=[task.id for task in created_tasks if task.id is not None],
        created_count=len(created_tasks),
    )


@router.get("/unscheduled", status_code=status.HTTP_200_OK)
async def get_unscheduled_tasks(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> list[TaskRead]:
    user_timezone: str = get_user_timezone(user_id, session)
    return [
        TaskRead.from_model(task, user_timezone)
        for task in task_crud.get_unscheduled_tasks(user_id, session)
    ]


@router.get("/scheduled", status_code=status.HTTP_200_OK)
async def get_scheduled_tasks(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> list[TaskRead]:
    user_timezone: str = get_user_timezone(user_id, session)
    return [
        TaskRead.from_model(task, user_timezone)
        for task in task_crud.get_scheduled_tasks(user_id, session)
    ]


@router.get("/completed", status_code=status.HTTP_200_OK)
async def get_completed_tasks(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> list[TaskRead]:
    user_timezone: str = get_user_timezone(user_id, session)
    return [
        TaskRead.from_model(task, user_timezone)
        for task in task_crud.get_completed_tasks(user_id, session)
    ]


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tasks(
    task_ids: list[int] = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> None:
    task_crud.delete_tasks(TasksDelete(task_ids=task_ids), user_id, session)


@router.get("/drafts", status_code=status.HTTP_200_OK)
async def get_drafts(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> list[TaskRead]:
    user_timezone: str = get_user_timezone(user_id, session)
    return [
        TaskRead.from_model(task, user_timezone)
        for task in task_crud.get_drafts(user_id, session)
    ]


@router.post("/drafts/commit", status_code=status.HTTP_200_OK)
async def commit_drafts(
    task_ids: list[int] = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> TasksCreateResponse:
    tasks = task_crud.commit_drafts(task_ids, user_id, session)
    session.commit()
    return TasksCreateResponse(
        task_ids=[t.id for t in tasks if t.id],
        created_count=len(tasks),
    )


@router.put("/{task_id}", status_code=status.HTTP_200_OK)
async def update_task(
    task_id: int,
    task_update: TaskUpdate = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> TaskRead:
    user_timezone: str = get_user_timezone(user_id, session)
    updated_task = task_crud.update_task(task_id, task_update, user_id, session)
    session.commit()
    return TaskRead.from_model(updated_task, user_timezone)


@router.get("/jobs/{job_id}", status_code=status.HTTP_200_OK)
async def get_job_status(
    job_id: str,
    _user_id: int = Depends(get_current_user_id),
) -> IngestTaskJob:
    """Get the status of a Celery job."""
    task_result: AsyncResult[dict[str, Any]] = AsyncResult(job_id, app=celery_app)

    # Map Celery states to our JobStatus enum
    celery_state = task_result.state
    if celery_state == "PENDING":
        status_enum = JobStatus.PENDING
    elif celery_state in ("STARTED", "RETRY"):
        status_enum = JobStatus.RUNNING
    elif celery_state == "SUCCESS":
        status_enum = JobStatus.SUCCESS
    elif celery_state in ("FAILURE", "REVOKED"):
        status_enum = JobStatus.FAILED
    else:
        status_enum = JobStatus.PENDING

    result: IngestTaskResponse | None = None
    error: str | None = None

    if status_enum == JobStatus.SUCCESS:
        task_result_value = task_result.result
        if isinstance(task_result_value, dict):
            try:
                result = IngestTaskResponse.model_validate(task_result_value)
            except Exception:
                result = None
    elif status_enum == JobStatus.FAILED:
        error = str(task_result.info) if task_result.info else "Task failed"

    return IngestTaskJob(
        id=job_id,
        status=status_enum,
        result=result,
        error=error,
    )


@router.get("/jobs", status_code=status.HTTP_200_OK)
async def get_active_jobs(
    _user_id: int = Depends(get_current_user_id),
) -> dict[str, Any]:
    """Get information about active Celery tasks (monitoring endpoint)."""
    inspect = celery_app.control.inspect()

    active = inspect.active() or {}
    scheduled = inspect.scheduled() or {}
    reserved = inspect.reserved() or {}

    return {
        "active": active,
        "scheduled": scheduled,
        "reserved": reserved,
        "stats": inspect.stats() or {},
    }
