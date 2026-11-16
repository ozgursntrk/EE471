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
    
# The script and the pose model (9 MB) go into the image
COPY arm_up.py pose_landmarker_full.task ./

# Do not run as root
RUN useradd --create-home appuser
USER appuser

# docker run arm-up /images/pose-1.jpg  ->  python arm_up.py /images/pose-1.jpg
ENTRYPOINT ["python", "arm_up.py"]