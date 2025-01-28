# --------------------------------------------------------------------------
# Enums module
#
# @author bnbong bbbong9@gmail.com
# --------------------------------------------------------------------------
from enum import Enum


class ResponseMessage(str, Enum):
    """응답 메시지 Enum

    - SUCCESS : 성공적으로 응답을 받은 경우
    - ERROR : 에러가 발생한 경우 (Internal Server Error, Bad Request 등)
    """

    SUCCESS = "SUCCESS"
    ERROR = "ERROR"

