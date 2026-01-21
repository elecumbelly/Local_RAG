FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    poppler-utils \
    tesseract-ocr \
    ocrmypdf \
    && rm -rf /var/lib/apt/lists/* \
    && groupadd -r appgroup && useradd -r -g appgroup appuser

COPY pyproject.toml /app/pyproject.toml
RUN pip install --no-cache-dir uv \
    && uv pip compile pyproject.toml -o requirements.txt \
    && uv pip install --system -r requirements.txt

COPY src /app/src
COPY tests /app/tests
ENV PYTHONPATH=/app/src

RUN chown -R appuser:appgroup /app

USER appuser

EXPOSE 8000

CMD ["uvicorn", "nexus.api.main:app", "--host", "0.0.0.0", "--port", "8000"]
