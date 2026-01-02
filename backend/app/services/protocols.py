"""Protocol definitions for swappable service implementations."""

from typing import Protocol

from app.models.availability import WeeklyAvailability
from app.models.schedule_item import ScheduleItem
from app.models.task import Task
from app.schemas.task import FileAnalysisRequest, TaskDraft
from app.services.scheduling_types import SchedulingConfig, SchedulingResponse


class ChronoAgent(Protocol):
    """Protocol for task analysis services (e.g., LLM-based analyzers)."""

    async def analyze_tasks_from_file(
        self, file_request: FileAnalysisRequest
    ) -> list[TaskDraft]:
        """
        Analyze a file and extract task information.

        Args:
            file_request: The file to analyze with content and metadata

        Returns:
            List of extracted task drafts
        """
        ...

    async def analyze_tasks_from_text(
        self, text: str, language: str
    ) -> list[TaskDraft]:
        """
        Analyze text and extract task information.

        Args:
            text: The text to analyze
            language: The language code for the response

        Returns:
            List of extracted task drafts
        """
        ...


class ChronoScheduler(Protocol):
    """Protocol for task scheduling services."""

    def schedule_tasks(
        self,
        tasks: list[Task],
        schedule_items: list[ScheduleItem],
        availability: WeeklyAvailability,
        config: SchedulingConfig,
    ) -> SchedulingResponse:
        """
        Schedule tasks into available time slots.

        Args:
            tasks: List of tasks to schedule
            schedule_items: Existing schedule items (busy intervals)
            availability: User's weekly availability
            config: Scheduling configuration

        Returns:
            SchedulingResponse with schedule blocks and warnings
        """
        ...
