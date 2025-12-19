from functools import cache

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile
from sqlmodel import Session

from app.core.auth import get_current_user_id
from app.core.db import get_db
from app.crud import task_crud
from app.models.task import Task
from app.schemas.task import FileAnalysisRequest, TaskCreate, TaskDraft
from app.services.llm.chrono_agent import ChronoAgent

router = APIRouter(prefix="/tasks", tags=["tasks"])

@cache
def get_chrono_agent() -> ChronoAgent:
    return ChronoAgent()

@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), chrono_agent: ChronoAgent = Depends(get_chrono_agent)) -> list[TaskDraft]:
    allowed_content_types: list[str] = ["image/jpeg", "image/png", "application/pdf"]
    content_type: str | None = file.content_type
    if content_type is None:
        raise HTTPException(status_code=400, detail="No valid file content type")
    if content_type not in allowed_content_types:
        raise HTTPException(status_code=400, detail="Invalid file content type")
    file_content: bytes = await file.read()
    file_request: FileAnalysisRequest = FileAnalysisRequest(file_content=file_content, content_type=content_type)
    return await chrono_agent.analyze_tasks_from_file(file_request)

@router.post("/ingest/text")
async def ingest_text(text: str = Body(...), chrono_agent: ChronoAgent = Depends(get_chrono_agent)) -> list[TaskDraft]:
    return await chrono_agent.analyze_tasks_from_text(text)

@router.post("/")
async def create_task(task: TaskCreate = Body(...), user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> Task:
    return task_crud.create_task(task, user_id, session)

@router.post("/bulk")
async def create_tasks(tasks: list[TaskCreate] = Body(...), user_id: int = Depends(get_current_user_id), session: Session = Depends(get_db)) -> list[Task]:
    return task_crud.create_tasks(tasks, user_id, session)
