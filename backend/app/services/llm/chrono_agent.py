import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentResponse, Part

from app.schemas.task import FileAnalysisRequest, TaskAnalysisResult


class ChronoAgent:
    client: genai.Client

    def __init__(self) -> None:
        load_dotenv()
        api_key: str | None = os.getenv("GEMINI_API_KEY")
        if api_key is None:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=api_key)

    async def analyze_tasks_from_file(
        self, file_request: FileAnalysisRequest
    ) -> list[TaskAnalysisResult]:
        prompt: str = "From the file, identify and list all tasks. For each task, include: Concise Title, Description, Estimated Duration, and 2-4 actionable Tips derived from the visual context."

        contents_parts: list[Part] = [
            Part(
                inline_data={  # type: ignore[arg-type]
                    "mime_type": file_request.content_type,
                    "data": file_request.file_content,
                }
            ),
            Part(text=prompt),
        ]

        response: GenerateContentResponse = await self.client.aio.models.generate_content( #type: ignore[arg-type]
            model="gemini-2.5-flash",
            contents=contents_parts,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[TaskAnalysisResult],
            },
        )
        if response.text is None:
            return []
        json_task_list: list[dict[str, Any]] = json.loads(response.text)
        analyzed_tasks = [
            TaskAnalysisResult.model_validate(task_data) for task_data in json_task_list
        ]
        return analyzed_tasks

    async def analyze_tasks_from_text(self, text: str) -> list[TaskAnalysisResult]:
        prompt: str = "From the text, identify and list all tasks. For each task, include: Concise Title, Description, Estimated Duration, and 2-4 actionable Tips derived from the text."

        contents_parts: list[Part] = [
            Part(text=text),
            Part(text=prompt),
        ]

        response: GenerateContentResponse = await self.client.aio.models.generate_content( #type: ignore[arg-type]
            model="gemini-2.5-flash",
            contents=contents_parts,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[TaskAnalysisResult],
            },
        )
        if response.text is None:
            return []
        json_task_list: list[dict[str, Any]] = json.loads(response.text)
        analyzed_tasks = [
            TaskAnalysisResult.model_validate(task_data) for task_data in json_task_list
        ]
        return analyzed_tasks
