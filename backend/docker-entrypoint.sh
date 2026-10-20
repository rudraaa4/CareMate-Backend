#!/bin/sh
set -e

# Bring the database schema up to date, then start the API.
alembic upgrade head
exec uvicorn app.main:app --host 0.0.0.0 --port 8000
