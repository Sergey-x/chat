import fastapi as fa
from fastapi_pagination import add_pagination

from chat.handlers import api_router


def get_app() -> fa.FastAPI:
    """
    Creates application and all dependable objects.
    """
    description = "Микросервис чата."

    application = fa.FastAPI(
        title="Chat",
        description=description,
        docs_url="/swagger",
        openapi_url="/openapi",
        version="0.1.0",
    )

    application.include_router(api_router)
    add_pagination(application)

    return application


app = get_app()
