from fastapi import APIRouter

from app.api.v1.endpoints import (
    action_logs,
    auth,
    decisions,
    guides,
    partners,
    scans,
    users,
)

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_router.include_router(users.router, prefix="/users", tags=["Users"])
api_router.include_router(scans.router, prefix="/scans", tags=["Waste Scanner"])
api_router.include_router(decisions.router, prefix="/decisions", tags=["Decision Engine"])
api_router.include_router(partners.router, prefix="/partners", tags=["Partner Directory"])
api_router.include_router(guides.router, prefix="/guides", tags=["Processing Guides"])
api_router.include_router(action_logs.router, prefix="/action-logs", tags=["Action & Impact Logs"])
