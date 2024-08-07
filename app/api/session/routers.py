import json
import logging

from fastapi import APIRouter
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from api.session import services, redis_services
from api.session.exceptions import JSONDecodeException
from api.session.response_types import ResponseType
from api.session.schemas import ResponseModel, ReadyResponse
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
    if await manager.session_is_ready(session_id):
        await manager.send_enemies_id(session_id)

    try:
        while True:
            data = await websocket.receive_text()
            logger.debug('Received data:\n%s', data)
            try:
                message = json.loads(data)
                response = ResponseModel(**message)
            except json.decoder.JSONDecodeError:
                logger.warning('Data is invalid JSON!')
                await manager.disconnect(session_id, player_id)
                raise JSONDecodeException

            if response.type == ResponseType.ready.value:
                logger.debug('Player ready, player_id: %s', player_id)
                detail = ReadyResponse(**response.detail)
                await redis_services.set_player_data(
                    session_id, player_id, detail.board, detail.entities
                )
                logger.info('Player data added to redis, session_id: %s, player1_id: %s', session_id, player_id)
                session = await services.get_session(uuid=session_id)
                if session and session.player1_id == player_id:
                    session = await services.update_session(session_id, new_player1_ready=True)
                elif session.player2_id == player_id:
                    session = await services.update_session(session_id, new_player2_ready=True)

                if session.player1_ready and session.player2_ready:
                    await manager.send_game_is_ready(session_id)
                    logger.debug('Game ready, session_id: %s', session_id)
    except WebSocketDisconnect:
        await manager.disconnect(session_id, player_id)
    except:
        await services.delete_session(session_id)
        logger.info('Session deleted from database.')
        await manager.delete_connections(session_id)
        logger.debug('Connections cleared.')
        await redis_services.delete_session(session_id)
        logger.info('Session deleted from redis.')
