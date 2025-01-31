# --------------------------------------------------------------------------
# Main server application module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from contextlib import asynccontextmanager
from datetime import datetime

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.qshing_server.api import api_router
from src.qshing_server.core.config import settings
from src.qshing_server.service.model.model_manager import PhishingDetector
from src.qshing_server.utils.logging import Logger

logger = Logger(file_path=f'./log/{datetime.now().strftime("%Y-%m-%d")}', name="main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting server...")

        logger.info("Loading model...")
        app.state.model = PhishingDetector(model_path=settings.MODEL_PATH)
        yield
    finally:
        logger.info("Shutting down server...")
        app.state.model = None
        logger.info("Model unloaded")


app = FastAPI(
    title=settings.PROJECT_NAME,
    lifespan=lifespan,
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )


@app.get("/")
def read_root():
    return {"message": "Main page"}


app.include_router(api_router)
