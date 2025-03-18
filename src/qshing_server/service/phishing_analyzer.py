# --------------------------------------------------------------------------
# Phishing CRUD module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
from typing import Any, Dict, Optional, Type

from fastapi import Request

from src.qshing_server.core.config import settings
from src.qshing_server.db.db_manager import DBManager
from src.qshing_server.db.models import UserFeedback
from src.qshing_server.dto.phishing_schema import (
    PhishingDetectionResponse,
    UserFeedbackRequest,
)

logger = logging.getLogger("main")


def analyze(
    url: str,
    request: Request,
    response_model: Type[PhishingDetectionResponse] = PhishingDetectionResponse,
) -> Optional[Any]:
    logger.info(f"Analyzing URL: {url}")

    db_manager = DBManager()

    # 1. Redis 캐시에서 결과 확인
    cached_result = db_manager.get_cached_result(url)
    if cached_result:
        logger.info(
            f"Using cached result for URL: {url} - Is phishing site: {cached_result['is_phishing']}, Confidence: {cached_result['confidence']}"
        )
        return response_model.model_validate(
            {
                "result": cached_result["is_phishing"],
                "confidence": cached_result["confidence"],
                "source": "cache",
            }
        )

    # 2. 캐시에 없으면 AI 모델로 분석
    detector = request.app.state.model
    result = detector.predict(url)

    if result["confidence"] is not None:
        logger.info(
            f"AI 분석 결과: {url} - 피싱 여부: {result['result']}, 신뢰도: {result['confidence']:.4f}"
        )

        # HTML 콘텐츠 가져오기
        html_content = None
        if hasattr(detector, "html_loader") and detector.html_loader:
            try:
                html_content = detector.html_loader.load(url)
            except Exception as e:
                logger.warning(f"Failed to get HTML for storage: {e}")

        # PostgreSQL에 데이터 저장
        db_manager.save_phishing_url(
            url=url,
            is_phishing=result["result"],
            confidence=result["confidence"],
            html_content=html_content,
        )

        # 피싱으로 판정된 경우, Redis에 캐시
        if result["result"]:
            db_manager.cache_phishing_result(
                url=url, is_phishing=result["result"], confidence=result["confidence"]
            )

        return response_model.model_validate(
            {
                "result": result["result"],
                "confidence": result["confidence"],
                "source": "model",
            }
        )
    else:
        logger.error(f"Failed to analyze URL: {url}")
        return response_model.model_validate(
            {"result": False, "confidence": 0.0, "source": "error"}
        )


def save_feedback(feedback: UserFeedbackRequest) -> Dict[str, Any]:
    """사용자 피드백 저장"""
    logger.info(f"Saving feedback for URL: {feedback.url}")

    db_manager = DBManager()

    # MongoDB에 피드백 저장
    user_feedback = UserFeedback(
        url=feedback.url,
        is_correct=feedback.is_correct,
        user_comment=feedback.comment,
        detected_result=feedback.detected_result,
        confidence=feedback.confidence,
        metadata=feedback.metadata,
    )

    feedback_id = db_manager.save_user_feedback(user_feedback)

    return {"feedback_id": feedback_id, "status": "success"}


def get_recent_phishing_urls(limit: int = 100, offset: int = 0) -> list:
    """최근 피싱 URL 목록 조회"""
    logger.info(f"Fetching recent phishing URLs, limit: {limit}, offset: {offset}")

    db_manager = DBManager()
    urls = db_manager.get_phishing_urls(limit=limit, offset=offset)

    return [
        {
            "url": url.url,
            "is_phishing": url.is_phishing,
            "confidence": url.confidence,
            "detection_time": url.detection_time.isoformat(),
        }
        for url in urls
    ]


def update_cache() -> Dict[str, Any]:
    """PostgreSQL의 피싱 URL을 Redis 캐시로 업데이트"""
    logger.info("Updating Redis cache from PostgreSQL")

    db_manager = DBManager()
    count = db_manager.update_cache_from_db()

    return {"updated_count": count, "status": "success"}
