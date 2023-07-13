from enum import Enum
from typing import Optional


class TapoError(Enum):
    ERR_AES_DECODE_FAIL = -1005
    ERR_REQUEST_LEN_ERROR = -1006
    ERR_CLOUD_FAILED = -1007
    ERR_PARAMS = -1008
    ERR_SESSION_PARAM = -1101
    INVALID_PUBLIC_KEY = -1010
    INVALID_CREDENTIAL = -1501
    INVALID_REQUEST = -1002
    INVALID_JSON = -1003
    ERR_NULL_TRANSPORT = 1000
    ERR_CMD_COMMAND_CANCEL = 1001
    ERR_TRANSPORT_NOT_AVAILABLE = 1002
    ERR_HAND_SHAKE_FAILED = 1100
    ERR_LOGIN_FAILED = 1111
    ERR_HTTP_TRANSPORT_FAILED = 1112
    ERR_MULTI_REQUEST_FAILED = 1200
    ERR_SESSION_TIMEOUT = 9999


_error_message = {
    TapoError.INVALID_PUBLIC_KEY: "Invalid Public Key Length",
    TapoError.INVALID_CREDENTIAL: "Invalid credentials",
    TapoError.INVALID_REQUEST: "Invalid request",
    TapoError.INVALID_JSON: "Malformed json request",
    TapoError.ERR_AES_DECODE_FAIL: "AES Decode Fail",
    TapoError.ERR_REQUEST_LEN_ERROR: "Request length error",
    TapoError.ERR_PARAMS: "Request params error",
    TapoError.ERR_SESSION_PARAM: "Session params error",
    TapoError.ERR_NULL_TRANSPORT: "Null transport error",
    TapoError.ERR_CMD_COMMAND_CANCEL: "Command cancel error",
    TapoError.ERR_TRANSPORT_NOT_AVAILABLE: "Transport not available error",
    TapoError.ERR_HAND_SHAKE_FAILED: "Handshake failed",
    TapoError.ERR_LOGIN_FAILED: "Login failed",
    TapoError.ERR_HTTP_TRANSPORT_FAILED: "Http transport error",
    TapoError.ERR_MULTI_REQUEST_FAILED: "Multirequest failed",
    TapoError.ERR_SESSION_TIMEOUT: "Session Timeout"
}


class TapoException(Exception):
    error_code: int

    @staticmethod
    def from_error_code(error_code, msg: Optional[str]):
        try:
            tapo_error = TapoError(error_code)
            return TapoException(error_code, f"Returned error_code: {tapo_error}: {_error_message[tapo_error]}")
        except ValueError:
            return TapoException(error_code, f"Returned unknown error_code: {error_code}  msg: {msg}")

    def __init__(self, error_code, msg):
        super(TapoException, self).__init__(msg)
        self.error_code = error_code
