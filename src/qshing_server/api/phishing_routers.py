# --------------------------------------------------------------------------
# Phishing Detection API endpoints module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from . import APIRouter

router = APIRouter(prefix="/phishing-detection")


@router.get("/")
async def determine():
    """디버깅용 엔드포인트, 추후 제거"""
    return {"message": "Phshing site detection with url"}


@router.post("/analyze")
async def analyze():
    """피싱 사이트 판별 분석 엔드포인트"""
    # TODO: 분석 로직 구현
    return {"result": "phishing", "confidence": 0.95}
