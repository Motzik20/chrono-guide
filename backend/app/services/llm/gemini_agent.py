import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentResponse, Part

from app.schemas.task import FileAnalysisRequest, TaskDraft


class GeminiAgent:
    """
    Google Gemini-based implementation of TaskAnalyzer protocol.

    This class implements the TaskAnalyzer protocol by providing:
    - analyze_tasks_from_file: Extracts tasks from uploaded files
    - analyze_tasks_from_text: Extracts tasks from text input
    """

    client: genai.Client

    def __init__(self) -> None:
        load_dotenv()
        api_key: str | None = os.getenv("GEMINI_API_KEY")
        if api_key is None:
            raise ValueError("GEMINI_API_KEY is not set")
        self.client = genai.Client(api_key=api_key)

    def analyze_tasks_from_file(
        self, file_request: FileAnalysisRequest
    ) -> list[TaskDraft]:
        prompt: str = f"From the file, identify and list all tasks. For each task, include: Concise Title, Description, Expected Duration (in minutes), and 2-4 actionable Tips derived from the visual context. Respond in {file_request.language}."

        contents_parts: list[Part] = [
            Part(
                inline_data={  # type: ignore[arg-type]
                    "mime_type": file_request.content_type,
                    "data": file_request.file_content,
                }
            ),
            Part(text=prompt),
        ]

        response: GenerateContentResponse = self.client.models.generate_content(  # type: ignore[arg-type]
            model="gemini-2.5-flash",
            contents=contents_parts,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[TaskDraft],
            },
        )
        if response.text is None:
            return []
        json_task_list: list[dict[str, Any]] = json.loads(response.text)
        analyzed_tasks = [
            TaskDraft.model_validate(task_data) for task_data in json_task_list
        ]
        return analyzed_tasks

    def analyze_tasks_from_text(self, text: str, language: str) -> list[TaskDraft]:
        prompt: str = f"From the text, identify and list all tasks. For each task, include: Concise Title, Description, Estimated Duration, and 2-4 actionable Tips derived from the text. Respond in {language}."

        contents_parts: list[Part] = [
            Part(text=text),
            Part(text=prompt),
        ]

        response: GenerateContentResponse = self.client.models.generate_content(  # type: ignore[arg-type]
            model="gemini-2.5-flash",
            contents=contents_parts,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[TaskDraft],
            },
        )
        if response.text is None:
            return []
        json_task_list: list[dict[str, Any]] = json.loads(response.text)
        analyzed_tasks = [
            TaskDraft.model_validate(task_data) for task_data in json_task_list
        ]
        return analyzed_tasks
