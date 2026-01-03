from unittest.mock import MagicMock, patch

from fastapi.testclient import TestClient

from app.schemas.task import TextAnalysisRequest


class TestIngestFile:
    """Tests for POST /tasks/ingest/file endpoint."""

    @patch("app.api.routers.tasks.ingest_file_task")
    def test_ingest_file_success(
        self,
        mock_ingest_task: MagicMock,
        client: TestClient,
        mock_user_id: int,
    ) -> None:
        """Test successful file ingestion returns job ID."""
        # Mock Celery task
        mock_job = MagicMock()
        mock_job.id = "test-job-id-123"
        mock_ingest_task.delay.return_value = mock_job

        file_content = b"fake image content"
        files = {"file": ("test.jpg", file_content, "image/jpeg")}

        response = client.post("/tasks/ingest/file", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == "test-job-id-123"
        assert data["status"] == "processing"
        mock_ingest_task.delay.assert_called_once()

    def test_ingest_file_invalid_content_type(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test file ingestion fails with invalid content type."""
        file_content = b"fake content"
        files = {"file": ("test.txt", file_content, "text/plain")}

        response = client.post("/tasks/ingest/file", files=files)

        assert response.status_code == 400
        assert "Invalid file content type" in response.json()["detail"]

    @patch("app.api.routers.tasks.ingest_file_task")
    def test_ingest_file_png_success(
        self,
        mock_ingest_task: MagicMock,
        client: TestClient,
        mock_user_id: int,
    ) -> None:
        """Test successful PNG file ingestion returns job ID."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id-png"
        mock_ingest_task.delay.return_value = mock_job

        file_content = b"fake png content"
        files = {"file": ("test.png", file_content, "image/png")}

        response = client.post("/tasks/ingest/file", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == "test-job-id-png"

    @patch("app.api.routers.tasks.ingest_file_task")
    def test_ingest_file_pdf_success(
        self,
        mock_ingest_task: MagicMock,
        client: TestClient,
        mock_user_id: int,
    ) -> None:
        """Test successful PDF file ingestion returns job ID."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id-pdf"
        mock_ingest_task.delay.return_value = mock_job

        file_content = b"fake pdf content"
        files = {"file": ("test.pdf", file_content, "application/pdf")}

        response = client.post("/tasks/ingest/file", files=files)

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == "test-job-id-pdf"


class TestIngestText:
    """Tests for POST /tasks/ingest/text endpoint."""

    @patch("app.api.routers.tasks.ingest_text_task")
    def test_ingest_text_success(
        self,
        mock_ingest_task: MagicMock,
        client: TestClient,
        mock_user_id: int,
    ) -> None:
        """Test successful text ingestion returns job ID."""
        mock_job = MagicMock()
        mock_job.id = "test-job-id-text"
        mock_ingest_task.delay.return_value = mock_job

        text_request = TextAnalysisRequest(text="This is a test task description")
        response = client.post("/tasks/ingest/text", json=text_request.model_dump())

        assert response.status_code == 200
        data = response.json()
        assert "job_id" in data
        assert data["job_id"] == "test-job-id-text"
        assert data["status"] == "processing"
        mock_ingest_task.delay.assert_called_once()


class TestCreateTask:
    """Tests for POST /tasks/ endpoint."""

    def test_create_task_success(self, client: TestClient, mock_user_id: int) -> None:
        """Test successful task creation."""
        task_data = {
            "title": "New Task",
            "description": "Task description",
            "expected_duration_minutes": 45,
            "priority": 2,
            "tips": ["Tip 1"],
        }

        response = client.post(
            "/tasks/",
            json=task_data,
        )

        assert response.status_code == 201
        assert response.json()["task_id"] is not None
        assert response.json()["created"] is True

    def test_create_task_with_deadline(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test task creation with deadline."""
        import datetime as dt

        future_date = dt.datetime.now(dt.timezone.utc) + dt.timedelta(days=7)
        task_data = {
            "title": "Task with Deadline",
            "description": "Description",
            "expected_duration_minutes": 30,
            "deadline": future_date.isoformat(),
        }

        response = client.post(
            "/tasks/",
            json=task_data,
        )

        assert response.status_code == 201
        assert response.json()["task_id"] is not None
        assert response.json()["created"] is True

    def test_create_task_invalid_duration(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test task creation fails with invalid duration."""
        task_data = {
            "title": "Task",
            "description": "Description",
            "expected_duration_minutes": 0,  # Invalid: must be > 0
        }

        response = client.post(
            "/tasks/",
            json=task_data,
        )

        assert response.status_code == 422

    def test_create_task_invalid_priority(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test task creation fails with invalid priority."""
        task_data = {
            "title": "Task",
            "description": "Description",
            "expected_duration_minutes": 30,
            "priority": 5,  # Invalid: must be 0-4
        }

        response = client.post(
            "/tasks/",
            json=task_data,
        )

        assert response.status_code == 422


class TestCreateTasksBulk:
    """Tests for POST /tasks/bulk endpoint."""

    def test_create_tasks_bulk_success(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test successful bulk task creation."""
        tasks_data = [
            {
                "title": "Task 1",
                "description": "Description 1",
                "expected_duration_minutes": 30,
            },
            {
                "title": "Task 2",
                "description": "Description 2",
                "expected_duration_minutes": 60,
            },
        ]

        response = client.post(
            "/tasks/bulk",
            json=tasks_data,
        )

        assert response.status_code == 201
        data = response.json()
        assert data["created_count"] == 2
        assert data["task_ids"][0] is not None
        assert data["task_ids"][1] is not None

    def test_create_tasks_bulk_empty_list(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test bulk creation with empty list."""
        response = client.post(
            "/tasks/bulk",
            json=[],
        )

        assert response.status_code == 201
        assert response.json()["created_count"] == 0
        assert response.json()["task_ids"] == []

    def test_create_tasks_bulk_partial_invalid(
        self, client: TestClient, mock_user_id: int
    ) -> None:
        """Test bulk creation fails when one task is invalid."""
        tasks_data = [
            {
                "title": "Valid Task",
                "description": "Description",
                "expected_duration_minutes": 30,
            },
            {
                "title": "Invalid Task",
                "description": "Description",
                "expected_duration_minutes": -1,
            },
        ]

        response = client.post(
            "/tasks/bulk",
            json=tasks_data,
        )

        assert response.status_code == 422
