# --------------------------------------------------------------------------
# Health check router module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime
from typing import Dict

from fastapi import APIRouter, HTTPException, Request, status

router = APIRouter()


@router.get("/health")
def health_check(request: Request) -> Dict[str, str]:
    """
    헬스체크 엔드포인트
    쿠버네티스 liveness 프로브에서 사용
    """
    try:
        status_checks = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "service": "qshing-server",
        }

        # AI 모델 로드 상태 확인
        if hasattr(request.app.state, "model") and request.app.state.model is not None:
            status_checks["model"] = "loaded"
        else:
            status_checks["model"] = "not_loaded"
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI model not loaded"
            )

        return status_checks

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Health check failed: {str(e)}"
        )


@router.get("/ready")
def readiness_check(request: Request) -> Dict[str, str]:
    """
    준비 상태 확인 엔드포인트
    쿠버네티스 readiness 프로브에서 사용
    """
    try:
        checks = {
            "status": "ready",
            "timestamp": datetime.now().isoformat(),
        }

        # AI 모델 확인
        if not (hasattr(request.app.state, "model") and request.app.state.model is not None):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="AI model not ready"
            )

        # DB 매니저 확인
        if not (hasattr(request.app.state, "db_manager") and request.app.state.db_manager is not None):
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Database manager not ready"
            )

        return checks

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Readiness check failed: {str(e)}"
        ) 