from fastapi import FastAPI

from app.api.main import api_router

app = FastAPI(
    title="Squint-API",
)

app.include_router(api_router)
