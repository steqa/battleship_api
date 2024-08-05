from fastapi import FastAPI

from api.common import configure_logging
from api.session.routers import router as session_router

app = FastAPI(
    title="API",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)

app.include_router(session_router)

configure_logging(level=20)
