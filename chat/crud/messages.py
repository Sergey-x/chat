import sqlalchemy as sa
from fastapi_pagination.ext.sqlalchemy import paginate
from models import ChatParticipant, Message, MessagesToParticipants
from schemas import CreateMessageRequestSchema, MessageResponseItem
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func


message_returning_keys: tuple = (
    "id",
    "text",
    "author_id",
    "chat_id",
    "is_available",
    "dt_created",
    "dt_updated",
)

message_returning: tuple = (
    Message.id,
    Message.text,
    Message.author_id,
    Message.chat_id,
    Message.is_available,
    Message.dt_created,
    Message.dt_updated,
)


class MessageCRUD:
    @classmethod
    async def add_message_to_chat(
            cls,
            db: AsyncSession,
            author_id: int,
            chat_id: int,
            message: CreateMessageRequestSchema,
    ) -> MessageResponseItem | None:
        """Добавить сообщение чата в таблицу."""
        insert_stmt = insert(Message) \
            .values(text=message.text,
                    author_id=author_id,
                    chat_id=chat_id) \
            .returning(*message_returning)

        try:
            res = (await db.execute(insert_stmt)).one()
            if res is not None:
                new_msg: MessageResponseItem = MessageResponseItem.parse_obj(dict(zip(message_returning_keys, res)))
                # Сообщение добавлено в чат - надо завести записи о статусе (прочитано или нет)
                # каждым пользователем в чате

                # вытаскиваем всех членов чата
                select_participant_ids = sa.select(ChatParticipant.participant_id) \
                    .where(ChatParticipant.chat_id == chat_id)
                participant_ids = (await db.execute(select_participant_ids)).scalars()

                # каждому члену создаем запись - сообщение не прочитано
                message_participants: list[MessagesToParticipants] = []
                for participant_id in participant_ids:
                    message_participants.append(
                        MessagesToParticipants(
                            message_id=new_msg.id,
                            participant_id=participant_id,
                            is_read=bool(participant_id == author_id),  # свое сообщение считается сразу же прочитанным
                            chat_id=chat_id,
                        )
                    )
                db.add_all(message_participants)

                # завершаем транзакцию
                await db.commit()
                return new_msg
            else:
                return None
        except OperationalError:
            return None

    @classmethod
    async def get_chat_messages(
            cls,
            chat_id: int,
            db: AsyncSession,
    ):
        """Получить сообщения чата с id = chat_id.

        Есть пагинация на уровне db.
        """
        select_stmt = sa.select(Message) \
            .where(sa.and_(
                Message.chat_id == chat_id,
                Message.is_available == True,  # noqa
            )) \
            .order_by(Message.dt_created)

        try:
            return await paginate(db, select_stmt)
        except OperationalError:
            return []

    @classmethod
    async def update_message(
            cls,
            author_id: int,
            message_id: int,
            message_text: str,
            db: AsyncSession,
    ) -> MessageResponseItem | None:
        update_stmt = sa.update(Message) \
            .values(text=message_text, dt_updated=func.current_timestamp()) \
            .where(sa.and_(Message.id == message_id, Message.author_id == author_id)) \
            .returning(*message_returning)

        try:
            res = (await db.execute(update_stmt)).one()
            if res:
                await db.commit()
                return MessageResponseItem.parse_obj(dict(zip(message_returning_keys, res)))
            else:
                return None
        except OperationalError:
            return None

    @classmethod
    async def delete_message(cls, db: AsyncSession, message_id: int, author_id: int) -> int:
        # только автор может удалить сообщение
        stmt = sa.update(Message) \
            .values(is_available=False) \
            .where(sa.and_(Message.id == message_id, Message.author_id == author_id))
        res = (await db.execute(stmt)).rowcount  # noqa
        await db.commit()
        return res
