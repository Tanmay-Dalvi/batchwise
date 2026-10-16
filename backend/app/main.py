"""Batchwise application entry point and FastAPI server factory.

Every batch. Every cost. Every rupee.
"""

from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.v1 import api_v1_router
from app.calculator.exceptions import BatchwiseError
from app.config import settings
from app.db.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Predictable database initialization on application startup."""
    init_db()
    yield


def create_application() -> FastAPI:
    """FastAPI application factory."""
    app = FastAPI(
        title=settings.PROJECT_NAME,
        description=f"{settings.TAGLINE} — Local-first batch costing & profit intelligence.",
        version=settings.VERSION,
        lifespan=lifespan,
    )

    # Configure CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.CORS_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Domain error exception handler
    @app.exception_handler(BatchwiseError)
    async def batchwise_error_handler(request: Request, exc: BatchwiseError):
        return JSONResponse(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            content={
                "detail": {
                    "error_type": exc.__class__.__name__,
                    "message": str(exc),
                }
            },
        )

    from fastapi import APIRouter
    from app.api.v1.batches import router as batches_router
    from app.api.v1.calculate import router as calculate_router
    from app.api.v1.health import router as health_router
    from app.api.v1.parse import router as parse_router
    from app.api.v1.recipes import router as recipes_router

    # Register versioned API v1 routes
    app.include_router(api_v1_router)

    # Register root compatibility routes (for clients connecting to host without /api/v1)
    root_compat_router = APIRouter(include_in_schema=False)
    root_compat_router.include_router(health_router)
    root_compat_router.include_router(calculate_router)
    root_compat_router.include_router(parse_router)
    root_compat_router.include_router(recipes_router)
    root_compat_router.include_router(batches_router)
    app.include_router(root_compat_router)

    # Root discovery endpoint (supports both GET and HEAD for container health checks)
    @app.api_route("/", methods=["GET", "HEAD"], tags=["root"])
    def root():
        return {
            "app": settings.PROJECT_NAME,
            "tagline": settings.TAGLINE,
            "version": settings.VERSION,
            "docs_url": "/docs",
            "health_url": f"{settings.API_V1_PREFIX}/health",
        }

    return app


app = create_application()

if __name__ == "__main__":
    import os
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    host = os.getenv("HOST", "0.0.0.0")
    uvicorn.run("app.main:app", host=host, port=port, reload=False)
