# --------------------------------------------------------------------------
# Main server application module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware

from qshing_server.core.config import settings
from qshing_server.api import api_router

app = FastAPI(
    title=settings.PROJECT_NAME,
)

if settings.all_cors_origins:
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.all_cors_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )



@app.get("/")
def read_root():
    return {"message": "Main page"}


app.include_router(api_router)
