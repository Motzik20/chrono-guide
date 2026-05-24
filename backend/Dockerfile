FROM python:3.13-slim AS base

WORKDIR /backend

COPY --from=ghcr.io/astral-sh/uv:0.11.16 /uv /uvx /bin/

ENV PATH="/backend/.venv/bin:$PATH"
ENV UV_LINK_MODE=copy

COPY pyproject.toml uv.lock ./

FROM base AS dev
RUN uv sync --frozen --no-install-project
COPY ./app ./app
COPY alembic.ini ./
COPY ./scripts ./scripts
RUN chmod +x /backend/scripts/start.sh

ENV HOME=/tmp
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

FROM base AS prod
RUN addgroup --system appgroup && adduser --system --group appuser
RUN uv sync --frozen --no-dev --no-install-project
COPY ./app ./app
COPY alembic.ini ./
COPY ./scripts ./scripts

RUN chmod +x /backend/scripts/start.sh
RUN chown -R appuser:appgroup /backend
ENV HOME=/tmp
USER appuser
EXPOSE 8000
ENTRYPOINT ["/backend/scripts/start.sh"]
