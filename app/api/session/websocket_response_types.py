from enum import StrEnum


class WsResponseType(StrEnum):
    PLAYER_START_SESSION = 'PlayerStartSession'
    PLAYER_PLACEMENT_READY = 'PlayerPlacementReady'
    PLAYER_PLACEMENT_NOT_READY = 'PlayerPlacementNotReady'
    PLAYER_START_GAME = 'PlayerStartGame'
    HIT = 'Hit'

