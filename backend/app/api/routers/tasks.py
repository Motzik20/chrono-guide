from functools import cache

from fastapi import APIRouter, Body, Depends, File, HTTPException, UploadFile

from app.schemas.task import FileAnalysisRequest, TaskAnalysisResult
from app.services.llm.chrono_agent import ChronoAgent

router = APIRouter(prefix="/tasks", tags=["tasks"])

@cache
def get_chrono_agent() -> ChronoAgent:
    return ChronoAgent()

@router.post("/ingest/file")
async def ingest_file(file: UploadFile = File(...), chrono_agent: ChronoAgent = Depends(get_chrono_agent)) -> list[TaskAnalysisResult]:
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
async def ingest_text(text: str = Body(...), chrono_agent: ChronoAgent = Depends(get_chrono_agent)) -> list[TaskAnalysisResult]:
    return await chrono_agent.analyze_tasks_from_text(text)
