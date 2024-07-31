from fastapi import FastAPI

app = FastAPI(
    title="API",
    docs_url="/api/v1/docs",
    redoc_url="/api/v1/redoc",
)
