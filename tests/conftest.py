# --------------------------------------------------------------------------
# 테스트 공통 fixture 및 클래스
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import os
import subprocess
import time
from typing import Generator
from unittest.mock import MagicMock, patch

import motor.motor_asyncio
import pymongo
import pytest
from fastapi import Depends
from fastapi.testclient import TestClient
from sqlalchemy.orm import Session, sessionmaker
from sqlmodel import create_engine

from src.qshing_server.api import deps
from src.qshing_server.core.config import settings
from src.qshing_server.db.db_manager import DBManager
from src.qshing_server.db.models import SQLModel, UserFeedback
from src.qshing_server.main import app, init_beanie


class HTMLLoader:
    """테스트용 HTML 로더"""

    def load(self, url):
        return f"<html><body>테스트 페이지 {url}</body></html>"


class MockModel:
    """테스트용 가짜 모델 클래스"""

    def __init__(self):
        self.html_loader = HTMLLoader()

    def predict(self, url):
        if "phishing" in url:
            return {"result": True, "confidence": 0.95}
        else:
            return {"result": False, "confidence": 0.2}


# Test database settings - always use local docker containers
POSTGRES_TEST_USER = "admin"
POSTGRES_TEST_PASSWORD = "password"
POSTGRES_TEST_HOST = "localhost"
POSTGRES_TEST_PORT = "5432"
POSTGRES_TEST_DB = "phishing_data"

MONGODB_TEST_USER = "admin"
MONGODB_TEST_PASSWORD = "password"
MONGODB_TEST_HOST = "localhost"
MONGODB_TEST_PORT = "27017"
MONGODB_TEST_DB = "phishing_feedback"

REDIS_TEST_HOST = "localhost"
REDIS_TEST_PORT = "6379"
REDIS_TEST_DB = "0"

# Test PostgreSQL engine
SQLALCHEMY_TEST_DATABASE_URL = f"postgresql+psycopg2://{POSTGRES_TEST_USER}:{POSTGRES_TEST_PASSWORD}@{POSTGRES_TEST_HOST}:{POSTGRES_TEST_PORT}/{POSTGRES_TEST_DB}"
test_engine = create_engine(SQLALCHEMY_TEST_DATABASE_URL)
TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)


# Override environment variables for test
def override_env_vars():
    """Override environment variables for testing to ensure only local connections"""
    os.environ["POSTGRES_HOST"] = POSTGRES_TEST_HOST
    os.environ["POSTGRES_PORT"] = POSTGRES_TEST_PORT
    os.environ["POSTGRES_USER"] = POSTGRES_TEST_USER
    os.environ["POSTGRES_PASSWORD"] = POSTGRES_TEST_PASSWORD
    os.environ["POSTGRES_DB"] = POSTGRES_TEST_DB

    os.environ["MONGODB_HOST"] = MONGODB_TEST_HOST
    os.environ["MONGODB_PORT"] = MONGODB_TEST_PORT
    os.environ["MONGODB_USER"] = MONGODB_TEST_USER
    os.environ["MONGODB_PASSWORD"] = MONGODB_TEST_PASSWORD
    os.environ["MONGODB_NAME"] = MONGODB_TEST_DB

    os.environ["REDIS_HOST"] = REDIS_TEST_HOST
    os.environ["REDIS_PORT"] = REDIS_TEST_PORT
    os.environ["REDIS_DB"] = REDIS_TEST_DB

    # Ensure test environment
    os.environ["ENVIRONMENT"] = "development"


# 테스트 환경에서 사용할 의존성 오버라이드 함수들
def get_test_db_manager():
    """테스트용 DB 매니저 가져오기"""
    manager = TestDBManager()
    try:
        yield manager
    finally:
        # 테스트 후 정리 작업은 여기서 수행
        pass


def get_test_db_session():
    """테스트용 DB 세션 가져오기"""
    db = TestSessionLocal()
    try:
        yield db
    finally:
        db.close()


# 테스트 전용 DB 매니저 클래스
class TestDBManager:
    """테스트 환경을 위한 DB 매니저"""

    def __init__(self):
        self._init_test_connections()
        self._ensure_tables_exist()

    def _init_test_connections(self):
        """테스트용 연결 초기화"""
        # Redis 테스트 연결
        import redis

        self.redis_client = redis.Redis(
            host=REDIS_TEST_HOST,
            port=int(REDIS_TEST_PORT),
            db=int(REDIS_TEST_DB),
            decode_responses=True,
        )

        # PostgreSQL 테스트 연결
        self.postgres_engine = test_engine
        self.SessionLocal = TestSessionLocal

        # MongoDB 테스트 연결 (모킹)
        self.mongo_client = MagicMock()
        mock_db = MagicMock()
        mock_collection = MagicMock()

        self.mongo_client.__getitem__.return_value = mock_db
        mock_db.__getitem__.return_value = mock_collection

        self.feedback_collection = mock_collection
        # MongoDB ID 생성 모킹
        self.feedback_collection.insert_one.return_value.inserted_id = "mock-id-12345"

    def _ensure_tables_exist(self):
        """테이블이 존재하는지 확인하고 없으면 생성"""
        from src.qshing_server.db.models import SQLModel

        SQLModel.metadata.create_all(self.postgres_engine)

    def close(self):
        """테스트 연결 종료"""
        if hasattr(self, "redis_client"):
            self.redis_client.close()

    # db_manager와 호환되는 메서드들 구현
    def get_postgres_session(self) -> Session:
        return self.SessionLocal()

    def cache_phishing_result(self, url, is_phishing, confidence, ttl=86400):
        import json
        from datetime import datetime

        cache_data = {
            "is_phishing": is_phishing,
            "confidence": confidence,
            "last_updated": datetime.now().isoformat(),
        }
        self.redis_client.setex(f"phishing:{url}", ttl, json.dumps(cache_data))

    def get_cached_result(self, url):
        import json

        result = self.redis_client.get(f"phishing:{url}")
        if result:
            return json.loads(result)
        return None

    def save_phishing_url(
        self, url, is_phishing, confidence, html_content=None, features=None
    ):
        import json
        from datetime import datetime

        from src.qshing_server.db.models import PhishingURL

        # Ensure tables exist
        self._ensure_tables_exist()

        session = self.get_postgres_session()
        try:
            existing = session.query(PhishingURL).filter(PhishingURL.url == url).first()

            if existing:
                existing.is_phishing = is_phishing
                existing.confidence = confidence
                existing.detection_time = datetime.now()
                if html_content:
                    existing.html_content = html_content
                if features:
                    existing.features = json.dumps(features)
                url_obj = existing
            else:
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
            return url_obj
        except Exception as e:
            session.rollback()
            raise e
        finally:
            session.close()

    def get_phishing_urls(self, limit=100, offset=0):
        from src.qshing_server.db.models import PhishingURL

        # Ensure tables exist
        self._ensure_tables_exist()

        session = self.get_postgres_session()
        try:
            return (
                session.query(PhishingURL)
                .order_by(PhishingURL.detection_time.desc())
                .limit(limit)
                .offset(offset)
                .all()
            )
        finally:
            session.close()

    def save_user_feedback(self, feedback):
        # 모킹된 ID 반환
        return "mock-id-12345"

    def get_user_feedbacks(self, limit=100):
        # 모킹된 피드백 데이터 반환
        return [
            {
                "url": "http://feedback-test.com",
                "is_correct": True,
                "user_comment": "This result is accurate",
                "detected_result": True,
                "confidence": 0.95,
            }
        ]

    def update_cache_from_db(self, limit=1000):
        from src.qshing_server.db.models import PhishingURL

        # Ensure tables exist
        self._ensure_tables_exist()

        session = self.get_postgres_session()
        try:
            urls = (
                session.query(PhishingURL)
                .filter(PhishingURL.is_phishing == True)
                .order_by(PhishingURL.detection_time.desc())
                .limit(limit)
                .all()
            )

            count = 0
            for url_obj in urls:
                self.cache_phishing_result(
                    url_obj.url, url_obj.is_phishing, url_obj.confidence
                )
                count += 1

            return count
        finally:
            session.close()


@pytest.fixture(scope="session", autouse=True)
def setup_test_environment():
    """Setup test environment with safety measures"""
    # Override environment variables
    original_env = dict(os.environ)
    override_env_vars()

    # Setup mock MongoDB client
    mock_mongo_client = MagicMock()
    mock_db = MagicMock()
    mock_collection = MagicMock()

    mock_mongo_client.__getitem__.return_value = mock_db
    mock_db.__getitem__.return_value = mock_collection

    # Patch MongoDB client
    with patch(
        "motor.motor_asyncio.AsyncIOMotorClient", return_value=mock_mongo_client
    ):
        # Patch Beanie initialization
        with patch("src.qshing_server.main.init_beanie"):
            yield

    # Restore original environment
    os.environ.clear()
    os.environ.update(original_env)


@pytest.fixture(scope="session")
def docker_setup() -> Generator[None, None, None]:
    """테스트를 위한 Docker 컨테이너 설정"""
    try:
        subprocess.run(
            ["docker-compose", "up", "-d"],
            check=True,
            capture_output=True,
        )

        time.sleep(10)

        yield
    finally:
        subprocess.run(
            ["docker-compose", "down", "-v"],
            check=True,
            capture_output=True,
        )


@pytest.fixture
def test_db(docker_setup):
    """테스트 데이터베이스 설정"""
    SQLModel.metadata.drop_all(test_engine)
    SQLModel.metadata.create_all(test_engine)

    yield

    SQLModel.metadata.drop_all(test_engine)


@pytest.fixture
def client(docker_setup, test_db):
    """테스트 클라이언트 설정 - 의존성 오버라이드 적용"""
    # 모델 객체를 모의 객체로 교체
    app.state.model = MockModel()

    # Mock MongoDB client in the app
    mock_mongo_client = MagicMock()
    mock_db = MagicMock()
    app.state.mongo_client = mock_mongo_client
    mock_mongo_client.__getitem__.return_value = mock_db

    # 원래 의존성을 테스트용 의존성으로 오버라이드
    app.dependency_overrides[deps.get_db_manager] = get_test_db_manager
    app.dependency_overrides[deps.get_db] = get_test_db_session

    # Patch MongoDB initialization
    with patch("motor.motor_asyncio.AsyncIOMotorClient"):
        # Patch Beanie initialization
        with patch("src.qshing_server.main.init_beanie"):
            with TestClient(app) as test_client:
                yield test_client

    # 테스트 후 의존성 오버라이드 제거
    app.dependency_overrides.clear()


@pytest.fixture
def db_manager() -> TestDBManager:  # type: ignore
    """테스트를 위한 DB 매니저 인스턴스"""
    manager = TestDBManager()

    # 테스트 데이터 초기화
    try:
        keys = manager.redis_client.keys("phishing:*")
        if keys:
            manager.redis_client.delete(*keys)

        # MongoDB 초기화
        manager.feedback_collection.delete_many({})
    except Exception as e:
        print(f"DB 초기화 중 오류: {e}")

    yield manager

    manager.close()
