from sqlalchemy import (
    Column,
    String,
    UUID,
    text,
    ForeignKey,
    Boolean,
    DateTime,
    Table
)
from sqlalchemy.dialects.postgresql import BYTEA

from api.database import metadata

session = Table(
    'session', metadata,
    Column('id', UUID, primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
    Column('name', String, unique=True, nullable=False),
    Column('password', BYTEA, nullable=False),
    Column('is_ready', Boolean, nullable=False, server_default=text("false")),
    Column('created_at', DateTime, nullable=False, server_default=text("now()")),
)


player = Table(
    'player', metadata,
    Column('id', UUID, primary_key=True, nullable=False, server_default=text("gen_random_uuid()")),
    Column('session_id', ForeignKey('session.id'), nullable=False),
)
