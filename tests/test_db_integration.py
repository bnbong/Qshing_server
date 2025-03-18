# --------------------------------------------------------------------------
# 데이터베이스 통합 테스트
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import subprocess
import time
from typing import Generator

import pymongo
import pytest

from src.qshing_server.db.db_manager import DBManager
from src.qshing_server.db.models import PhishingURL, UserFeedback
from src.qshing_server.service.phishing_analyzer import analyze


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
def db_manager() -> DBManager:
    """테스트를 위한 DBManager 인스턴스"""
    DBManager._reset_instance()
    manager = DBManager()

    # Initialize DB
    try:
        keys = manager.redis_client.keys("phishing:*")
        if keys:
            manager.redis_client.delete(*keys)

        session = manager.get_postgres_session()
        session.query(PhishingURL).delete()
        session.commit()
        session.close()

        manager.feedback_collection.delete_many({})
    except Exception as e:
        print(f"초기 정리 중 오류 발생: {e}")

    return manager


def test_redis_operations(docker_setup, db_manager):
    """Redis 캐시 작업 테스트"""
    # 캐시 저장 테스트
    db_manager.cache_phishing_result("http://example.com", True, 0.95)

    # 캐시 조회 테스트
    result = db_manager.get_cached_result("http://example.com")
    assert result is not None
    assert result["is_phishing"] is True
    assert result["confidence"] == 0.95

    # 캐시 미스 테스트
    result = db_manager.get_cached_result("http://nonexistent.com")
    assert result is None


def test_postgres_operations(docker_setup, db_manager):
    """PostgreSQL 작업 테스트"""
    # URL 저장 테스트
    url_obj = db_manager.save_phishing_url(
        "http://test-phishing.com",
        True,
        0.95,
        html_content="<html><body>Test</body></html>",
    )

    assert url_obj is not None
    assert url_obj.url == "http://test-phishing.com"
    assert url_obj.is_phishing is True
    assert url_obj.confidence == 0.95

    # URL 업데이트 테스트
    updated_obj = db_manager.save_phishing_url("http://test-phishing.com", True, 0.98)

    assert updated_obj.confidence == 0.98

    # URL 목록 조회 테스트
    urls = db_manager.get_phishing_urls()
    assert len(urls) >= 1

    found = False
    for url in urls:
        if url.url == "http://test-phishing.com":
            found = True
            assert url.is_phishing is True
            assert url.confidence == 0.98

    assert found, "저장한 URL을 찾을 수 없습니다"


def test_mongodb_operations(docker_setup, db_manager):
    """MongoDB 작업 테스트"""
    # 피드백 저장 테스트
    feedback = UserFeedback(
        url="http://feedback-test.com",
        is_correct=True,
        user_comment="이 결과는 정확합니다",
        detected_result=True,
        confidence=0.95,
    )

    feedback_id = db_manager.save_user_feedback(feedback)
    assert feedback_id is not None

    # 피드백 조회 테스트
    feedbacks = db_manager.get_user_feedbacks()
    assert len(feedbacks) >= 1

    found = False
    for item in feedbacks:
        if item["url"] == "http://feedback-test.com":
            found = True
            assert item["is_correct"] is True
            assert item["user_comment"] == "이 결과는 정확합니다"

    assert found, "저장한 피드백을 찾을 수 없습니다"


def test_cache_update_from_db(docker_setup, db_manager):
    """PostgreSQL에서 Redis로 캐시 업데이트 테스트"""
    urls = [
        ("http://update-test1.com", True, 0.91),
        ("http://update-test2.com", True, 0.92),
        ("http://update-test3.com", False, 0.45),  # 피싱이 아닌 URL
    ]

    for url, is_phishing, confidence in urls:
        db_manager.save_phishing_url(url, is_phishing, confidence)

    # 기존 캐시 정리
    keys = db_manager.redis_client.keys("phishing:*")
    if keys:
        db_manager.redis_client.delete(*keys)

    count = db_manager.update_cache_from_db()

    # 피싱 URL만 캐시되었는지 확인 (is_phishing=True인 항목만)
    assert count >= 2  # 적어도 2개 이상의 피싱 URL이 캐시되어야 함

    # 피싱 URL 확인
    assert db_manager.get_cached_result("http://update-test1.com") is not None
    assert db_manager.get_cached_result("http://update-test2.com") is not None

    # 피싱이 아닌 URL은 캐시되지 않아야 함
    assert db_manager.get_cached_result("http://update-test3.com") is None


def test_full_data_flow(docker_setup, db_manager, monkeypatch):
    """전체 데이터 흐름 테스트 (URL 분석 → DB 저장 → 캐시)"""

    # AI 검증 부분만 모킹 (흐름만 테스트하기 위함)
    class MockModel:
        def predict(self, url):
            return {"result": True, "confidence": 0.97}

    class MockRequest:
        def __init__(self):
            self.app = type("", (), {})()
            self.app.state = type("", (), {})()
            self.app.state.model = MockModel()

    mock_request = MockRequest()

    test_url = "http://fullflow-test.com"
    assert db_manager.get_cached_result(test_url) is None

    session = db_manager.get_postgres_session()
    try:
        db_url = session.query(PhishingURL).filter(PhishingURL.url == test_url).first()
        assert db_url is None
    finally:
        session.close()

    # URL 분석 실행
    result = analyze(test_url, mock_request)

    # 결과 검증
    assert result.result is True
    assert result.confidence == 0.97

    # DB에 저장되었는지 확인
    session = db_manager.get_postgres_session()
    try:
        db_url = session.query(PhishingURL).filter(PhishingURL.url == test_url).first()
        assert db_url is not None
        assert db_url.is_phishing is True
        assert db_url.confidence == 0.97
    finally:
        session.close()

    # 캐시에 저장되었는지 확인
    cache_result = db_manager.get_cached_result(test_url)
    assert cache_result is not None
    assert cache_result["is_phishing"] is True
    assert cache_result["confidence"] == 0.97


def check_mongodb_auth():
    """MongoDB 인증 테스트"""
    try:
        client = pymongo.MongoClient(
            "mongodb://admin:password@localhost:27017/phishing_feedback?authSource=admin"
        )
        # 데이터베이스 액세스 테스트
        db_names = client.list_database_names()
        client.close()
        return True
    except Exception as e:
        print(f"MongoDB 연결 확인 실패: {e}")
        return False


@pytest.fixture(scope="session", autouse=True)
def check_mongo_before_tests(docker_setup):
    """모든 테스트 전에 MongoDB 연결 확인"""
    if not check_mongodb_auth():
        # Docker 컨테이너 로그 확인
        subprocess.run(["docker-compose", "logs", "mongodb"], check=False)
        pytest.fail("MongoDB 연결에 실패했습니다. Docker 컨테이너 로그를 확인하세요.")
