from datetime import datetime, timezone
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.api.deps import get_db
from app.core.config import settings
from app.main import app
from app.models.user import FreeTimeLevel, User, UserRole
from app.services.google_auth_service import GoogleAuthService


def test_google_auth_service_mock_token():
    payload = GoogleAuthService.verify_id_token("mock-google-token")
    assert payload["email"] == "developer.google@sihijau.id"
    assert payload["google_id"] == "google-mock-sub-123456789"
    assert payload["email_verified"] is True


def test_google_auth_service_invalid_token():
    with pytest.raises(HTTPException):
        # A non-mock malformed token should fail verification
        GoogleAuthService.verify_id_token("invalid-real-token-123")


@pytest.mark.asyncio
async def test_google_auth_dev_mock_endpoint():
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=999,
        email="demo.google@sihijau.id",
        full_name="Demo Google User",
        role=UserRole.USER,
        auth_provider="google",
        google_id="google-dev-1234567890",
        avatar_url="https://lh3.googleusercontent.com/a/default-avatar",
        has_yard=False,
        free_time_level=FreeTimeLevel.LOW,
        created_at=now,
        updated_at=now,
        is_active=True,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/google/dev-mock",
                json={
                    "email": "demo.google@sihijau.id",
                    "full_name": "Demo Google User",
                    "picture": "https://lh3.googleusercontent.com/a/default-avatar",
                    "sub": "google-dev-1234567890",
                },
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["token_type"] == "bearer"
        assert data["user"]["email"] == "demo.google@sihijau.id"
        assert data["user"]["auth_provider"] == "google"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_google_auth_endpoint_with_mock_token():
    now = datetime.now(timezone.utc)
    mock_user = User(
        id=888,
        email="developer.google@sihijau.id",
        full_name="Developer Google",
        role=UserRole.USER,
        auth_provider="google",
        google_id="google-mock-sub-123456789",
        avatar_url="https://lh3.googleusercontent.com/a/default-user",
        has_yard=False,
        free_time_level=FreeTimeLevel.LOW,
        created_at=now,
        updated_at=now,
        is_active=True,
    )

    mock_db = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalars.return_value.first.return_value = mock_user
    mock_db.execute.return_value = mock_result

    app.dependency_overrides[get_db] = lambda: mock_db

    try:
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.post(
                "/api/v1/auth/google",
                json={"id_token": "mock-google-token"},
            )

        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert data["user"]["email"] == "developer.google@sihijau.id"
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.asyncio
async def test_google_auth_url_endpoint():
    with patch.object(settings, "GOOGLE_CLIENT_ID", "test-client-id.apps.googleusercontent.com"):
        async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
            response = await ac.get("/api/v1/auth/google/url")

        assert response.status_code == 200
        data = response.json()
        assert "authorization_url" in data
        assert "accounts.google.com" in data["authorization_url"]
        assert "test-client-id.apps.googleusercontent.com" in data["authorization_url"]
