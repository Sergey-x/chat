import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from .base import BaseTable


CHAT_TABLE_NAME: str = 'chats'


class Chat(BaseTable):
    __tablename__ = CHAT_TABLE_NAME

    dt_created = sa.Column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        doc="Date and time of create (type TIMESTAMP)",
    )

    dt_updated = sa.Column(
        TIMESTAMP(timezone=True),
        server_default=func.current_timestamp(),
        nullable=False,
        doc="Date and time of last updating (type TIMESTAMP)",
    )

    name = sa.Column(
        sa.Text,
        nullable=True,
        doc='Название чата',
    )

    admin_id = sa.Column(
        sa.Integer,
        nullable=True,
        doc='Создатель чата, используется только если is_private=False',
    )

    is_private = sa.Column(
        sa.Boolean,
        default=True,
        doc='Если is_private=True, то это переписка между 2-мя людьми',
    )

    participants = relationship("ChatParticipant", back_populates="parent", lazy="selectin")
