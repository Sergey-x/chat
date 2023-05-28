import sqlalchemy as sa
from db import DeclarativeBase
from sqlalchemy.orm import relationship

from . import Chat


CHAT_PARTICIPANTS_TABLE_NAME: str = 'chat_participants'


class ChatParticipant(DeclarativeBase):
    __tablename__ = CHAT_PARTICIPANTS_TABLE_NAME

    is_available = sa.Column(
        sa.Boolean,
        nullable=False,
        default=True,
        doc='Удален чат этим собеседником или нет',
    )

    chat_id = sa.Column(sa.ForeignKey(Chat.id), primary_key=True)  # noqa
    parent = relationship("Chat", back_populates="participants")

    participant_id = sa.Column(
        sa.Integer,
        primary_key=True,
        nullable=False,
        doc='Идентификатор пользователя',
    )
