import pydantic as pd


class CreateMessageRequestSchema(pd.BaseModel):
    chat_id: int | None = pd.Field(description="Id чата на несколько человек (если уже создан)")
    text: str = pd.Field(description="Текст сообщения")
    dest_id: int | None = pd.Field(
        description="Id пользователя, которому отправлено сообщение, если это первое сообщения между людьми",
    )

    @pd.root_validator(pre=True)
    def check_chat_or_dest_id_exist(cls, values):
        chat_id: int | None = values.get('chat_id', None)
        dest_id: int | None = values.get('dest_id', None)

        if chat_id is None and dest_id is None:
            raise ValueError("chat_id or dest_id must be specified")
        return values


class UpdateMessageRequestSchema(pd.BaseModel):
    text: str
