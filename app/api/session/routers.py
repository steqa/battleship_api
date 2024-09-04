import logging
from uuid import UUID

from fastapi import APIRouter
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from api.session import redis_services
from api.session import services
from api.session.exceptions import (
    WsPlayerNotFound,
    WsSessionNotFound,
    HttpSessionNotFound,
    HttpInvalidPassword,
    HttpSessionAlreadyExists,
    HttpSessionAlreadyFull
)
from api.session.schemas import (
    SessionCreate,
    PlayerIDResponse,
    Session,
    SessionLogin,
    Entities
)
from api.session.utils import validate_password
from api.session.websocket_manager import manager
from api.session.websocket_utils import (
    ws_receive_player_placement_ready_message
)

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/session",
    tags=["Session"],
)


@router.get('', response_model=list[Session])
async def get_sessions():
    sessions = await services.get_sessions(is_ready=False, desc_sort=True)
    return sessions


@router.post('/create', response_model=PlayerIDResponse)
async def create_session(session_request: SessionCreate):
    session = await services.get_session(name=session_request.name)
    if session is not None:
        logger.warning('Session already exists, session_name: %s', session_request.name)
        raise HttpSessionAlreadyExists

    session = await services.create_session(
        name=session_request.name,
        password=session_request.password
    )
    logger.debug('Session created in database, session_id: %s', session.id)
    player = await services.create_player(session.id)
    logger.debug('Player created in database, session_id: %s', player.id)
    return PlayerIDResponse(player_id=player.id)


@router.post('/login')
async def login_session(session_request: SessionLogin):
    session = await services.get_session(name=session_request.name)
    if session is None:
        logger.warning('Session not found in database, session_name: %s', session_request.name)
        raise HttpSessionNotFound

    if session.is_ready:
        raise HttpSessionAlreadyFull

    correct_password = session.password
    if not validate_password(session_request.password, correct_password):
        logger.info('Session login failed, session_id: %s', session.id)
        raise HttpInvalidPassword

    player = await services.create_player(session.id)
    logger.debug('Player created in database, player_id: %s', player.id)

    if not session.is_ready:
        await services.update_session(session.id, is_ready=True)
        logger.debug('Session updated (is_ready=True) in database, session_id: %s', session.id)
    return PlayerIDResponse(player_id=player.id)


@router.websocket('/ws')
async def websocket_connect_player(websocket: WebSocket, player_id: UUID):
    player = await services.get_player(player_id)
    if player is None:
        logger.warning('Player not found in database, player_id: %s', player_id)
        raise WsPlayerNotFound

    session = await services.get_session(player.session_id)
    if session is None:
        logger.warning('Session not found in database, player_id: %s', player_id)
        raise WsSessionNotFound

    await manager.connect(websocket, player_id)
    try:
        await manager.login_session(websocket, session_id=session.id, player_id=player.id)
        enemy = await services.get_enemy(player_id, session.id)
        while True:
            placement = await ws_receive_player_placement_ready_message(websocket)
            start = await manager.start_game(websocket, player_id, enemy.id)
            if start:
                break
        await redis_services.set_player_data(
            session.id, player_id, placement.board, placement.entities
        )
        logger.info('Player placement added to redis, session_id: %s, player_id: %s', session.id, player_id)
        await manager.send_player_entities_message(enemy.id, Entities(entities=placement.entities))
        while True:
            await manager.handle_hit(websocket, session.id, player_id, enemy.id)

    except WebSocketDisconnect:
        await manager.disconnect(player.id)

        await services.delete_player(player.id)
        logger.debug('Player deleted from database, player_id: %s', player.id)

        enemy = await services.get_enemy(player_id=player.id, session_id=session.id)
        if enemy is not None:
            await manager.send_enemy_left_message(to_id=enemy.id)
        else:
            session = await services.get_session(uuid=player.session_id)
            if session is not None:
                await services.delete_session(session.id)
                logger.debug('Session deleted from database, session_id: %s', session.id)
                await redis_services.delete_session(session.id)
                logger.debug('Session deleted from redis, session_id: %s', session.id)
