import logging
from uuid import UUID

from fastapi import WebSocket
from starlette.websockets import WebSocketState

from api.session import services
from api.session.exceptions import (
    WsPlayerNotFound
)
from api.session.models import player
from api.session.websocket_messages import (
    start_game_message,
    enemy_left_message,
    enemy_joined_message
)
from api.session.websocket_utils import ws_receive_player_start_game_message

logger = logging.getLogger(__name__)


class Player:
    __slots__ = ('websocket', 'enemy_joined')

    def __init__(self, websocket: WebSocket) -> None:
        self.websocket = websocket
        self.enemy_joined = False


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
            self, websocket: WebSocket,
            player_id: UUID,
            session_id: UUID
    ) -> player:
        enemy = await services.get_enemy(player_id, session_id)
        while True:
            if enemy is not None and enemy.id in self.active_connections:
                await self.send_enemy_joined_message(to_id=player_id)
                await self.send_enemy_joined_message(to_id=enemy.id)
                self.update_enemy_joined(player_id, True)
                self.update_enemy_joined(enemy.id, True)
                await ws_receive_player_start_game_message(websocket)
                await self.send_start_game_message(to_id=player_id)
                logger.debug('Session start, player_id: %s', player_id)
                return enemy
            else:
                await ws_receive_player_start_game_message(websocket)
                if self.enemy_joined(player_id):
                    enemy = await services.get_enemy(player_id, session_id)
                    await self.send_start_game_message(to_id=player_id)
                    logger.debug('Session start, player_id: %s', player_id)
                    return enemy

    def enemy_joined(self, player_id: UUID) -> bool:
        if player_id in self.active_connections:
            return self.active_connections[player_id].enemy_joined
        else:
            return False

    def update_enemy_joined(self, player_id: UUID, status: bool) -> None:
        if player_id in self.active_connections:
            self.active_connections[player_id].enemy_joined = status

    async def send_enemy_joined_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, enemy_joined_message())

    async def send_enemy_left_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, enemy_left_message())

    async def send_start_game_message(self, to_id: UUID) -> None:
        await self.__send_message(to_id, start_game_message())

    async def __send_message(self, player_id: UUID, message: dict) -> None:
        if player_id not in self.active_connections:
            logger.warning('Player for message not found, player_id: %s', player_id)
            raise WsPlayerNotFound
        connection = self.active_connections[player_id].websocket
        if connection.client_state == WebSocketState.CONNECTED:
            await connection.send_json(message)
            logger.debug('Message sent to player, player_id: %s, message: %s', player_id, message)
        else:
            logger.warning('Cannot send message to disconnected websocket, player_id: %s', player_id)


manager = ConnectionManager()
