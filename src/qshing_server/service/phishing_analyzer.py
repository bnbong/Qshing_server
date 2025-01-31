# --------------------------------------------------------------------------
# Phishing CRUD module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
import logging
from typing import Any, Optional, Type

from fastapi import Request

from src.qshing_server.core.config import settings
from src.qshing_server.dto.phishing_schema import PhishingDetectionResponse

logger = logging.getLogger("main")


def analyze(
    url: str,
    request: Request,
    response_model: Type[PhishingDetectionResponse] = PhishingDetectionResponse,
) -> Optional[Any]:
    logger.info(f"Analyzing URL: {url}")
    detector = request.app.state.model
    result = detector.predict(url)

    if result["confidence"] is not None:
        logger.info(f"Analysis completed for URL: {url}")
        return response_model.model_validate(result)
    else:
        logger.error(f"Failed to analyze URL: {url}")
        return response_model.model_validate({"result": False, "confidence": 0.0})
