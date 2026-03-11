FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY pyproject.toml README.md /app/

RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir .

COPY app /app/app
COPY config /app/config
COPY domain /app/domain
COPY infra /app/infra
COPY portex /app/portex
COPY scripts /app/scripts
COPY services /app/services
COPY uvicorn.ini /app/uvicorn.ini

RUN useradd -m -u 1000 portex \
    && mkdir -p /app/data \
    && chown -R portex:portex /app

USER portex

EXPOSE 8000

CMD ["python", "-m", "uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
