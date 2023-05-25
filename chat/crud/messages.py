import sqlalchemy as sa
from fastapi_pagination.ext.sqlalchemy import paginate
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql import func

from chat.models import Message
from chat.schemas import AddMessageRequest


message_returning_keys: tuple = (
    "id",
    "text",
    "author_id",
    "dest_id",
    "is_available",
    "read",
    "dt_created",
    "dt_updated",
)

message_returning: tuple = (
    Message.id,
    Message.text,
    Message.author_id,
    Message.dest_id,
    Message.is_available,
    Message.read,
    Message.dt_created,
    Message.dt_updated,
)


class MessageCRUD:

    @classmethod
    async def get_messages(
            cls,
            author_id: int,
            dest_id: int,
            db: AsyncSession,
    ):
        select_stmt = sa.select(Message) \
            .where(
            sa.or_(
                sa.and_(Message.author_id == author_id, Message.dest_id == dest_id),
                sa.and_(Message.author_id == dest_id, Message.dest_id == author_id),
            )
        ).order_by(Message.dt_created)

        try:
            return await paginate(db, select_stmt)
        except OperationalError:
            return []

    @classmethod
    async def add_message(
            cls,
            author_id: int,
            message: AddMessageRequest,
            db: AsyncSession,
    ) -> object | None:
        insert_stmt = insert(Message) \
            .values(text=message.text,
                    author_id=author_id,
                    dest_id=message.dest_id) \
            .returning(*message_returning)

        try:
            res = (await db.execute(insert_stmt)).one()
            await db.commit()

            return dict(zip(message_returning_keys, res))
        except OperationalError:
            return None

    @classmethod
    async def update_message(
            cls,
            author_id: int,
            message_id: int,
            message_text: str,
            db: AsyncSession,
    ) -> object | None:
        update_stmt = sa.update(Message) \
            .values(text=message_text, dt_updated=func.current_timestamp()) \
            .where(sa.and_(Message.id == message_id, Message.author_id == author_id)) \
            .returning(*message_returning)

        try:
            res = (await db.execute(update_stmt)).one()
            await db.commit()

            return dict(zip(message_returning_keys, res))
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
