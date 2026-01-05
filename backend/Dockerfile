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
RUN poetry install --without dev --no-interaction --no-ansi
COPY ./app ./app
COPY alembic.ini ./

RUN printf '#!/bin/bash\nset -e\necho "Running database migrations..."\npoetry run alembic upgrade head\necho "Starting server..."\nexec "$@"\n' > /backend/entrypoint.sh && chmod +x /backend/entrypoint.sh
RUN chown -R appuser:appgroup /backend
# Set HOME for appuser and ensure Poetry doesn't create virtualenvs
ENV HOME=/tmp
ENV POETRY_VIRTUALENVS_CREATE=false
USER appuser
EXPOSE 8000
ENTRYPOINT ["/backend/entrypoint.sh"]