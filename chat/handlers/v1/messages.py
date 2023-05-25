from typing import Annotated

import fastapi as fa
from fastapi.responses import ORJSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from chat.crud import MessageCRUD
from chat.handlers.deps import get_db
from chat.schemas import AddMessageRequest, MessageResponseItem, UpdateMessageRequest


api_router = fa.APIRouter()


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
        message: UpdateMessageRequest,
        x_user_identity: Annotated[int | None, fa.Header()] = None,
        db: AsyncSession = fa.Depends(get_db),
):
    res = await MessageCRUD.update_message(x_user_identity, message_id, message.text, db)
    if not res:
        raise fa.HTTPException(fa.status.HTTP_400_BAD_REQUEST)
    return res


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
async def add_message(message: AddMessageRequest,
                      x_user_identity: Annotated[int | None, fa.Header()] = None,
                      db: AsyncSession = fa.Depends(get_db)):
    res = await MessageCRUD.add_message(x_user_identity, message, db)
    if not res:
        raise fa.HTTPException(fa.status.HTTP_400_BAD_REQUEST)
    return res


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
                                   x_user_identity: Annotated[int | None, fa.Header()] = None,
                                   db: AsyncSession = fa.Depends(get_db)):
    if x_user_identity is None:
        raise fa.HTTPException(status_code=fa.status.HTTP_401_UNAUTHORIZED,
                               detail="User id in HTTP header is not defined")

    deleted_row: int = await MessageCRUD.delete_message(db, message_id, x_user_identity)
    if deleted_row == 0:
        raise fa.HTTPException(status_code=fa.status.HTTP_400_BAD_REQUEST(), detail="Нет указанного сообщения")
