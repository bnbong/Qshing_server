#!/usr/bin/env python
import asyncio
import os
import sys

# 프로젝트 루트를 sys.path에 추가
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import motor.motor_asyncio
from beanie import init_beanie
from sqlmodel import SQLModel, create_engine

from src.qshing_server.core.config import settings
from src.qshing_server.db.models import PhishingURL, UserFeedback


async def init_mongodb():
    """MongoDB Beanie 초기화"""
    print(f"MongoDB 연결 중... {settings.MONGODB_HOST}:{settings.MONGODB_PORT}")
    client = motor.motor_asyncio.AsyncIOMotorClient(settings.MONGODB_URI)

    try:
        server_info = await client.admin.command("serverStatus")
        print(f"MongoDB 서버 버전: {server_info.get('version', 'unknown')}")

        # Beanie 초기화
        await init_beanie(
            database=client[settings.MONGODB_NAME], document_models=[UserFeedback]
        )
        print(f"MongoDB 컬렉션 초기화 완료: {settings.MONGODB_NAME}")
        return True
    except Exception as e:
        print(f"MongoDB 연결 실패: {e}")
        return False
    finally:
        client.close()


def init_postgres():
    """PostgreSQL 초기화"""
    print(f"PostgreSQL 연결 중... {settings.POSTGRES_HOST}:{settings.POSTGRES_PORT}")
    try:
        engine = create_engine(str(settings.POSTGRES_URI))

        SQLModel.metadata.create_all(engine)
        print("PostgreSQL 테이블 생성 완료")
        return True
    except Exception as e:
        print(f"PostgreSQL 연결 실패: {e}")
        return False


async def main():
    """데이터베이스 초기화 메인 함수"""
    print("데이터베이스 초기화 시작...")

    postgres_success = init_postgres()

    mongodb_success = await init_mongodb()

    if postgres_success and mongodb_success:
        print("모든 데이터베이스 초기화 완료!")
        return 0
    else:
        print("일부 데이터베이스 초기화 실패!")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)
