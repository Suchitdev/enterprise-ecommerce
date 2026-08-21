FROM python:3.12-slim

WORKDIR /app

RUN groupadd --system appgroup && \
    useradd --system --gid appgroup --home-dir /tmp appuser

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY backend/ .

RUN mkdir -p /app/staticfiles /app/media && \
    chown -R appuser:appgroup /app

USER appuser

CMD ["gunicorn", "--bind", "0.0.0.0:8000", "config.wsgi:application"]