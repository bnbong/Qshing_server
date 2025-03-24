# --------------------------------------------------------------------------
# Main server application module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from contextlib import asynccontextmanager
from datetime import datetime

import motor.motor_asyncio
from beanie import init_beanie
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from src.qshing_server.api import api_router
from src.qshing_server.core.config import settings
from src.qshing_server.db.db_manager import DBManager
from src.qshing_server.db.models import UserFeedback
from src.qshing_server.service.model.model_manager import PhishingDetector
from src.qshing_server.utils.logging import Logger

logger = Logger(file_path=f'./log/{datetime.now().strftime("%Y-%m-%d")}', name="main")


@asynccontextmanager
async def lifespan(app: FastAPI):
    try:
        logger.info("Starting server...")

        logger.info("Initializing database connections...")
        app.state.db_manager = DBManager()

        # 모델 로드
        logger.info("Loading model...")
        app.state.model = PhishingDetector(model_path=settings.MODEL_PATH)

        if not hasattr(app.state, "mongo_client"):
            logger.info("Initializing MongoDB connection...")
            mongo_uri = str(settings.MONGODB_URI)
            app.state.mongo_client = motor.motor_asyncio.AsyncIOMotorClient(mongo_uri)

        await init_beanie(
            database=app.state.mongo_client[settings.MONGODB_NAME],
            document_models=[UserFeedback],
        )

        logger.info("Application startup complete")

        yield
    finally:
        logger.info("Shutting down server...")

        if hasattr(app.state, "db_manager"):
            logger.info("Closing database connections...")
            app.state.db_manager.close()

        # 모델 언로드
        app.state.model = None
        logger.info("Model unloaded")

        if hasattr(app.state, "mongo_client") and app.state.mongo_client is not None:
            logger.info("Closing MongoDB connection...")
            app.state.mongo_client.close()
            app.state.mongo_client = None

        logger.info("Application shutdown complete")


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


app.include_router(api_router)
