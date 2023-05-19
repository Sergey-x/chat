ARG PYTHON_VERSION=3.11
FROM python:${PYTHON_VERSION}-slim

RUN apt-get update && pip install poetry && poetry config virtualenvs.create false

WORKDIR /chat

COPY ./pyproject.toml .
COPY ./poetry.lock .
COPY . .

RUN poetry install

ENTRYPOINT uvicorn chat.main:app --host 0.0.0.0 --port 8088 --reload
