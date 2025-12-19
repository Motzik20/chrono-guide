from fastapi.testclient import TestClient


def test_health_check(client: TestClient) -> None:
    """Test the health check endpoint returns ok status."""
    response = client.get("/health/")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_health_check_trailing_slash_redirect(client: TestClient) -> None:
    """Test that /health redirects to /health/."""
    response = client.get("/health", follow_redirects=False)
    assert response.status_code == 307  # Temporary redirect


def test_health_check_with_trailing_slash_follows_redirect(client: TestClient) -> None:
    """Test that /health follows redirect to /health/."""
    response = client.get("/health", follow_redirects=True)
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}

