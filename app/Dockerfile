FROM python:3.11-slim

WORKDIR /app

ENV PYTHONUNBUFFERED=1 \
    APP_VERSION=v1.0 \
    APP_TITLE="LUMEN - Premium Audio & Smart Gear (v1.0)" \
    REDIS_HOST=redis \
    REDIS_PORT=6379

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY templates templates/
COPY app.py .

EXPOSE 5000

CMD ["python", "app.py"]
