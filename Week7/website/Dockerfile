# Small Linux image with Python 3.12
FROM python:3.12-slim

# No .pyc files, print logs immediately
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Install packages first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the website code
COPY . .

# Run as a normal user, not root
RUN useradd --create-home appuser
USER appuser

EXPOSE 5000

# gunicorn web server, every request is printed to the logs
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--timeout", "120", "--access-logfile", "-", "app:app"]