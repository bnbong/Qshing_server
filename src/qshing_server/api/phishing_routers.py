# --------------------------------------------------------------------------
# Phishing Detection API endpoints module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
from datetime import datetime

from fastapi import BackgroundTasks, Depends, Query, Request

import src.qshing_server.service.phishing_analyzer as crud
from src.qshing_server.dto.base import ResponseSchema
from src.qshing_server.dto.phishing_schema import (
    CacheUpdateResponse,
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
    Phshing site detection info 엔드포인트
    """
    result = {"status": "ok", "message": "Phshing site detection with url"}
    response: ResponseSchema[dict] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response


@router.post("/analyze", response_model=ResponseSchema[PhishingDetectionResponse])
def analyze(data: PhishingDetectionRequest, request: Request):
    """
    Phishing site detection 엔드포인트
    # TODO : 에러 처리 추가
    """
    result = crud.analyze(data.url, request)
    response: ResponseSchema[PhishingDetectionResponse] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response


@router.post("/feedback", response_model=ResponseSchema[dict])
def submit_feedback(data: UserFeedbackRequest):
    """
    사용자 피드백 제출 엔드포인트
    """
    result = crud.save_feedback(data)
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
):
    """
    최근 피싱 URL 목록 조회 엔드포인트

    개별 유저가 판별을 요청한 피싱 사이트 목록 조회가 아님.
    개발자 유지보수 측면에서 DB에 저장되어 있는 피싱 사이트 목록을 조회하는 endpoint이니
    주의할 것.
    """
    urls = crud.get_recent_phishing_urls(limit=limit, offset=offset)
    result = {
        "urls": urls,
        "total": len(urls),  # 실제로는 DB 전체 카운트를 가져와야 함
        "limit": limit,
        "offset": offset,
    }
    response: ResponseSchema[PhishingURLListResponse] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response


@router.post("/update-cache", response_model=ResponseSchema[CacheUpdateResponse])
def update_cache(background_tasks: BackgroundTasks):
    """
    Redis 캐시 업데이트 엔드포인트
    """
    # 백그라운드 작업
    background_tasks.add_task(crud.update_cache)

    result = {
        "status": "scheduled",
        "updated_count": 0,
        "timestamp": datetime.now().isoformat(),
    }
    response: ResponseSchema[CacheUpdateResponse] = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message=ResponseMessage.SUCCESS,
        data=result,
    )
    return response
