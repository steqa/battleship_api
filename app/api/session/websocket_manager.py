import logging
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from api.session import services
from api.session.exceptions import (
    WsPlayerNotFound
)
from api.session.models import player
from api.session.schemas import (
    Entities
)
from api.session.websocket_request_types import WsRequestType
from api.session.websocket_response_types import WsResponseType
from api.session.websocket_utils import (
    ws_receive_player_start_session_message,
    ws_receive_message
)

logger = logging.getLogger(__name__)


class Player:
    __slots__ = ('websocket', 'enemy_joined', 'is_ready')

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        self.enemy_joined = False
        self.is_ready = False


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[UUID, Player] = {}

    async def connect(self, websocket: WebSocket, player_id: UUID):
        await websocket.accept()
        self.active_connections[player_id] = Player(websocket)
        logger.debug('Websocket connected, player_id: %s', player_id)

    async def disconnect(self, player_id: UUID):
        connection = self.active_connections.pop(player_id, None)
        if connection:
            if connection.websocket.client_state != WebSocketState.DISCONNECTED:
                await connection.websocket.close()
            logger.debug('Websocket disconnected, player_id: %s', player_id)

    async def login_session(
            self,
            websocket: WebSocket,
            player_id: UUID,
            session_id: UUID
    ) -> player:
        enemy = await services.get_enemy(player_id, session_id)
        while True:
            if enemy is not None and enemy.id in self.active_connections:
                await self.send_enemy_joined_message(to_id=player_id)
                await self.send_enemy_joined_message(to_id=enemy.id)
                self.active_connections[player_id].enemy_joined = True
                self.active_connections[enemy.id].enemy_joined = True
                await ws_receive_player_start_session_message(websocket)
                await self.send_start_session_message(to_id=player_id)
                logger.debug('Session start, player_id: %s', player_id)
                return enemy
            else:
                await ws_receive_player_start_session_message(websocket)
                if self.active_connections[player_id].enemy_joined:
                    enemy = await services.get_enemy(player_id, session_id)
                    await self.send_start_session_message(to_id=player_id)
                    logger.debug('Session start, player_id: %s', player_id)
                    return enemy

    async def start_game(
            self,
            websocket: WebSocket,
            player_id: UUID,
            enemy_id: UUID
    ) -> None:
        logger.debug('Player is ready, player_id: %s', player_id)
        self.active_connections[player_id].is_ready = True
        enemy_is_ready = self.active_connections[enemy_id].is_ready
        if enemy_is_ready:
            await self.send_enemy_placement_ready_message(player_id)
            await self.send_enemy_placement_ready_message(enemy_id)
        #     TODO: добавить поле типо очереди и рандомно выдавать одному True, другому False

        while True:
            message = await ws_receive_message(websocket)
            enemy_is_ready = self.active_connections[enemy_id].is_ready
            if message.type == WsResponseType.PLAYER_START_GAME and enemy_is_ready:
                await self.send_start_game_message(player_id)
                logger.debug('Game start, player_id: %s', player_id)
                return
            elif message.type == WsResponseType.PLAYER_PLACEMENT_NOT_READY and not enemy_is_ready:
                logger.debug('Player is not ready, player_id: %s', player_id)
                self.active_connections[player_id].is_ready = False
                break

    async def send_enemy_joined_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.ENEMY_JOINED)

    async def send_enemy_left_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.ENEMY_LEFT)

    async def send_start_session_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.START_SESSION)

    async def send_enemy_placement_ready_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.ENEMY_PLACEMENT_READY)

    async def send_start_game_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, WsRequestType.START_GAME)

    async def send_player_entities_message(
            self,
            to_id: UUID,
            entities: Entities
    ) -> None:
        detail = entities.to_dict()
        await self.__send_message(to_id, WsRequestType.ENEMY_ENTITIES, detail)

    async def __send_message(
            self,
            player_id: UUID,
            message_type: WsRequestType,
            detail: dict | str | None = None
    ) -> None:
        if player_id not in self.active_connections:
            logger.warning('Player for message not found, player_id: %s', player_id)
            raise WsPlayerNotFound
        connection = self.active_connections[player_id].websocket
        if connection.client_state == WebSocketState.CONNECTED:
            if detail is None:
                detail = {}
            message = {"type": message_type, "detail": detail}
            await connection.send_json(message)
            logger.debug('Message sent to player, player_id: %s, message: %s', player_id, message)
        else:
            logger.warning('Cannot send message to disconnected websocket, player_id: %s', player_id)


manager = ConnectionManager()
