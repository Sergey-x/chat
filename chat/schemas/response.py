from datetime import datetime

import pydantic as pd


class MessageResponseItem(pd.BaseModel):
    id: int
    dt_created: datetime | str
    dt_updated: datetime | str | None
    text: str
    is_available: bool
    author_id: int
    dest_id: int
    read: bool
