"""
Application entrypoint. Run with:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
"""
import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from config.settings import get_settings
from database.session import Base, engine
import models  # noqa: F401  (registers all models on Base.metadata)
from routes import settings_routes  # registers InstituteSettings model too
from routes import (
    auth_routes, academic_routes, question_routes, evaluation_routes,
    dashboard_routes, report_routes, websocket_routes,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)
settings = get_settings()

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(
    title=settings.APP_NAME,
    description=(
        "AI-powered platform for OCR-based handwritten answer script reading, "
        "NLP semantic evaluation, and automated mark assignment with teacher verification."
    ),
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
)

app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled exception on %s %s", request.method, request.url)
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.on_event("startup")
def on_startup() -> None:
    # Dev convenience: auto-create tables if they don't exist yet.
    # Production deployments should use Alembic migrations instead.
    if settings.APP_ENV == "development":
        Base.metadata.create_all(bind=engine)


@app.get("/api/health", tags=["Health"])
def health_check():
    return {"status": "ok", "app": settings.APP_NAME, "env": settings.APP_ENV}


PREFIX = settings.API_V1_PREFIX
app.include_router(auth_routes.router, prefix=PREFIX)
app.include_router(academic_routes.router, prefix=PREFIX)
app.include_router(question_routes.router, prefix=PREFIX)
app.include_router(evaluation_routes.router, prefix=PREFIX)
app.include_router(dashboard_routes.router, prefix=PREFIX)
app.include_router(report_routes.router, prefix=PREFIX)
app.include_router(settings_routes.router, prefix=PREFIX)
app.include_router(websocket_routes.router)
