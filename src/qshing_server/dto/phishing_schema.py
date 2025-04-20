# --------------------------------------------------------------------------
# Phishing Detection DTO module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class PhishingDetectionRequest(BaseModel):
    url: str = Field(..., description="파싱할 URL")


class PhishingDetectionResponse(BaseModel):
    result: bool = Field(..., description="피싱 사이트 여부")
    confidence: float = Field(..., description="피싱 사이트 판별 신뢰도")
    source: str = Field("model", description="결과 출처 (cache, model, error)")


class UserFeedbackRequest(BaseModel):
    url: str = Field(..., description="피드백 제공할 URL")
    is_correct: bool = Field(..., description="AI 모델 판정 결과가 정확한지 여부")
    comment: Optional[str] = Field(None, description="사용자 피드백 내용")
    detected_result: bool = Field(..., description="AI 모델이 판정한 결과")
    confidence: float = Field(..., description="AI 모델의 판정 신뢰도")
    metadata: Optional[Dict[str, Any]] = Field(None, description="추가 메타데이터 (별점, 브라우저 정보, OS 등)")


class PhishingURLListResponse(BaseModel):
    urls: List[Dict[str, Any]] = Field(..., description="피싱 URL 목록")
    total: int = Field(..., description="전체 항목 수")
    offset: int = Field(0, description="시작 오프셋")
    limit: int = Field(..., description="조회 제한 수")
