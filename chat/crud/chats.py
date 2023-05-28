import sqlalchemy as sa
from models import Chat, ChatParticipant
from schemas import ChatResponseItem, UpdateChatRequestSchema
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession


chat_returning_keys: tuple = (
    "id",
    "dt_created",
    "dt_updated",
    "admin_id",
    "name",
    "is_private",
)

chat_returning: tuple = (
    Chat.id,
    Chat.dt_created,
    Chat.dt_updated,
    Chat.admin_id,
    Chat.name,
    Chat.is_private,
)


class ChatCRUD:
    @classmethod
    async def get_chats(
            cls,
            participant_id: int,
            db: AsyncSession,
    ) -> list[dict]:
        chat_ids_subquery = sa.select(ChatParticipant.chat_id).where(
            sa.and_(
                ChatParticipant.is_available == True,  # noqa
                ChatParticipant.participant_id == participant_id,
            )
        )

        select_stmt = sa.select(*chat_returning) \
            .filter(Chat.id.in_(chat_ids_subquery)) \
            .order_by(Chat.dt_updated)

        try:
            res = (await db.execute(select_stmt)).all()
            return [dict(zip(chat_returning_keys, row)) for row in res]
        except OperationalError:
            return []

    @classmethod
    async def create_chat(
            cls,
            db: AsyncSession,
            participant_ids: list[int],
            is_private: bool,
            chat_name: str | None = None,
            admin_id: int | None = None,
    ) -> ChatResponseItem | None:
        chat_insert_stmt = sa.insert(Chat) \
            .values(name=chat_name, admin_id=admin_id, is_private=is_private) \
            .returning(*chat_returning)

        try:
            res = (await db.execute(chat_insert_stmt)).one()
            if res:
                new_chat_id: int = res[0]
                chat_participants: list[ChatParticipant] = []
                for participant_id in participant_ids:
                    chat_participants.append(ChatParticipant(chat_id=new_chat_id, participant_id=participant_id))
                db.add_all(chat_participants)
                await db.commit()
                return ChatResponseItem.parse_obj(dict(zip(chat_returning_keys, res)))
            else:
                return None
        except OperationalError:
            return None

    @classmethod
    async def update_chat(
            cls,
            chat: UpdateChatRequestSchema,
            chat_id: int,
            user_id: int,
            db: AsyncSession,
    ):
        raw_query = sa.text(
            """
            UPDATE :chat_table
            SET name = :chat_name
            WHERE
                id = :chat_id AND
                :user_id IN (
                    SELECT participant_id
                    FROM chat_participants
                    WHERE chat_id = :chat_id
                )
            RETURNING *;
            """
        )
        query = raw_query.bindparams(
            chat_name=chat.name,
            user_id=user_id,
            chat_id=chat_id,
            chat_table=Chat.__tablename__,
        )
        try:
            res = (await db.execute(query)).fetchone()
            await db.commit()
            if res:
                return dict(zip(chat_returning_keys, res))
            return res
        except OperationalError:
            return None

    @classmethod
    async def change_participant_status_in_status(
            cls,
            db: AsyncSession,
            chat_id: int,
            participant_id: int,
            new_status: bool,
    ) -> int:
        stmt = sa.update(ChatParticipant) \
            .values(is_available=new_status) \
            .where(sa.and_(chat_id == chat_id, participant_id == participant_id))
        res = (await db.execute(stmt)).rowcount  # noqa
        await db.commit()
        return res

    @classmethod
    async def check_user_in_chat(
            cls,
            db: AsyncSession,
            chat_id: int,
            participant_id: int,
    ) -> bool:
        """Проверить, что пользователь (participant_id) является членом чата chat_id."""
        check_user_stmt = sa.select(ChatParticipant.participant_id).where(
            sa.and_(
                ChatParticipant.chat_id == chat_id,
                ChatParticipant.participant_id == participant_id,
            )
        )

        res = (await db.execute(check_user_stmt)).fetchone()
        return bool(res)
