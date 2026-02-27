FROM python:3.13-slim-bookworm

RUN apt-get update && apt-get install -y curl 
RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app
COPY pyproject.toml poetry.lock ./

RUN --mount=type=cache,target=/root/.cache/pypoetry \
    --mount=type=cache,target=/root/.cache/pip \
    poetry config virtualenvs.create false && poetry lock && poetry install --no-root --no-interaction --no-ansi --only main

RUN python -m spacy download en_core_web_md

COPY ./app /app/app

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

COPY ./README.md /README.md
COPY ./version.txt /version.txt

EXPOSE 8090

CMD ["poetry", "run", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8090", "--workers", "4", "--loop", "uvloop", "--http", "httptools"]
