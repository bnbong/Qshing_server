# --------------------------------------------------------------------------
# API module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from datetime import datetime

from fastapi import APIRouter

from src.qshing_server.dto.base import ResponseSchema

from . import deps
from .phishing_routers import router as phishing_router

api_router = APIRouter()

api_router.include_router(phishing_router)
