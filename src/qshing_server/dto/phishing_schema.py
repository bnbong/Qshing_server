# --------------------------------------------------------------------------
# Phishing Detection DTO module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.qshing_server.dto.base import ResponseSchema


class PhishingDetectionRequest(BaseModel):
    url: str = Field(..., description="파싱할 URL")


class PhishingDetectionResponse(BaseModel):
    result: bool = Field(..., description="피싱 사이트 여부")
    confidence: float = Field(..., description="피싱 사이트 판별 신뢰도")
    source: str = Field("model", description="결과 출처 (cache, model, error)")


class UserFeedbackRequest(BaseModel):
    url: str = Field(..., description="피드백을 제공하는 URL")
    is_correct: bool = Field(..., description="AI 모델 판정 결과가 정확한지 여부")
    comment: Optional[str] = Field(None, description="사용자 피드백 내용")
    detected_result: bool = Field(..., description="AI 모델이 판정한 결과")
    confidence: float = Field(..., description="AI 모델의 판정 신뢰도")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터")


class PhishingURLListResponse(BaseModel):
    urls: List[Dict[str, Any]] = Field(..., description="피싱 URL 목록")
    total: int = Field(..., description="전체 항목 수")
    offset: int = Field(0, description="시작 오프셋")
    limit: int = Field(..., description="조회 제한 수")


class CacheUpdateResponse(BaseModel):
    updated_count: int = Field(..., description="업데이트된 항목 수")
    status: str = Field(..., description="상태")
    timestamp: datetime = Field(
        default_factory=datetime.utcnow, description="업데이트 시간"
    )
