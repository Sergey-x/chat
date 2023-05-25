import pydantic as pd


class AddMessageRequest(pd.BaseModel):
    text: str
    dest_id: int


class UpdateMessageRequest(pd.BaseModel):
    text: str
