import json
import os
from typing import Any

from dotenv import load_dotenv
from google import genai
from google.genai.types import GenerateContentResponse, Part

from app.schemas.task import TaskAnalysisResult, TaskImageAnalysisRequest


class ChronoAgent:
    client: genai.Client

    def __init__(self) -> None:
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    async def generate_tasks_from_image(
        self, image_request: TaskImageAnalysisRequest
    ) -> list[TaskAnalysisResult]:
        prompt: str = "From the image, identify and list all tasks. For each task, include: Concise Title, Description, Estimated Duration, and 2-4 actionable Tips derived from the visual context."

        contents_parts: list[Part] = [
            Part(
                inline_data={  # type: ignore[arg-type]
                    "mime_type": "image/png",
                    "data": image_request.image_description,
                }
            ),
            Part(text=prompt),
        ]

        response: GenerateContentResponse = await self.client.aio.models.generate_content( #type: ignore[arg-type]
            model="gemini-2.0-flash",
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
