from datetime import datetime

import pydantic as pd


class ChatResponseItem(pd.BaseModel):
    id: int
    admin_id: int | None
    dt_created: datetime | str
    dt_updated: datetime | str
    name: str | None
    is_private: bool


class GetChatsResponseItem(pd.BaseModel):
    chats: list[ChatResponseItem]
