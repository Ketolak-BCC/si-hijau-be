import logging
import urllib.parse
from typing import Any

import httpx
from fastapi import HTTPException, status
from google.auth.transport import requests as google_requests
from google.oauth2 import id_token

from app.core.config import settings

logger = logging.getLogger(__name__)


class GoogleAuthService:
    @staticmethod
    def verify_id_token(token: str) -> dict[str, Any]:
        """
        Verifies Google ID Token.
        In development mode, supports mock tokens for automated Postman testing.
        In production or with real tokens, cryptographically verifies against Google's public keys.
        """
        # Development mock token support for local testing / Postman without real Google Cloud project
        if settings.ENVIRONMENT == "development" and (
            token == "mock-google-token"
            or token.startswith("dev-token-")
            or token.startswith("mock-")
        ):
            logger.info("Using development mock Google ID token verification.")
            return {
                "google_id": "google-mock-sub-123456789",
                "email": "developer.google@sihijau.id",
                "full_name": "Developer Google",
                "avatar_url": "https://lh3.googleusercontent.com/a/default-user",
                "email_verified": True,
            }

        try:
            # Prepare audience check if GOOGLE_CLIENT_ID is configured
            audience = settings.GOOGLE_CLIENT_ID if settings.GOOGLE_CLIENT_ID else None
            
            request = google_requests.Request()
            payload = id_token.verify_oauth2_token(token, request, audience=audience)

            # Security checks
            issuer = payload.get("iss")
            if issuer not in ("accounts.google.com", "https://accounts.google.com"):
                raise ValueError("Wrong issuer in Google ID token.")

            email = payload.get("email")
            if not email:
                raise ValueError("Email not found in Google ID token.")

            # Best practice: ensure email is verified by Google
            if not payload.get("email_verified", False):
                raise ValueError("Google account email is not verified.")

            return {
                "google_id": str(payload.get("sub")),
                "email": str(email).lower(),
                "full_name": str(payload.get("name") or email.split("@")[0]),
                "avatar_url": payload.get("picture"),
                "email_verified": True,
            }

        except ValueError as err:
            logger.warning(f"Google ID token verification failed: {err}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid Google ID token: {err}",
            ) from err
        except Exception as err:
            logger.error(f"Unexpected error during Google ID token verification: {err}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to verify Google authentication token.",
            ) from err

    @staticmethod
    def get_authorization_url(state: str | None = None) -> str:
        """
        Generates the Google OAuth 2.0 authorization URL for browser redirect flow.
        """
        if not settings.GOOGLE_CLIENT_ID:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GOOGLE_CLIENT_ID is not configured in environment.",
            )

        base_url = "https://accounts.google.com/o/oauth2/v2/auth"
        params = {
            "client_id": settings.GOOGLE_CLIENT_ID,
            "redirect_uri": settings.GOOGLE_REDIRECT_URI,
            "response_type": "code",
            "scope": "openid email profile",
            "access_type": "offline",
            "prompt": "consent",
        }
        if state:
            params["state"] = state

        return f"{base_url}?{urllib.parse.urlencode(params)}"

    @staticmethod
    async def exchange_code_for_tokens(code: str, redirect_uri: str | None = None) -> dict[str, Any]:
        """
        Exchanges Google OAuth authorization code for Google tokens (id_token & access_token).
        """
        if not settings.GOOGLE_CLIENT_ID or not settings.GOOGLE_CLIENT_SECRET:
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="GOOGLE_CLIENT_ID or GOOGLE_CLIENT_SECRET is not configured.",
            )

        token_url = "https://oauth2.googleapis.com/token"
        data = {
            "code": code,
            "client_id": settings.GOOGLE_CLIENT_ID,
            "client_secret": settings.GOOGLE_CLIENT_SECRET,
            "redirect_uri": redirect_uri or settings.GOOGLE_REDIRECT_URI,
            "grant_type": "authorization_code",
        }

        async with httpx.AsyncClient(timeout=10.0) as client:
            try:
                response = await client.post(token_url, data=data)
            except httpx.RequestError as err:
                logger.error(f"Network error exchanging Google code: {err}")
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail="Failed to communicate with Google OAuth server.",
                ) from err

            if response.status_code != 200:
                logger.warning(f"Google token endpoint rejected code: {response.text}")
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail=f"Google code exchange failed: {response.text}",
                )

            return response.json()
