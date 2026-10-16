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

    # Register versioned API v1 routes
    app.include_router(api_v1_router)

    # Root discovery endpoint
    @app.get("/", tags=["root"])
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
