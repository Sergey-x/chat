import fastapi as fa
from api import api_router
from api.consts import USER_ID_HTTP_HEADER
from enums import Stages
from fastapi_pagination import add_pagination
from settings import SETTINGS


SWAGGER_PATH = "/swagger"
OPENAPI_PATH = "/openapi"


def get_app() -> fa.FastAPI:
    """
    Creates application and all dependable objects.
    """
    description = "Микросервис чата."

    application = fa.FastAPI(
        title="Chat",
        description=description,
        docs_url=None if SETTINGS.STAGE == Stages.PROD else SWAGGER_PATH,
        openapi_url=None if SETTINGS.STAGE == Stages.PROD else OPENAPI_PATH,
        version="0.1.0",
    )

    application.include_router(api_router)
    add_pagination(application)

    return application


app = get_app()


@app.middleware("http")
async def check_user_identity_header(request: fa.Request, call_next):
    # Даем доступ к документации без HTTP header-a в DEV stage
    if SETTINGS.STAGE != Stages.PROD and (request.url.path == OPENAPI_PATH or request.url.path == SWAGGER_PATH):
        return await call_next(request)

    user_id = request.headers.get(USER_ID_HTTP_HEADER, None)
    if user_id is None or not user_id:
        return fa.Response(status_code=fa.status.HTTP_401_UNAUTHORIZED, content="User id in HTTP header is not defined")
    response = await call_next(request)
    return response
