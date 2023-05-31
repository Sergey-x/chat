from typing import Annotated

import fastapi as fa
from api.consts import USER_ID_HTTP_HEADER
from api.deps import get_db
from crud import ChatCRUD
from fastapi.responses import ORJSONResponse
from schemas import (
    ChatResponseItem,
    CreateChatRequestSchema,
    GetChatsResponseItem,
    UpdateChatRequestSchema,
)
from sqlalchemy.ext.asyncio import AsyncSession


api_router = fa.APIRouter()


@api_router.get(
    "",
    response_class=ORJSONResponse,
    response_model=GetChatsResponseItem,
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
async def get_chats(
        user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
        db: AsyncSession = fa.Depends(get_db),
):
    res: list[ChatResponseItem] | None = await ChatCRUD.get_chats(user_id, db)
    if res is None:
        raise fa.HTTPException(status_code=fa.status.HTTP_500_INTERNAL_SERVER_ERROR)
    return GetChatsResponseItem(chats=res)


@api_router.get(
    "/{chat_id}",
    response_class=ORJSONResponse,
    status_code=fa.status.HTTP_200_OK,
    responses={
        fa.status.HTTP_200_OK: {
            "description": "Ok",
        },
        fa.status.HTTP_401_UNAUTHORIZED: {
            "description": "Could not validate credentials",
        },
        fa.status.HTTP_404_NOT_FOUND: {
            "description": "Chat not found",
        },
    },
)
async def get_chat_by_id(
        chat_id: Annotated[int, fa.Path()],
        user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
        db: AsyncSession = fa.Depends(get_db),
):
    full_chat = await ChatCRUD.get_chat_by_id(chat_id, db)
    if full_chat is None:
        raise fa.HTTPException(status_code=fa.status.HTTP_404_NOT_FOUND)

    participant_objects = getattr(full_chat.get("chat"), "participants")

    # check user is member of the chat
    is_user_member_of_chat: bool = False
    for member in participant_objects:
        if getattr(member, "participant_id") == user_id:
            is_user_member_of_chat = True
            break

    if not is_user_member_of_chat:
        raise fa.HTTPException(status_code=fa.status.HTTP_400_BAD_REQUEST,
                               detail="You don't have permission to read this chat")
    return full_chat


@api_router.post(
    "",
    response_class=ORJSONResponse,
    response_model=ChatResponseItem,
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
async def create_chat(chat: CreateChatRequestSchema,
                      user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
                      db: AsyncSession = fa.Depends(get_db)):
    res: ChatResponseItem | None = await ChatCRUD.create_chat(
        chat_name=chat.name,
        participant_ids=chat.participants,
        admin_id=user_id,
        is_private=False,
        db=db,
    )

    if not res:
        raise fa.HTTPException(fa.status.HTTP_400_BAD_REQUEST)
    return res


@api_router.patch(
    "/{chat_id}",
    response_class=ORJSONResponse,
    # response_model=ChatResponseItem,
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
async def update_chat(
        chat_id: int,
        chat: UpdateChatRequestSchema,
        user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
        db: AsyncSession = fa.Depends(get_db),
):
    res = await ChatCRUD.update_chat(user_id=user_id, chat_id=chat_id, chat=chat, db=db)
    if not res:
        raise fa.HTTPException(fa.status.HTTP_400_BAD_REQUEST)
    return res


@api_router.delete(
    "/{chat_id}",
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
async def make_chat_unavailable(chat_id: int,
                                user_id: Annotated[int | None, fa.Header(alias=USER_ID_HTTP_HEADER)] = None,
                                db: AsyncSession = fa.Depends(get_db)):
    changed_row_count: int = await ChatCRUD.change_participant_status_in_status(db, chat_id, user_id, False)
    if changed_row_count == 0:
        raise fa.HTTPException(status_code=fa.status.HTTP_400_BAD_REQUEST(),
                               detail="Нет указанного чата или он уже удален")
