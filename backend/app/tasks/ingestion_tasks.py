import os
from typing import Any

from celery import Task

from app.celery_app import celery_app
from app.core.db import get_db
from app.crud import task_crud
from app.models.task import Task as TaskModel
from app.schemas.task import (
    FileAnalysisRequest,
    IngestTaskResponse,
    TaskCreate,
    TaskDraft,
)
from app.services.file_storage import storage
from app.services.llm.gemini_agent import GeminiAgent
from app.services.protocols import ChronoAgent


@celery_app.task(bind=True, max_retries=3)
def ingest_file(
    self: Task,  # type: ignore[reportUnknownReturnType]
    file_path: str,
    content_type: str,
    language: str,
    user_id: int,
) -> dict[str, Any]:
    """Ingest a file into the database."""
    chrono_agent: ChronoAgent = GeminiAgent()
    # Manually get session
    session_gen = get_db()
    session = next(session_gen)

    try:
        # File should be available due to fsync in save_upload and countdown delay
        # But check existence as a safety measure
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File {file_path} not found")

        # Read file content
        with open(file_path, "rb") as file:
            file_content = file.read()

        file_request = FileAnalysisRequest(
            file_content=file_content, content_type=content_type, language=language
        )

        task_drafts: list[TaskDraft] = chrono_agent.analyze_tasks_from_file(
            file_request
        )

        if task_drafts:
            tasks_to_create = [
                TaskCreate(
                    title=task_draft.title,
                    description=task_draft.description,
                    expected_duration_minutes=task_draft.expected_duration_minutes,
                    tips=task_draft.tips,
                )
                for task_draft in task_drafts
            ]
            created_tasks: list[TaskModel] = task_crud.create_tasks(
                tasks_to_create, user_id, session
            )
            session.commit()
            return IngestTaskResponse(
                draft_ids=[
                    task_model.id
                    for task_model in created_tasks
                    if task_model.id is not None
                ],
                created_count=len(created_tasks),
            ).model_dump()
        else:
            return IngestTaskResponse(
                draft_ids=[],
                created_count=0,
            ).model_dump()

    except (ValueError, FileNotFoundError) as exc:
        session.rollback()
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()
        # Only delete if file exists
        if os.path.exists(file_path):
            storage.delete(file_path)


@celery_app.task(bind=True, max_retries=3)
def ingest_text(
    self: Task,  # type: ignore[reportUnknownReturnType]
    text: str,
    language: str,
    user_id: int,
) -> dict[str, Any]:
    """Ingest text into the database."""
    chrono_agent: ChronoAgent = GeminiAgent()
    session_gen = get_db()
    session = next(session_gen)

    try:
        task_drafts: list[TaskDraft] = chrono_agent.analyze_tasks_from_text(
            text, language
        )

        if task_drafts:
            tasks_to_create = [
                TaskCreate(
                    title=task_draft.title,
                    description=task_draft.description,
                    expected_duration_minutes=task_draft.expected_duration_minutes,
                    tips=task_draft.tips,
                )
                for task_draft in task_drafts
            ]
            created_tasks: list[TaskModel] = task_crud.create_tasks(
                tasks_to_create, user_id, session
            )
            session.commit()
            return IngestTaskResponse(
                draft_ids=[
                    task_model.id
                    for task_model in created_tasks
                    if task_model.id is not None
                ],
                created_count=len(created_tasks),
            ).model_dump()
        else:
            return IngestTaskResponse(
                draft_ids=[],
                created_count=0,
            ).model_dump()

    except ValueError as exc:
        session.rollback()
        raise self.retry(exc=exc, countdown=5)
    finally:
        session.close()
