FROM python:3.13-slim

# Send logs straight to stdout (so "docker compose logs" shows them) and skip .pyc files.
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

WORKDIR /srv

# Dependencies first: this layer is cached until requirements.txt changes.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app

# Do not run the app as root inside the container.
RUN useradd --system --no-create-home appuser
USER appuser

EXPOSE 5000

# 0.0.0.0 so other containers can reach it; 127.0.0.1 would be container-local only.
CMD ["gunicorn", "--workers", "2", "--bind", "0.0.0.0:5000", "--access-logfile", "-", "app:create_app()"]
