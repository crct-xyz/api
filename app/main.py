import logging
from fastapi import FastAPI
from app.api.main import api_router

# Configure logging
logging.basicConfig(
    level=logging.DEBUG,  # Change to INFO or WARNING in production
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Squint-API",
)

app.include_router(api_router)
