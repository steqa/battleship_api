import bcrypt


def hash_password(password: str) -> bytes:
    salt = bcrypt.gensalt()
    return bcrypt.hashpw(password.encode(), salt)


def validate_password(password: str, hashed_password: bytes) -> bool:
    return bcrypt.checkpw(password.encode(), hashed_password)


def check_full_board_in_hits(board: str, hits: str) -> bool:
    for board_char, hits_char in zip(board, hits):
        if board_char == '1' and hits_char != '1':
            return False
    return True
