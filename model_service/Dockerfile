FROM registry-1.docker.io/library/python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    HF_HOME=/app/models_cache

WORKDIR /app

# Install standard PyTorch with GPU support
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir torch

# Copy and install other Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application source code
COPY app.py .

# Create cache directory
RUN mkdir -p /app/models_cache

EXPOSE 8001

CMD ["uvicorn", "app:app", "--host", "0.0.0.0", "--port", "8001"]
