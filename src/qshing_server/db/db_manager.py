# --------------------------------------------------------------------------
# 데이터베이스 연결 관리 모듈
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Sequence, Union

import pymongo
import redis
from sqlalchemy import desc
from sqlalchemy.orm import sessionmaker
from sqlmodel import Session, SQLModel, create_engine, select

from src.qshing_server.core.config import settings
from src.qshing_server.core.exceptions import BackendExceptions
from src.qshing_server.db.models import PhishingURL, UserFeedback

logger = logging.getLogger("main")


class DBManager:
    _instance = None

    @classmethod
    def _reset_instance(cls):
        """테스트 목적으로 인스턴스 초기화 (테스트 환경에서만 사용)"""
        cls._instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(DBManager, cls).__new__(cls)
            cls._instance._initialize()
        return cls._instance

    def _initialize(self):
        # PostgreSQL 연결 설정
        self.postgres_engine = create_engine(settings.POSTGRES_URI)
        SQLModel.metadata.create_all(bind=self.postgres_engine)
        self.SessionLocal = sessionmaker(
            autocommit=False, autoflush=False, bind=self.postgres_engine
        )

        # Redis 연결 설정
        self.redis_client = redis.Redis(
            host=settings.REDIS_HOST,
            port=settings.REDIS_PORT,
            db=settings.REDIS_DB,
            decode_responses=True,
        )

        # MongoDB 연결 설정
        try:
            self.mongo_client = pymongo.MongoClient(
                settings.MONGODB_URI, serverSelectionTimeoutMS=5000  # timeout 5 secs
            )
            self.mongo_client.admin.command("ping")
            self.mongodb = self.mongo_client[settings.MONGODB_NAME]
            self.feedback_collection = self.mongodb["user_feedback"]
            logger.info("MongoDB connection initialized")
        except Exception as e:
            logger.error(f"MongoDB 연결 오류: {e}")
            if settings.is_test:
                logger.warning("테스트 환경에서 MongoDB 연결 실패, mock 사용")
                self.feedback_collection = None
            else:
                raise

    def get_postgres_session(self) -> Session:
        """PostgreSQL 세션 가져오기"""
        return self.SessionLocal()

    def close(self):
        """모든 데이터베이스 연결 종료"""
        if hasattr(self, "mongo_client"):
            self.mongo_client.close()
        if hasattr(self, "redis_client"):
            self.redis_client.close()
        logger.info("All database connections closed")

    # Redis 작업 메서드
    def cache_phishing_result(
        self, url: str, is_phishing: bool, confidence: float, ttl: int = 86400
    ) -> None:
        """피싱 URL 결과를 Redis에 캐시"""
        cache_data = {
            "is_phishing": is_phishing,
            "confidence": confidence,
            "last_updated": datetime.utcnow().isoformat(),
        }
        self.redis_client.setex(f"phishing:{url}", ttl, json.dumps(cache_data))
        logger.info(f"Cached result for URL: {url}")

    def get_cached_result(self, url: str) -> Optional[Dict[str, Any]]:
        """Redis에서 캐시된 피싱 URL 결과 조회"""
        result = self.redis_client.get(f"phishing:{url}")
        if result:
            logger.info(f"Cache hit for URL: {url}")
            return json.loads(result)
        logger.info(f"Cache miss for URL: {url}")
        return None

    def update_cache_from_db(self, limit: int = 1000) -> int:
        """PostgreSQL의 피싱 URL을 Redis 캐시로 업데이트"""
        session = self.get_postgres_session()
        try:
            urls = session.exec(
                select(PhishingURL)
                .where(PhishingURL.is_phishing == True)
                .order_by(desc("detection_time"))
                .limit(limit)
            ).all()

            count = 0
            for url_obj in urls:
                self.cache_phishing_result(
                    url_obj.url,
                    url_obj.is_phishing,
                    url_obj.confidence,
                )
                count += 1

            logger.info(f"Updated {count} URLs in cache from database")
            return count
        finally:
            session.close()

    def save_phishing_url(
        self,
        url: str,
        is_phishing: bool,
        confidence: float,
        html_content: Optional[str] = None,
        features: Optional[Dict[str, Any]] = None,
    ) -> PhishingURL:
        """피싱 URL 정보를 PostgreSQL에 저장"""
        session = self.get_postgres_session()
        try:
            existing = session.exec(
                select(PhishingURL).where(PhishingURL.url == url)
            ).first()

            if existing:
                # 기존 데이터 업데이트
                existing.is_phishing = is_phishing
                existing.confidence = confidence
                existing.detection_time = datetime.utcnow()
                if html_content:
                    existing.html_content = html_content
                if features:
                    existing.features = json.dumps(features)
                url_obj = existing
            else:
                # 새로운 데이터 추가
                url_obj = PhishingURL(
                    url=url,
                    is_phishing=is_phishing,
                    confidence=confidence,
                    html_content=html_content,
                    features=json.dumps(features) if features else None,
                )
                session.add(url_obj)

            session.commit()
            session.refresh(url_obj)
            logger.info(f"Saved phishing URL data: {url}")

            return url_obj
        except Exception as e:
            session.rollback()
            logger.error(f"Error saving URL to database: {e}")
            raise
        finally:
            session.close()

    def get_phishing_urls(
        self, limit: int = 100, offset: int = 0
    ) -> Sequence[PhishingURL]:
        """PostgreSQL에서 피싱 URL 목록 조회"""
        session = self.get_postgres_session()
        try:
            return session.exec(
                select(PhishingURL)
                .order_by(desc("detection_time"))
                .limit(limit)
                .offset(offset)
            ).all()
        finally:
            session.close()

    # MongoDB 작업 메서드
    def save_user_feedback(self, feedback: UserFeedback) -> str:
        """사용자 피드백을 MongoDB에 저장"""
        # 테스트 환경에서 MongoDB 연결 실패 시
        if self.feedback_collection is None:
            logger.warning("MongoDB mock 사용 중: save_user_feedback")
            return "test_id"

        try:
            result = self.feedback_collection.insert_one(feedback.model_dump())
            logger.info(f"Saved user feedback for URL: {feedback.url}")
            return str(result.inserted_id)
        except Exception as e:
            logger.error(f"Error saving feedback to MongoDB: {e}")
            raise BackendExceptions(f"Error saving feedback to MongoDB: {e}")

    def get_user_feedbacks(self, limit: int = 100) -> List[Dict[str, Any]]:
        """MongoDB에서 사용자 피드백 목록 조회"""
        return list(
            self.feedback_collection.find().sort("feedback_time", -1).limit(limit)
        )
