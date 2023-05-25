import fastapi as fa

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
    return application


app = get_app()
