"""FastAPI application factory."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.bitbucket import router as bitbucket_router
from app.api.v1.router import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging
from app.providers.bitbucket.client import BitbucketClient
from app.providers.bitbucket.config import BitbucketConfig
from app.providers.bitbucket.errors import BitbucketError

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncIterator[None]:
    client = BitbucketClient(BitbucketConfig.from_settings())
    app.state.bitbucket = client
    logger.info(
        "Bitbucket client ready configured=%s host=%s",
        client.is_configured(),
        client.config.base_url or "(unset)",
    )
    try:
        yield
    finally:
        await client.aclose()


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    setup_logging()

    application = FastAPI(
        title=settings.app_name,
        description=(
            "Enterprise DevOps intelligence for Bitbucket Data Center. "
            "Enterprise DevOps intelligence for Bitbucket Data Center, including SHA-locked "
            "PR comparison and deep analysis."
        ),
        version=settings.app_version,
        docs_url="/docs",
        redoc_url="/redoc",
        openapi_url="/openapi.json",
        lifespan=lifespan,
    )

    application.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    application.include_router(api_router)
    application.include_router(bitbucket_router)

    @application.get("/", include_in_schema=False)
    async def root() -> dict[str, str]:
        return {
            "name": settings.app_name,
            "version": settings.app_version,
            "docs": "/docs",
            "health": "/api/v1/health",
            "bitbucket_health": "/api/bitbucket/health",
        }

    @application.exception_handler(BitbucketError)
    async def bitbucket_error(request: Request, exc: BitbucketError) -> JSONResponse:
        logger.warning(
            "Bitbucket error on %s: %s",
            request.url.path,
            exc.message,
        )
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.message},
        )

    @application.exception_handler(Exception)
    async def unhandled_error(request: Request, exc: Exception) -> JSONResponse:
        logger.exception("Unhandled error on %s: %s", request.url.path, exc)
        return JSONResponse(
            status_code=500,
            content={"detail": "An unexpected error occurred"},
        )

    return application


app = create_app()
