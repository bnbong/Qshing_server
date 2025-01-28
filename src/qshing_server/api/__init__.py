from fastapi import APIRouter

from .phishing_routers import router as determine_router

api_router = APIRouter()

api_router.include_router(determine_router)
