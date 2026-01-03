FROM python:3.13-slim AS base

WORKDIR /backend

RUN pip install poetry==1.8.3

RUN poetry config virtualenvs.create false

COPY pyproject.toml poetry.lock ./

FROM base AS dev
RUN poetry install --no-interaction --no-ansi
COPY ./app ./app
COPY alembic.ini ./

ENV HOME=/tmp
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod
RUN addgroup --system appgroup && adduser --system --group appuser
RUN poetry install --without dev--no-interaction --no-ansi
COPY ./app ./app
COPY alembic.ini ./
RUN chown -R appuser:appgroup /backend
USER appuser
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]