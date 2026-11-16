# Small Linux image with Python 3.12
FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# System libraries OpenCV (a MediaPipe dependency) needs inside a container
RUN apt-get update \
    && apt-get install -y --no-install-recommends libgl1 libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install MediaPipe first (cached layer)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# MediaPipe's Linux library also needs the EGL / OpenGL ES libraries (no GPU is used)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libegl1 libgles2 \
    && rm -rf /var/lib/apt/lists/*

# The script and the face model (4 MB) go into the image
COPY face_direction.py face_landmarker.task ./

# Do not run as root
RUN useradd --create-home appuser
USER appuser

# docker run face-direction /images/face-1.png  ->  python face_direction.py /images/face-1.png
ENTRYPOINT ["python", "face_direction.py"]