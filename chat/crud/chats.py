import sqlalchemy as sa
from models import Chat, ChatParticipant, Message, MessagesToParticipants
from schemas import ChatResponseItem, UpdateChatRequestSchema
from schemas.chats.response import NEW_MESSAGE_COUNT, GetFullChatResponse
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.sql.expression import func
from utils import row2dict


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

full_chat_returning_keys: tuple = (
    "chat",
    "id",
    "dt_created",
    "dt_updated",
    "admin_id",
    "name",
    "is_private",
    "participants",
)

full_chat_returning: tuple = (
    Chat.id,
    Chat.dt_created,
    Chat.dt_updated,
    Chat.admin_id,
    Chat.name,
    Chat.is_private,
    Chat.participants,
)


class ChatCRUD:
    @classmethod
    async def get_chats(
            cls,
            participant_id: int,
            db: AsyncSession,
    ) -> list[ChatResponseItem] | None:
        # Подзапрос на получение id чатов, в которых состоит пользователь
        chat_ids_subquery = (
            sa.select(ChatParticipant.chat_id)
            .where(
                sa.and_(
                    ChatParticipant.is_available == True,  # noqa
                    ChatParticipant.participant_id == participant_id,
                )
            )
        )

        # Подзапрос на получение количества непрочитанных сообщений для чата
        unread_msgs_subquery = (
            sa.select(func.count(MessagesToParticipants.message_id))
            .where(
                sa.and_(
                    MessagesToParticipants.participant_id == participant_id,
                    MessagesToParticipants.is_read == False,  # noqa
                    MessagesToParticipants.chat_id == Chat.id,
                )
            ).order_by(None).scalar_subquery()
        )

        # Подзапрос на получение последнего сообщения чата
        last_chat_msg_id = (
            sa.select(Message.id)
            .filter(Message.chat_id == Chat.id)
            .order_by(Message.dt_created.desc())
            .order_by(Message.id.desc())
            .limit(1)
            .correlate(Chat)
            .as_scalar()
        )

        # итоговый запрос
        select_stmt = (
            sa.select(
                *chat_returning,
                unread_msgs_subquery.label(NEW_MESSAGE_COUNT),
                Message,
            )
            .filter(Chat.id.in_(chat_ids_subquery))
            .outerjoin(Message, Message.id == last_chat_msg_id)
            .order_by(Chat.dt_updated)
        )

        # добавляем в схему возврата кол-во непрочитанных сообщений для чата
        try:
            res = (await db.execute(select_stmt)).all()
            chats: list[ChatResponseItem] = []
            for row in res:
                chat_response_item: ChatResponseItem = ChatResponseItem.parse_obj(dict(zip(chat_returning_keys, row)))
                # Осторожно порядок определен в запросе выше
                chat_response_item.new_message_count = row[-2]
                chat_response_item.last_message = row2dict(row[-1]) if row[-1] else None
                chats.append(chat_response_item)
            return chats
        except OperationalError:
            return None

    @classmethod
    async def get_chat_by_id(
            cls,
            chat_id: int,
            db: AsyncSession,
    ) -> GetFullChatResponse | None:
        select_chat_stmt = (
            sa.select(Chat)
            .where(Chat.id == chat_id)
        )

        try:
            res = (await db.execute(select_chat_stmt)).scalars()

            if not res:
                return None
            res = dict(zip(full_chat_returning_keys, res))
            return res
        except OperationalError:
            return None

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
