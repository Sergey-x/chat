from datetime import datetime

import pydantic as pd

from ..messages import MessageResponseItem


NEW_MESSAGE_COUNT: str = "new_message_count"
LAST_MESSAGE: str = "last_message"


class ChatResponseItem(pd.BaseModel):
    id: int
    admin_id: int | None
    dt_created: datetime | str
    dt_updated: datetime | str
    name: str | None
    is_private: bool
    last_message: MessageResponseItem | None = pd.Field(default=None, alias=LAST_MESSAGE)
    new_message_count: int | None = pd.Field(default=None, alias=NEW_MESSAGE_COUNT)


class GetChatsResponseItem(pd.BaseModel):
    chats: list[ChatResponseItem]


class ChatParticipantItem(pd.BaseModel):
    chat_id: int
    participant_id: int
    is_available: bool


class FullChatResponseItem(pd.BaseModel):
    id: int
    admin_id: int | None
    dt_created: datetime | str
    dt_updated: datetime | str
    name: str | None
    is_private: bool
    participants: list[ChatParticipantItem]


class GetFullChatResponse(pd.BaseModel):
    chat: FullChatResponseItem
