from enum import StrEnum


class WsRequestType(StrEnum):
    ENEMY_JOINED = 'EnemyJoined'
    ENEMY_LEFT = 'EnemyLeft'
    START_SESSION = 'StartSession'
    ENEMY_PLACEMENT_READY = 'EnemyPlacementReady'
    START_GAME = 'StartGame'
    ENEMY_ENTITIES = 'EnemyEntities'
    YOUR_TURN = 'YourTurn'
    PLAYER_HIT = 'PlayerHit'
    ENEMY_HIT = 'EnemyHit'
    WIN = 'Win'
    DEFEAT = 'Defeat'
