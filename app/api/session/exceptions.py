from fastapi import WebSocketException, status


class BaseWebSocketException(WebSocketException):
    code = 4000
    reason = "Bad Request"

    def __init__(self):
        super().__init__(
            code=self.code,
            reason=self.reason
        )


class SessionAlreadyFull(BaseWebSocketException):
    code = status.HTTP_403_FORBIDDEN
    reason = "Session Already Full"


class JSONDecodeException(BaseWebSocketException):
    code = status.WS_1011_INTERNAL_ERROR
    reason = "JSON decode error"


class PlayerNotFound(BaseWebSocketException):
    code = status.WS_1003_UNSUPPORTED_DATA
    reason = "Player not found"
