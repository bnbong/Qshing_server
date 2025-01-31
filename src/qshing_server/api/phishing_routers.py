# --------------------------------------------------------------------------
# Phishing Detection API endpoints module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
from datetime import datetime

from fastapi import Request

import src.qshing_server.service.phishing_analyzer as crud
from src.qshing_server.dto.base import ResponseSchema
from src.qshing_server.dto.phishing_schema import (
    PhishingDetectionRequest,
    PhishingDetectionResponse,
)

from . import APIRouter

logger = logging.getLogger("main")

router = APIRouter(prefix="/phishing-detection")


@router.get("/")
async def determine():
    """
    Phshing site detection info 엔드포인트
    """
    result = {"status": "ok", "message": "Phshing site detection with url"}
    response: ResponseSchema[dict] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message="SUCCESS",
        data=result,
    )
    return response


@router.post("/analyze", response_model=ResponseSchema[PhishingDetectionResponse])
def analyze(data: PhishingDetectionRequest, request: Request):
    """
    Phishing site detection 엔드포인트
    """
    result = crud.analyze(data.url, request)
    response: ResponseSchema[PhishingDetectionResponse] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message="SUCCESS",
        data=result,
    )
    return response
