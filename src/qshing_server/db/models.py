# --------------------------------------------------------------------------
# 데이터베이스 모델 정의
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field
from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String, Text
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


# PostgreSQL 모델
class PhishingURL(Base):  # type: ignore
    __tablename__ = "phishing_urls"

    id = Column(Integer, primary_key=True, index=True)
    url = Column(String, index=True)
    is_phishing = Column(Boolean, default=False)
    confidence = Column(Float)
    detection_time = Column(DateTime, default=datetime.utcnow)
    html_content = Column(Text, nullable=True)
    features = Column(Text, nullable=True)  # JSON 형태로 저장될 특성들


# MongoDB 문서 모델
class UserFeedback(BaseModel):
    url: str
    is_correct: bool
    user_comment: Optional[str] = None
    detected_result: bool
    confidence: float
    feedback_time: datetime = Field(default_factory=datetime.utcnow)
    metadata: Optional[Dict[str, Any]] = None


# Redis 캐시 키-값 구조 (개념적 모델)
# key: url
# value: {"is_phishing": bool, "confidence": float, "last_updated": timestamp}
