# --------------------------------------------------------------------------
# API Router module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime

from fastapi import APIRouter

from src.qshing_server.dto.base import ResponseSchema

from .phishing_routers import router as determine_router

api_router = APIRouter()


@api_router.get("/health", tags=["health"])
async def health_check():
    """
    서버 상태를 확인하는 health check 엔드포인트
    """
    response = ResponseSchema(
        timestamp=datetime.now().isoformat(),
        message="SUCCESS",
        data={"status": "ok", "message": "Server is running"},
    )
    return response


api_router.include_router(determine_router)
