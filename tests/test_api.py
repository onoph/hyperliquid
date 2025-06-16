"""Tests for the Hyperliquid Observer REST API."""

import os
import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch, MagicMock

from main_api import app
from src.api.service import observer_service


@pytest.fixture
def client() -> TestClient:
    """Create a test client for the API."""
    return TestClient(app)


@pytest.fixture
def auth_headers() -> dict[str, str]:
    """Create basic auth headers for testing."""
    import base64
    credentials = base64.b64encode(b"testuser:testpass").decode("utf-8")
    return {"Authorization": f"Basic {credentials}"}


@pytest.fixture(autouse=True)
def mock_env_vars():
    """Mock environment variables for testing."""
    with patch.dict(os.environ, {
        "API_USERNAME": "testuser",
        "API_PASSWORD": "testpass"
    }):
        yield


@pytest.fixture(autouse=True)
def clean_observer_service():
    """Clean observer service before and after each test."""
    observer_service.stop_all_observers()
    observer_service._observers.clear()
    yield
    observer_service.stop_all_observers()
    observer_service._observers.clear()


class TestHealthEndpoint:
    """Test the health endpoint."""

    def test_health_check_no_auth_required(self, client: TestClient) -> None:
        """Test that health check doesn't require authentication."""
        response = client.get("/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "active_observers" in data

    def test_health_check_returns_observer_count(self, client: TestClient) -> None:
        """Test that health check returns correct observer count."""
        response = client.get("/health")
        data = response.json()
        
        # Should start with 0 observers
        assert data["active_observers"] == 0


class TestAuthentication:
    """Test authentication requirements."""

    def test_protected_endpoint_requires_auth(self, client: TestClient) -> None:
        """Test that protected endpoints require authentication."""
        response = client.get("/observers")
        assert response.status_code == 401

    def test_invalid_credentials_rejected(self, client: TestClient) -> None:
        """Test that invalid credentials are rejected."""
        import base64
        bad_credentials = base64.b64encode(b"wrong:wrong").decode("utf-8")
        headers = {"Authorization": f"Basic {bad_credentials}"}
        
        response = client.get("/observers", headers=headers)
        assert response.status_code == 401

    def test_valid_credentials_accepted(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test that valid credentials are accepted."""
        response = client.get("/observers", headers=auth_headers)
        assert response.status_code == 200


class TestObserverEndpoints:
    """Test observer management endpoints."""

    @patch('src.api.service.HyperliquidObserver')
    @patch('src.api.service.Algo')
    def test_start_observer_success(
        self, 
        mock_algo: MagicMock, 
        mock_observer: MagicMock,
        client: TestClient, 
        auth_headers: dict[str, str]
    ) -> None:
        """Test starting an observer successfully."""
        # Mock the observer and algo
        mock_observer_instance = MagicMock()
        mock_observer.return_value = mock_observer_instance
        mock_algo_instance = MagicMock()
        mock_algo.return_value = mock_algo_instance
        
        response = client.post(
            "/observers/start",
            json={"address": "0x1234567890abcdef", "algo_type": "default"},
            headers=auth_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "observer_id" in data
        assert "0x1234567890abcdef" in data["message"]

    def test_start_observer_invalid_request(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test starting observer with invalid request data."""
        response = client.post(
            "/observers/start",
            json={"invalid": "data"},
            headers=auth_headers
        )
        
        assert response.status_code == 422

    def test_list_observers_empty(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test listing observers when none are running."""
        response = client.get("/observers", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        assert len(data) == 0

    def test_get_observer_status_not_found(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test getting status of non-existent observer."""
        response = client.get("/observers/nonexistent/status", headers=auth_headers)
        assert response.status_code == 404

    def test_stop_observer_not_found(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test stopping non-existent observer."""
        response = client.post("/observers/nonexistent/stop", headers=auth_headers)
        assert response.status_code == 404

    def test_stop_all_observers(self, client: TestClient, auth_headers: dict[str, str]) -> None:
        """Test stopping all observers."""
        response = client.post("/observers/stop-all", headers=auth_headers)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_missing_env_vars(self, client: TestClient) -> None:
        """Test behavior when environment variables are missing."""
        with patch.dict(os.environ, {}, clear=True):
            response = client.get("/observers", headers={"Authorization": "Basic dGVzdDp0ZXN0"})
            assert response.status_code == 500 