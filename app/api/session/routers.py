from fastapi import APIRouter
import json
from fastapi import WebSocket, WebSocketDisconnect
from api.session.websocket_manager import manager

router = APIRouter(
    prefix="/api/v1/session",
    tags=["Session"],
)


@router.websocket('/ws/{session_name}/{session_password}')
async def websocket_endpoint(
        websocket: WebSocket,
        session_name: str,
        session_password: str
):
    session_id, player_id = await manager.connect(
        websocket,
        session_name,
        session_password
    )

    try:
        while True:
            data = await websocket.receive_text()
            message = json.loads(data)
    except WebSocketDisconnect:
        await manager.disconnect(session_id, player_id)
