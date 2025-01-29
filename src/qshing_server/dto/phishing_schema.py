# --------------------------------------------------------------------------
# Phishing Detection DTO module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from pydantic import BaseModel, Field

from src.qshing_server.dto.base import ResponseSchema


class PhishingDetectionRequest(BaseModel):
    url: str = Field(..., description="파싱할 URL")


class PhishingDetectionResponse(BaseModel):
    result: bool = Field(..., description="피싱 사이트 여부")
    confidence: float = Field(..., description="피싱 사이트 판별 신뢰도")
