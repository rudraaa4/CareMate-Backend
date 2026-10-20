FROM python:3.14-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Dependencies first, so rebuilds that only change code reuse this layer.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY alembic.ini .
COPY alembic ./alembic
COPY app ./app
COPY docker-entrypoint.sh .

# Run as an unprivileged user, not root.
RUN useradd --create-home appuser && chown -R appuser /app
USER appuser

EXPOSE 8000
ENTRYPOINT ["sh", "docker-entrypoint.sh"]
