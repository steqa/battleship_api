def enemy_joined_message() -> dict:
    return {
        'type': 'EnemyJoined',
        'detail': {'msg': 'Enemy is ready'}
    }


def enemy_left_message() -> dict:
    return {
        'type': 'EnemyLeft',
        'detail': {'msg': 'Enemy left'}
    }


def start_game_message() -> dict:
    return {
        'type': 'StartGame',
        'detail': {'msg': 'Game started'}
    }
