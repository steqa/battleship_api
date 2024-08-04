from uuid import UUID


def player_id_message(player_id: UUID) -> dict:
    return {'player_id': str(player_id)}


def enemy_id_message(enemy_id: UUID) -> dict:
    return {'enemy_id': str(enemy_id)}


def enemy_left_message() -> dict:
    return {'detail': 'Enemy left'}