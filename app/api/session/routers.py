import logging
from uuid import UUID

from fastapi import APIRouter
from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

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
)
from api.session.utils import validate_password
from api.session.websocket_manager import manager

logger = logging.getLogger(__name__)

router = APIRouter(
    prefix="/api/v1/session",
    tags=["Session"],
)


@router.get('', response_model=list[Session])
async def get_sessions():
    sessions = await services.get_sessions(desc_sort=True)
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
    logger.debug('Player created in database, session_id: %s', session.id)
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
    logger.debug('Player created in database, session_id: %s', session.id)

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
        enemy = await manager.login_session(websocket, player_id, session.id)

    except WebSocketDisconnect:
        await manager.disconnect(player.id)
        enemy = await services.get_enemy(player_id=player.id, session_id=session.id)
        await services.delete_player(player.id)
        logger.debug('Player deleted from database, player_id: %s', player.id)
        if enemy is not None:
            if enemy.id in manager.active_connections:
                await manager.send_enemy_left_message(enemy.id)
                await manager.disconnect(enemy.id)
        else:
            await services.delete_session(session.id)
            logger.debug('Session deleted from database, player_id: %s', player.id)
