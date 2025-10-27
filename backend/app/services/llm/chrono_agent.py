import json
import os

from dotenv import load_dotenv
from google import genai
from google.genai.types import Part

from app.schemas.task import TaskAnalysisResult, TaskImageAnalysisRequest


class ChronoAgent:
    client: genai.Client

    def __init__(self):
        load_dotenv()
        self.client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

    async def generate_tasks_from_image(
        self, image_request: TaskImageAnalysisRequest
    ) -> list[TaskAnalysisResult]:
        prompt: str = "From the image, identify and list all tasks. For each task, include: Concise Title, Description, Estimated Duration, and 2-4 actionable Tips derived from the visual context."

        contents_parts = [
            Part(
                inline_data={
                    "mime_type": "image/png",
                    "data": image_request.image_description,
                }
            ),
            Part(text=prompt),
        ]

        response = await self.client.aio.models.generate_content(
            model="gemini-2.0-flash",
            contents=contents_parts,
            config={
                "response_mime_type": "application/json",
                "response_schema": list[TaskAnalysisResult],
            },
        )
        json_task_list = json.loads(response.text)
        analyzed_tasks = [
            TaskAnalysisResult.model_validate(task_data) for task_data in json_task_list
        ]
        return analyzed_tasks
