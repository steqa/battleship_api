from uuid import UUID


def player_id_message(player_id: UUID) -> dict:
    return {
        'type': 'player_id',
        'detail': {
            'player_id': str(player_id)
        }
    }


def enemy_id_message(enemy_id: UUID) -> dict:
    return {
        'type': 'enemy_id',
        'detail': {
            'enemy_id': str(enemy_id)
        }
    }


def enemy_left_message() -> dict:
    return {'type': 'enemy_left'}


def game_is_ready() -> dict:
    return {'type': 'game_ready'}
