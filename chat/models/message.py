import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.sql import func

from .base import BaseTable


MESSAGES_TABLE_NAME: str = 'messages'


class Message(BaseTable):
    __tablename__ = MESSAGES_TABLE_NAME

    dt_created = sa.Column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        doc="Date and time of create (type TIMESTAMP)",
    )

    dt_updated = sa.Column(
        TIMESTAMP(timezone=True),
        nullable=True,
        doc="Date and time of update (type TIMESTAMP)",
    )

    text = sa.Column(
        sa.Text,
        doc='Текст сообщения',
    )

    is_available = sa.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        doc='Удалено автором или нет',
    )

    author_id = sa.Column(
        sa.Integer,
    )

    dest_id = sa.Column(
        sa.Integer,
    )

    read = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        doc='Прочитано сообщение получателем или нет',
    )
