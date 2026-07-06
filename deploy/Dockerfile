FROM python:3.11-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app
COPY requirements.txt pyproject.toml README.MD ./
RUN pip install --no-cache-dir -r requirements.txt

COPY tweetgrambot ./tweetgrambot
COPY scripts ./scripts
COPY deploy/entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

VOLUME ["/app/storage/temp"]
ENTRYPOINT ["/entrypoint.sh"]
