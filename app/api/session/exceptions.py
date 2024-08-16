from fastapi import status

from api.exceptions import BaseHTTPException, BaseWebSocketException


class HttpSessionNotFound(BaseHTTPException):
    status_code = status.HTTP_404_NOT_FOUND
    detail = "Session not found"


class HttpSessionAlreadyExists(BaseHTTPException):
    status_code = status.HTTP_409_CONFLICT
    detail = "Session already exists"


class HttpSessionAlreadyFull(BaseHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Session Already Full"


class HttpInvalidPassword(BaseHTTPException):
    status_code = status.HTTP_403_FORBIDDEN
    detail = "Invalid password"


class HttpInvalidNameLength(BaseHTTPException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Name must be at least 1 character"


class HttpInvalidPasswordLength(BaseHTTPException):
    status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
    detail = "Password must be at least 1 character"


class WsPlayerNotFound(BaseWebSocketException):
    code = status.WS_1003_UNSUPPORTED_DATA
    reason = "Player not found"


class WsSessionNotFound(BaseWebSocketException):
    code = status.WS_1003_UNSUPPORTED_DATA
    reason = "Session not found"


class WsJsonDecodeException(BaseWebSocketException):
    code = status.WS_1011_INTERNAL_ERROR
    reason = "JSON decode error"


class WsInvalidJsonFormat(BaseWebSocketException):
    code = status.WS_1011_INTERNAL_ERROR
    reason = "Invalid JSON format"


class WsEnemyNotFound(BaseWebSocketException):
    code = status.WS_1011_INTERNAL_ERROR
    reason = "Enemy not found"
