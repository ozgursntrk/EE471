# 1) Base image: a small Debian Linux with Python 3.12 already installed
FROM python:3.12-slim

# 2) Python settings that are useful inside containers
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# 3) All next commands run inside /app in the container
WORKDIR /app

# 4) Install the Python packages first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 5) Copy the application code (files in .dockerignore are skipped)
COPY . .

# 6) Do not run as root (safer)
RUN useradd --create-home appuser
USER appuser

# 7) The app listens on port 5000 inside the container
EXPOSE 5000

# 8) Start the app with gunicorn and print every request (access log)
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "app:app"]