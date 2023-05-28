from collections import defaultdict
from typing import Annotated

import fastapi as fa
from api.consts import USER_ID_HTTP_HEADER
from api.deps import get_db
from crud import ChatCRUD, MessageCRUD
from fastapi.responses import ORJSONResponse
from fastapi_pagination import Page
from pagination import MessagePaginationParams
from schemas import (
    ChatResponseItem,
    CreateMessageRequestSchema,
    MessageResponseItem,
    UpdateMessageRequestSchema,
)
from sqlalchemy.ext.asyncio import AsyncSession


api_router = fa.APIRouter()


@api_router.get(
    "/{chat_id}",
    response_class=ORJSONResponse,
    response_model=Page[object],
    status_code=fa.status.HTTP_200_OK,
    responses={
        fa.status.HTTP_200_OK: {
            "description": "Ok",
        },
        fa.status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials",
        },
        fa.status.HTTP_400_BAD_REQUEST: {
            "description": "Bad request",
        },
    },
)
async def get_chat_messages(
        chat_id: Annotated[int, fa.Path()],
        user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
        db: AsyncSession = fa.Depends(get_db),
        params: MessagePaginationParams = fa.Depends(),  # noqa
):
    """Получить сообщения чата постранично (есть пагинация)."""
    # проверить, что юзер состоит в чате
    is_user_in_chat: bool = await ChatCRUD.check_user_in_chat(db=db, participant_id=user_id, chat_id=chat_id)

    # сразу же получаем сообщения
    chat_messages = await MessageCRUD.get_chat_messages(db=db, chat_id=chat_id)

    # Если не состоит - то ошибка
    if not is_user_in_chat:
        raise fa.HTTPException(status_code=fa.status.HTTP_400_BAD_REQUEST)
    return chat_messages


@api_router.patch(
    "/{message_id}",
    response_class=ORJSONResponse,
    response_model=MessageResponseItem,
    status_code=fa.status.HTTP_200_OK,
    responses={
        fa.status.HTTP_200_OK: {
            "description": "Ok",
        },
        fa.status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials",
        },
    },
)
async def update_message(
        message_id: int,
        message: UpdateMessageRequestSchema,
        user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
        db: AsyncSession = fa.Depends(get_db),
):
    """Изменить сообщение."""
    updated_msg: MessageResponseItem | None = await MessageCRUD.update_message(user_id, message_id, message.text, db)
    if updated_msg is None:
        raise fa.HTTPException(fa.status.HTTP_400_BAD_REQUEST)
    return updated_msg


@api_router.post(
    "",
    response_class=ORJSONResponse,
    response_model=MessageResponseItem,
    status_code=fa.status.HTTP_201_CREATED,
    responses={
        fa.status.HTTP_201_CREATED: {
            "description": "Ok",
        },
        fa.status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials",
        },
    },
)
async def add_message(message: CreateMessageRequestSchema,
                      user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)],
                      db: AsyncSession = fa.Depends(get_db)):
    """Добавить сообщение.

    Если message.chat_id не установлено, то это первое сообщение в личной переписке 2-х пользователей.
    Перед созданием сообщения нужно создать приватный чат для этих пользователей (user_id, message.dest_id).
    Если message.chat_id установлен, то просто прикрепляем сообщение к указанному чату.
    """
    chat: ChatResponseItem | None = None
    print(message)
    if message.chat_id is None:
        # Сначала создаем чат
        print("Creating chat")
        chat = await ChatCRUD.create_chat(db=db, participant_ids=[user_id, message.dest_id], is_private=True, )
        print(chat)
        if chat is None:
            raise fa.HTTPException(status_code=fa.status.HTTP_500_INTERNAL_SERVER_ERROR,
                                   detail="Не удалось создать приватный чат")
    chat_id: int = message.chat_id or chat.id

    # Добавляем сообщение в чат
    new_msg: MessageResponseItem | None = await MessageCRUD.add_message_to_chat(
        db=db,
        author_id=user_id,
        chat_id=chat_id,
        message=message,
    )
    if new_msg is None:
        raise fa.HTTPException(fa.status.HTTP_400_BAD_REQUEST)
    return new_msg


@api_router.delete(
    "/{message_id}",
    status_code=fa.status.HTTP_204_NO_CONTENT,
    responses={
        fa.status.HTTP_204_NO_CONTENT: {
            "description": "Ok",
        },
        fa.status.HTTP_400_BAD_REQUEST: {
            "description": "Bad message id",
        },
        fa.status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials",
        },
    },
)
async def make_message_unavailable(message_id: int,
                                   user_id: Annotated[int, fa.Header(alias=USER_ID_HTTP_HEADER)],
                                   db: AsyncSession = fa.Depends(get_db)):
    deleted_row: int = await MessageCRUD.delete_message(db, message_id, user_id)
    if deleted_row == 0:
        raise fa.HTTPException(status_code=fa.status.HTTP_400_BAD_REQUEST(), detail="Нет указанного сообщения")


class ConnectionManager:
    def __init__(self):
        self.active_connections: dict[int, fa.WebSocket | None] = defaultdict()

    async def connect(self, user_id: int, websocket: fa.WebSocket):
        await websocket.accept()
        self.active_connections[user_id] = websocket

    def disconnect(self, user_id: int):
        self.active_connections[user_id] = None

    async def send_personal_message(self, message: str, websocket: fa.WebSocket):
        await websocket.send_text(message)


websocket_manager = ConnectionManager()


@api_router.websocket("/ws")
async def websocket_endpoint(
        websocket: fa.WebSocket,
        x_user_identity: Annotated[int | None, fa.Header()] = None,
):
    if x_user_identity is None:
        return

    await websocket_manager.connect(x_user_identity, websocket)

    try:
        while True:
            data = await websocket.receive_text()
            await websocket_manager.send_personal_message(f"You wrote: {data}", websocket)
            await websocket_manager.broadcast(f"Client #{x_user_identity} says: {data}")
    except fa.WebSocketDisconnect:
        websocket_manager.disconnect(websocket)
        await websocket_manager.broadcast(f"Client #{x_user_identity} left the chat")
