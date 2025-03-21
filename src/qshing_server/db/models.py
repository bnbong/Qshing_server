# --------------------------------------------------------------------------
# 데이터베이스 모델 정의 모듈
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime
from typing import Dict, List, Optional, Union

from beanie import Document
from pydantic import Field
from sqlmodel import JSON, Column
from sqlmodel import Field as SQLField
from sqlmodel import SQLModel


class Base(SQLModel):
    pass


class PhishingURL(SQLModel, table=True):
    """피싱 URL 데이터 모델"""

    __tablename__ = "phishing_urls"

    id: Optional[int] = SQLField(default=None, primary_key=True)
    url: str = SQLField(index=True)
    is_phishing: bool = SQLField(default=False)
    confidence: float = SQLField(default=0.0)
    detection_time: datetime = SQLField(default_factory=datetime.utcnow)
    html_content: Optional[str] = None
    features: Optional[str] = None  # JSON


# MongoDB 모델
class UserFeedback(Document):
    """사용자 피드백 데이터 모델"""

    url: str
    is_correct: bool
    detected_result: bool
    confidence: float
    user_comment: Optional[str] = None
    feedback_time: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict] = None

    class Settings:
        name = "user_feedback"


# Redis 캐시 키-값 구조 (개념적 모델)
# key: url
# value: {"is_phishing": bool, "confidence": float, "last_updated": timestamp}
