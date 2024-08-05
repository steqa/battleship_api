import json
import logging

from fastapi import APIRouter
from fastapi import WebSocket, WebSocketDisconnect

from api.session.exceptions import JSONDecodeException
from api.session.websocket_manager import manager

logger = logging.getLogger(__name__)

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
    await manager.send_player_id(session_id, player_id)
    await manager.send_enemies_id(session_id)

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug('Received data:\n%s', data)
            try:
                message = json.loads(data)
            except json.decoder.JSONDecodeError:
                logger.warning('Data is invalid JSON!')
                await manager.disconnect(session_id, player_id)
                raise JSONDecodeException

            if await manager.session_is_ready(session_id):
                await manager.send_message_to_enemy(session_id, player_id, message)
    except WebSocketDisconnect:
        await manager.disconnect(session_id, player_id)
