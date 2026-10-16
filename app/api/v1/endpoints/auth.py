from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.security import OAuth2PasswordRequestForm
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.core.security import create_access_token, get_password_hash, verify_password
from app.models.user import FreeTimeLevel, User, UserRole
from app.schemas.auth import (
    GoogleAuthRequest,
    GoogleAuthUrlResponse,
    GoogleDevLoginRequest,
)
from app.schemas.token import Token
from app.schemas.user import UserCreate, UserResponse
from app.services.google_auth_service import GoogleAuthService

router = APIRouter()


async def _process_google_user(db: AsyncSession, payload: dict) -> User:
    """
    Syncs or creates a user account from verified Google credentials.
    Supports linking existing email accounts with Google OAuth.
    """
    google_id = payload.get("google_id")
    email = payload.get("email")
    full_name = payload.get("full_name") or (email.split("@")[0] if email else "Google User")
    avatar_url = payload.get("avatar_url")

    # 1. Check if user exists by google_id
    user = None
    if google_id:
        result = await db.execute(select(User).where(User.google_id == google_id))
        user = result.scalars().first()

    # 2. If not found by google_id, check if existing account exists by email
    if not user and email:
        result = await db.execute(select(User).where(User.email == email))
        user = result.scalars().first()
        if user:
            # Link google_id and avatar if not present
            user.google_id = google_id
            if not user.avatar_url and avatar_url:
                user.avatar_url = avatar_url
            await db.commit()
            await db.refresh(user)

    # 3. If account does not exist, auto-provision new user
    if not user:
        user = User(
            email=email,
            full_name=full_name,
            google_id=google_id,
            avatar_url=avatar_url,
            auth_provider="google",
            role=UserRole.USER,
            has_yard=False,
            free_time_level=FreeTimeLevel.LOW,
            hashed_password=None,
            is_active=True,
        )
        db.add(user)
        await db.commit()
        await db.refresh(user)

    # 4. Check if user is active
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user account. Please contact support.",
        )

    return user


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(user_in: UserCreate, db: Annotated[AsyncSession, Depends(get_db)]):
    existing = await db.execute(select(User).where(User.email == user_in.email))
    if existing.scalars().first():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="The user with this email already exists in the system.",
        )

    user = User(
        email=user_in.email,
        hashed_password=get_password_hash(user_in.password),
        full_name=user_in.full_name,
        role=UserRole.USER,
        auth_provider="local",
        avatar_url=user_in.avatar_url,
        has_yard=user_in.has_yard,
        free_time_level=user_in.free_time_level,
    )
    db.add(user)
    await db.commit()
    await db.refresh(user)
    return user


@router.post("/login", response_model=Token)
async def login(
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
    db: Annotated[AsyncSession, Depends(get_db)],
):
    result = await db.execute(select(User).where(User.email == form_data.username))
    user = result.scalars().first()
    if not user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    if not user.hashed_password:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account was registered using Google Sign-In. Please log in with Google.",
        )

    if not verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Incorrect email or password",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user",
        )

    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))


@router.post(
    "/google",
    response_model=Token,
    summary="Authenticate with Google ID Token (Mobile & SPA)",
    description="Accepts Google ID Token (from mobile SDK / frontend GIS), verifies signature, and returns JWT session token.",
)
async def google_auth(
    body: GoogleAuthRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    """
    Industry-standard OAuth flow for Mobile (Flutter/React Native) and SPA (React/Next.js/Vue):
    Client signs in via Google SDK, gets ID Token, sends it here for server-side verification.
    """
    payload = GoogleAuthService.verify_id_token(body.id_token)
    user = await _process_google_user(db, payload)
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get(
    "/google/url",
    response_model=GoogleAuthUrlResponse,
    summary="Get Google OAuth Authorization URL",
    description="Generates Google OAuth 2.0 consent URL for web browser redirect flow.",
)
async def google_auth_url(state: str | None = Query(None, description="Optional CSRF state parameter")):
    url = GoogleAuthService.get_authorization_url(state=state)
    return GoogleAuthUrlResponse(authorization_url=url)


@router.get(
    "/google/callback",
    response_model=Token,
    summary="Google OAuth Redirect Callback",
    description="Handles callback redirect from Google consent screen, exchanges code for tokens, and logs in.",
)
async def google_auth_callback(
    code: str = Query(..., description="Authorization code from Google"),
    state: str | None = Query(None, description="CSRF state parameter"),
    db: Annotated[AsyncSession, Depends(get_db)] = None,
):
    token_response = await GoogleAuthService.exchange_code_for_tokens(code)
    id_token_str = token_response.get("id_token")
    if not id_token_str:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No ID token returned by Google OAuth server.",
        )

    payload = GoogleAuthService.verify_id_token(id_token_str)
    user = await _process_google_user(db, payload)
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))


@router.post(
    "/google/dev-mock",
    response_model=Token,
    summary="Development Google Login Mock (Postman / Testing)",
    description="Instant mock login for Postman testing without requiring real Google Cloud credentials in development mode.",
)
async def google_dev_mock(
    body: GoogleDevLoginRequest,
    db: Annotated[AsyncSession, Depends(get_db)],
):
    if settings.ENVIRONMENT != "development":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Mock authentication is only allowed in development environment.",
        )

    payload = {
        "google_id": body.sub,
        "email": body.email,
        "full_name": body.full_name,
        "avatar_url": body.picture,
        "email_verified": True,
    }
    user = await _process_google_user(db, payload)
    access_token = create_access_token(subject=user.id)
    return Token(access_token=access_token, token_type="bearer", user=UserResponse.model_validate(user))


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: Annotated[User, Depends(get_current_user)]):
    return current_user
