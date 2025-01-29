# --------------------------------------------------------------------------
# Phishing Detection API endpoints module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime
import logging

from . import APIRouter
from fastapi import Request

import src.qshing_server.service.phishing_analyzer as crud
from src.qshing_server.dto.base import ResponseSchema
from src.qshing_server.dto.phishing_schema import (
    PhishingDetectionRequest,
    PhishingDetectionResponse,
)

logger = logging.getLogger("main")

router = APIRouter(prefix="/phishing-detection")


@router.get("/")
async def determine():
    logger.info("Debug endpoint accessed")
    return {"message": "Phshing site detection with url"}


@router.post("/analyze", response_model=ResponseSchema[PhishingDetectionResponse])
def analyze(data: PhishingDetectionRequest, request: Request):
    print(data.url)
    logger.info(f"Phishing analysis requested for URL: {data.url}")
    result = crud.analyze(data.url, request)
    response = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message="SUCCESS",
        data=result,
    )
    logger.info(f"Analysis completed for URL: {data.url}")
    return response
