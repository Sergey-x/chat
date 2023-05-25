import fastapi as fa

from .v1 import messages_router


api_router = fa.APIRouter()

api_router.include_router(messages_router, prefix="/messages", tags=["messages"])
