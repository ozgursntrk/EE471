# 1) Base image: a small Debian Linux with Python 3.12 already installed
FROM python:3.12-slim

# 2) Python settings that are useful inside containers
#    - do not create .pyc files
#    - print logs immediately (so `docker logs` shows them right away)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) All next commands run inside /app in the container
WORKDIR /app

# 4) Install the Python packages first.
#    This layer is cached: if only the code changes, Docker does not reinstall them.
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copy the application code (files in .dockerignore are skipped)
COPY . .

# 6) Do not run as root (safer)
RUN useradd --create-home appuser
USER appuser

# 7) The app listens on port 5000 inside the container
EXPOSE 5000

# 8) Start the app with gunicorn, a production web server.
#    0.0.0.0 = accept connections from outside the container.
#    timeout 180 = speech recognition can take a while.
#    --access-logfile - = print every request to the terminal (docker logs)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "180", "--access-logfile", "-", "app:app"]