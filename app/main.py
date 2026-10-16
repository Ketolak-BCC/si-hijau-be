import logging
import time
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from sqladmin import Admin

from app.admin.views import (
    ActionLogAdmin,
    PartnerAdmin,
    ProcessingGuideAdmin,
    ScanHistoryAdmin,
    UserAdmin,
)
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.database import Base, engine

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("sihijau.api")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)
    except Exception:
        pass
    yield


app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan,
)

if settings.CORS_ORIGINS:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.perf_counter()
    client_ip = request.client.host if request.client else "unknown"
    method = request.method
    path = request.url.path

    response = await call_next(request)
    duration_ms = (time.perf_counter() - start_time) * 1000

    logger.info(
        f"[{method}] {path} -> {response.status_code} ({duration_ms:.2f}ms) from {client_ip}"
    )
    return response


app.include_router(api_router, prefix=settings.API_V1_STR)

admin = Admin(app, engine=engine)
admin.add_view(UserAdmin)
admin.add_view(PartnerAdmin)
admin.add_view(ProcessingGuideAdmin)
admin.add_view(ScanHistoryAdmin)
admin.add_view(ActionLogAdmin)


@app.get("/health", tags=["Health"])
async def health_check():
    return {
        "status": "healthy",
        "app": settings.PROJECT_NAME,
        "environment": settings.ENVIRONMENT,
    }
