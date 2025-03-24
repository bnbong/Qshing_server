# --------------------------------------------------------------------------
# API 의존성 관리 모듈
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from typing import Generator

from fastapi import Depends

from src.qshing_server.db.db_manager import DBManager


def get_db_manager() -> DBManager:
    """
    API에서 사용할 DB 매니저 인스턴스 제공
    """
    return DBManager()


def get_db():
    """
    API에서 사용할 PostgreSQL 세션 제공
    """
    db_manager = get_db_manager()
    db = db_manager.get_postgres_session()
    try:
        yield db
    finally:
        db.close()
