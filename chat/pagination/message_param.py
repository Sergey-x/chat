import fastapi as fa
import pydantic as pd
from fastapi_pagination.bases import AbstractParams, RawParams


class MessagePaginationParams(pd.BaseModel, AbstractParams):
    page: int = fa.Query(1, ge=1, description="Page number")
    size: int = fa.Query(15, ge=1, le=100, description="Page size")

    def to_raw_params(self) -> RawParams:
        return RawParams(
            limit=self.size,
            offset=self.size * (self.page - 1),
        )
