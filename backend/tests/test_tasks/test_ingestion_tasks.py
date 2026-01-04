from unittest.mock import MagicMock, Mock, patch

import pytest
from celery.exceptions import MaxRetriesExceededError
from sqlmodel import Session

from app.models.temp_upload import TempUpload
from app.models.user import User
from app.schemas.task import TaskDraft
from app.tasks.ingestion_tasks import ingest_file, ingest_text


class TestIngestFile:
    """Tests for ingest_file Celery task."""

    @patch("app.tasks.ingestion_tasks.temp_upload_crud")
    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_file_success(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        mock_temp_upload_crud: MagicMock,
        session: Session,
        user: User,
        mock_task_drafts: list[TaskDraft],
    ) -> None:
        """Test successful file ingestion."""
        # Setup mocks
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_file.return_value = mock_task_drafts
        mock_gemini_agent.return_value = mock_agent
        mock_temp_upload_crud.get_upload_record.return_value = TempUpload(
            id=1,
            filename="test.jpg",
            data=b"fake image content",
        )

        # Save original retry method
        original_retry = ingest_file.retry

        try:
            # Patch retry on the task instance to prevent retries on success
            ingest_file.retry = Mock(
                side_effect=Exception("Should not retry on success")
            )

            # Call the task function directly using .run() to bypass Celery wrapper
            result = ingest_file.run(
                upload_id=1,
                content_type="image/jpeg",
                language="en",
                user_id=user.id,  # type: ignore[attr-defined]
            )

            # Verify results
            assert result["created_count"] == 2
            assert len(result["draft_ids"]) == 2
            assert result["draft_ids"][0] is not None
            assert result["draft_ids"][1] is not None

            # Verify agent was called correctly
            mock_agent.analyze_tasks_from_file.assert_called_once()
            call_args = mock_agent.analyze_tasks_from_file.call_args[0][0]
            assert call_args.file_content == b"fake image content"
            assert call_args.content_type == "image/jpeg"
            assert call_args.language == "en"

            # Verify file was deleted
            mock_temp_upload_crud.delete_upload_record.assert_called_once_with(
                TempUpload(id=1, filename="test.jpg", data=b"fake image content"),
                session,
            )

        finally:
            # Restore original retry method
            ingest_file.retry = original_retry

    @patch("app.tasks.ingestion_tasks.temp_upload_crud")
    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_file_empty_result(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        mock_temp_upload_crud: MagicMock,
        session: Session,
        user: User,
    ) -> None:
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_file.return_value = []
        mock_gemini_agent.return_value = mock_agent
        mock_temp_upload_crud.get_upload_record.return_value = TempUpload(
            id=1,
            filename="test.jpg",
            data=b"fake image content",
        )

        # Save original retry method
        original_retry = ingest_file.retry

        try:
            ingest_file.retry = Mock(
                side_effect=Exception("Should not retry on success")
            )

            result = ingest_file.run(
                upload_id=1,
                content_type="image/jpeg",
                language="en",
                user_id=user.id,  # type: ignore[attr-defined]
            )

            assert result["created_count"] == 0
            assert len(result["draft_ids"]) == 0
            assert result["draft_ids"] == []

            mock_agent.analyze_tasks_from_file.assert_called_once()
            call_args = mock_agent.analyze_tasks_from_file.call_args[0][0]
            assert call_args.file_content == b"fake image content"
            assert call_args.content_type == "image/jpeg"
            assert call_args.language == "en"

            mock_temp_upload_crud.delete_upload_record.assert_called_once_with(
                TempUpload(id=1, filename="test.jpg", data=b"fake image content"),
                session,
            )

        finally:
            # Restore original retry method
            ingest_file.retry = original_retry

    @patch("app.tasks.ingestion_tasks.temp_upload_crud")
    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_file_value_error_retry(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        mock_temp_upload_crud: MagicMock,
        session: Session,
        user: User,
    ) -> None:
        """Test file ingestion retries on ValueError."""
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_file.side_effect = ValueError(
            "Invalid file format"
        )
        mock_gemini_agent.return_value = mock_agent

        mock_temp_upload_crud.get_upload_record.return_value = TempUpload(
            id=1,
            filename="test.jpg",
            data=b"fake image content",
        )

        # Save original retry method
        original_retry = ingest_file.retry

        try:
            # Patch retry to raise exception when called
            ingest_file.retry = Mock(side_effect=MaxRetriesExceededError)
            with pytest.raises(ValueError):
                ingest_file.run(
                    upload_id=1,
                    content_type="image/jpeg",
                    language="en",
                    user_id=user.id,  # type: ignore[attr-defined]
                )

            mock_temp_upload_crud.delete_upload_record.assert_called_once_with(
                TempUpload(id=1, filename="test.jpg", data=b"fake image content"),
                session,
            )
        finally:
            # Restore original retry method
            ingest_file.retry = original_retry

    @patch("app.tasks.ingestion_tasks.temp_upload_crud")
    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_file_deletes_file_on_success(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        mock_temp_upload_crud: MagicMock,
        session: Session,
        user: User,
        mock_task_drafts: list[TaskDraft],
    ) -> None:
        """Test that file is deleted after successful ingestion."""
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_file.return_value = mock_task_drafts
        mock_gemini_agent.return_value = mock_agent

        mock_temp_upload_crud.get_upload_record.return_value = TempUpload(
            id=1,
            filename="test.jpg",
            data=b"fake image content",
        )

        # Save original retry method
        original_retry = ingest_file.retry

        try:
            # Patch retry to prevent retries on success
            ingest_file.retry = Mock(side_effect=Exception("Should not retry"))

            ingest_file.run(
                upload_id=1,
                content_type="image/jpeg",
                language="en",
                user_id=user.id,  # type: ignore[attr-defined]
            )

            # Verify storage.delete was called
            mock_temp_upload_crud.delete_upload_record.assert_called_once_with(
                TempUpload(id=1, filename="test.jpg", data=b"fake image content"),
                session,
            )
        finally:
            # Restore original retry method
            ingest_file.retry = original_retry


class TestIngestText:
    """Tests for ingest_text Celery task."""

    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_text_success(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        session: Session,
        user: User,
        mock_task_drafts: list[TaskDraft],
    ) -> None:
        """Test successful text ingestion."""
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_text.return_value = mock_task_drafts
        mock_gemini_agent.return_value = mock_agent

        # Save original retry method
        original_retry = ingest_text.retry

        try:
            # Patch retry to prevent retries on success
            ingest_text.retry = Mock(
                side_effect=Exception("Should not retry on success")
            )

            result = ingest_text.run(
                text="This is a test task description",
                language="en",
                user_id=user.id,  # type: ignore[attr-defined]
            )

            assert result["created_count"] == 2
            assert len(result["draft_ids"]) == 2  # type: ignore[arg-type]

            # Verify agent was called correctly
            mock_agent.analyze_tasks_from_text.assert_called_once_with(
                "This is a test task description", "en"
            )
        finally:
            # Restore original retry method
            ingest_text.retry = original_retry

    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_text_empty_result(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        session: Session,
        user: User,
    ) -> None:
        """Test text ingestion with no tasks found."""
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_text.return_value = []
        mock_gemini_agent.return_value = mock_agent

        # Save original retry method
        original_retry = ingest_text.retry

        try:
            # Patch retry to prevent retries on success
            ingest_text.retry = Mock(side_effect=Exception("Should not retry"))

            result = ingest_text.run(
                text="No tasks here",
                language="en",
                user_id=user.id,  # type: ignore[attr-defined]
            )

            assert result["created_count"] == 0
            assert result["draft_ids"] == []
        finally:
            # Restore original retry method
            ingest_text.retry = original_retry

    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_text_value_error_retry(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        session: Session,
        user: User,
    ) -> None:
        """Test text ingestion retries on ValueError."""
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_text.side_effect = ValueError(
            "Invalid text format"
        )
        mock_gemini_agent.return_value = mock_agent

        # Save original retry method
        original_retry = ingest_text.retry

        try:
            # Patch retry to raise exception when called
            ingest_text.retry = Mock(side_effect=Exception("Retry called"))

            with pytest.raises(Exception, match="Retry called"):
                ingest_text.run(
                    text="Invalid text",
                    language="en",
                    user_id=user.id,  # type: ignore[attr-defined]
                )

        finally:
            # Restore original retry method
            ingest_text.retry = original_retry

    @patch("app.tasks.ingestion_tasks.GeminiAgent")
    @patch("app.tasks.ingestion_tasks.get_db")
    def test_ingest_text_different_language(
        self,
        mock_get_db: MagicMock,
        mock_gemini_agent: MagicMock,
        session: Session,
        user: User,
        mock_task_drafts: list[TaskDraft],
    ) -> None:
        """Test text ingestion with different language."""
        mock_get_db.return_value = iter([session])
        mock_agent = MagicMock()
        mock_agent.analyze_tasks_from_text.return_value = mock_task_drafts
        mock_gemini_agent.return_value = mock_agent

        # Save original retry method
        original_retry = ingest_text.retry

        try:
            # Patch retry to prevent retries on success
            ingest_text.retry = Mock(side_effect=Exception("Should not retry"))

            result = ingest_text.run(
                text="Teste em português",
                language="pt",
                user_id=user.id,  # type: ignore[attr-defined]
            )

            assert result["created_count"] == 2
            mock_agent.analyze_tasks_from_text.assert_called_once_with(
                "Teste em português", "pt"
            )
        finally:
            # Restore original retry method
            ingest_text.retry = original_retry
