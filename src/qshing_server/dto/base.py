# --------------------------------------------------------------------------
# Base DTO module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from typing import Generic, TypeVar

from pydantic import BaseModel, Field

from src.qshing_server.utils.enums import ResponseMessage

T = TypeVar("T")


class ResponseSchema(BaseModel, Generic[T]):
    timestamp: str = Field(..., description="응답이 생성 된 시간")
    message: str = Field(..., description="응답 결과 한 줄 메시지")
    data: T = Field(..., description="응답 데이터")
