from pydantic import BaseModel, EmailStr


class GoogleAuthRequest(BaseModel):
    id_token: str


class GoogleAuthUrlResponse(BaseModel):
    authorization_url: str


class GoogleDevLoginRequest(BaseModel):
    email: EmailStr = "demo.google@sihijau.id"
    full_name: str = "Demo Google User"
    picture: str | None = "https://lh3.googleusercontent.com/a/default-avatar"
    sub: str = "google-dev-1234567890"


class GoogleCodeExchangeRequest(BaseModel):
    code: str
    redirect_uri: str | None = None
