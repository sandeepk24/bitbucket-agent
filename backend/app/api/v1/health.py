"""Health, readiness, and non-secret settings."""

from fastapi import APIRouter

from app.schemas.health import HealthResponse, ReadyResponse
from app.schemas.settings import SettingsResponse
from app.services import health as health_service

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return await health_service.build_health()


@router.get("/ready", response_model=ReadyResponse)
async def readiness() -> ReadyResponse:
    return health_service.build_ready()


@router.get("/settings", response_model=SettingsResponse)
async def get_settings() -> SettingsResponse:
    return health_service.build_settings()
