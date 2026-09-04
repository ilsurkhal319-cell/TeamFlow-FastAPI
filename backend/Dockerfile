FROM python:3.12-slim
WORKDIR /app
ENV PYTHONPATH=/app
COPY backend/requirements.txt ./requirements.txt
RUN pip install --no-cache-dir -r requirements.txt
COPY backend/app ./app
COPY backend/tests ./tests
COPY backend/migrations ./migrations
COPY backend/alembic.ini backend/pyproject.toml ./
COPY backend/scripts ./scripts
RUN chmod +x scripts/entrypoint.sh
EXPOSE 8000
ENTRYPOINT ["./scripts/entrypoint.sh"]
