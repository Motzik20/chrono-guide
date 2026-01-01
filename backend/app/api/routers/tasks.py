from functools import cache

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile, status
from sqlmodel import Session

from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.crud import task_crud
from app.models.task import Task
from app.schemas.task import (
    FileAnalysisRequest,
    TaskCreate,
    TaskCreateResponse,
    TaskDraft,
    TaskRead,
    TasksCreateResponse,
    TasksDelete,
    TextAnalysisRequest,
)
from app.services.llm.chrono_agent import ChronoAgent

router = APIRouter(prefix="/tasks", tags=["tasks"])


@cache
def get_chrono_agent() -> ChronoAgent:
    return ChronoAgent()


@router.post("/ingest/file")
async def ingest_file(
    file: UploadFile = File(...),
    chrono_agent: ChronoAgent = Depends(get_chrono_agent),
    user_id: int = Depends(get_current_user_id),
) -> list[TaskDraft]:
    assert user_id
    allowed_content_types: list[str] = ["image/jpeg", "image/png", "application/pdf"]
    content_type: str | None = file.content_type
    if content_type is None:
        raise HTTPException(status_code=400, detail="No valid file content type")
    if content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Invalid file content type")
    file_content: bytes = await file.read()
    file_request: FileAnalysisRequest = FileAnalysisRequest(
        file_content=file_content, content_type=content_type
    )
    return await chrono_agent.analyze_tasks_from_file(file_request)


@router.post("/ingest/text")
async def ingest_text(
    text_request: TextAnalysisRequest = Body(...),
    chrono_agent: ChronoAgent = Depends(get_chrono_agent),
    user_id: int = Depends(get_current_user_id),
) -> list[TaskDraft]:
    assert user_id
    return await chrono_agent.analyze_tasks_from_text(text_request.text)


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
    return [
        TaskRead.model_validate(task)
        for task in task_crud.get_unscheduled_tasks(user_id, session)
    ]


@router.get("/scheduled", status_code=status.HTTP_200_OK)
async def get_scheduled_tasks(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> list[TaskRead]:
    return [
        TaskRead.model_validate(task)
        for task in task_crud.get_scheduled_tasks(user_id, session)
    ]


@router.get("/completed", status_code=status.HTTP_200_OK)
async def get_completed_tasks(
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> list[TaskRead]:
    return [
        TaskRead.model_validate(task)
        for task in task_crud.get_completed_tasks(user_id, session)
    ]


@router.delete("/bulk", status_code=status.HTTP_204_NO_CONTENT)
async def delete_tasks(
    task_ids: list[int] = Body(...),
    user_id: int = Depends(get_current_user_id),
    session: Session = Depends(get_db),
) -> None:
    task_crud.delete_tasks(TasksDelete(task_ids=task_ids), user_id, session)
