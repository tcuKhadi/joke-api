"""FastAPI application entrypoint."""

from contextlib import asynccontextmanager

from fastapi import FastAPI

from app.api.v1.battles import router as battles_router
from app.api.v1.categories import router as categories_router
from app.api.v1.jokes import router as jokes_router
from app.api.v1.roasts import router as roasts_router
from app.core.config import settings
from app.core.logging import configure_logging, get_logger
from app.core.security import configure_security
from app.services.cache_service import cache_service

logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage startup and shutdown resources."""
    configure_logging()
    logger.info("app_startup", environment=settings.environment)
    yield
    await cache_service.close()
    logger.info("app_shutdown")


app = FastAPI(
    title="Joke API",
    version="0.1.0",
    lifespan=lifespan,
)

configure_security(app)

app.include_router(categories_router, prefix="/v1")
app.include_router(jokes_router, prefix="/v1")
app.include_router(roasts_router, prefix="/v1")
app.include_router(battles_router, prefix="/v1")