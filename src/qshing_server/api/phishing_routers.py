# --------------------------------------------------------------------------
# Phishing Detection API endpoints module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
from datetime import datetime

from fastapi import Depends, Query, Request

import src.qshing_server.service.phishing_analyzer as crud
from src.qshing_server.api.deps import get_db_manager
from src.qshing_server.db.db_manager import DBManager
from src.qshing_server.dto.base import ResponseSchema
from src.qshing_server.dto.phishing_schema import (
    PhishingDetectionRequest,
    PhishingDetectionResponse,
    PhishingURLListResponse,
    UserFeedbackRequest,
)
from src.qshing_server.utils.enums import ResponseMessage

from . import APIRouter

logger = logging.getLogger("main")

router = APIRouter(prefix="/phishing-detection")


@router.get("/")
async def determine():
    """
    Phshing site detection info 엔드포인트 (health check)
    """
    result = {"status": "ok", "message": "Phshing site detection with url"}
    response: ResponseSchema[dict] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response


@router.post("/analyze", response_model=ResponseSchema[PhishingDetectionResponse])
def analyze(
    data: PhishingDetectionRequest,
    request: Request,
    db_manager: DBManager = Depends(get_db_manager),
):
    """
    Phishing site detection 엔드포인트
    """
    result = crud.analyze(data.url, request, db_manager=db_manager)
    response: ResponseSchema[PhishingDetectionResponse] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response


@router.post("/feedback", response_model=ResponseSchema[dict])
def submit_feedback(
    data: UserFeedbackRequest, db_manager: DBManager = Depends(get_db_manager)
):
    """
    사용자 피드백 제출 엔드포인트
    """
    result = crud.save_feedback(data, db_manager=db_manager)
    response: ResponseSchema[dict] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response


@router.get("/recent", response_model=ResponseSchema[PhishingURLListResponse])
def get_recent_phishing(
    limit: int = Query(100, ge=1, le=1000),
    offset: int = Query(0, ge=0),
    db_manager: DBManager = Depends(get_db_manager),
):
    """
    최근 URL 판별 요청 목록 조회 엔드포인트
    """
    urls = crud.get_recent_phishing_urls(
        db_manager=db_manager, limit=limit, offset=offset
    )
    result = {
        "urls": urls,
        "total": len(urls),
        "limit": limit,
        "offset": offset,
    }
    response: ResponseSchema[PhishingURLListResponse] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response
