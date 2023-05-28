import pydantic as pd


class CreateChatRequestSchema(pd.BaseModel):
    name: str | None
    participants: list[int]


class UpdateChatRequestSchema(pd.BaseModel):
    name: str | None
    participants: list[int]
