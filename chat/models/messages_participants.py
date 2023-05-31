import sqlalchemy as sa
from db import DeclarativeBase

from .chat import Chat
from .message import Message


MESSAGES_PARTICIPANTS_TABLE_NAME: str = 'messages_participants'


class MessagesToParticipants(DeclarativeBase):
    __tablename__ = MESSAGES_PARTICIPANTS_TABLE_NAME

    is_read = sa.Column(
        sa.Boolean,
        nullable=False,
        default=False,
        doc='Статус прочтения сообщения пользователем',
    )
    message_id = sa.Column(sa.ForeignKey(Message.id), primary_key=True)  # noqa
    chat_id = sa.Column(sa.ForeignKey(Chat.id))  # noqa

    participant_id = sa.Column(
        sa.Integer,
        primary_key=True,
        nullable=False,
        doc='Идентификатор пользователя',
    )
