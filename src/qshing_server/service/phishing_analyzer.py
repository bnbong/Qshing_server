# --------------------------------------------------------------------------
# Phishing CRUD module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from typing import Type, Optional, Any
from fastapi import Request
import logging

from src.qshing_server.dto.phishing_schema import PhishingDetectionResponse
from src.qshing_server.core.config import settings

logger = logging.getLogger("main")


def analyze(
    url: str,
    request: Request,
    response_model: Type[PhishingDetectionResponse] = PhishingDetectionResponse,
) -> Optional[Any]:
    logger.info(f"Analyzing URL: {url}")
    model = request.app.state.model
    result = model.predict(url)
    logger.info(f"Analysis completed for URL: {url}")
    return response_model.model_validate(result.__dict__)
