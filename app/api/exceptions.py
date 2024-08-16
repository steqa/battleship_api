from fastapi import WebSocketException, status, HTTPException


class BaseHTTPException(HTTPException):
    status_code = status.HTTP_400_BAD_REQUEST
    detail = "Bad Request"

    def __init__(self):
        super().__init__(
            status_code=self.status_code,
            detail=self.detail
        )


class BaseWebSocketException(WebSocketException):
    code = 4000
    reason = "Bad Request"

    def __init__(self):
        super().__init__(
            code=self.code,
            reason=self.reason
        )
