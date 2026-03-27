FROM python:3.11-slim

# Install system build deps needed for some Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential gcc libffi-dev libssl-dev curl && \
    rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy only requirements first for better caching
COPY backened/requirement.txt ./backened/requirement.txt

# Upgrade pip, then install dependencies
RUN pip install --upgrade pip setuptools wheel
RUN pip install --no-cache-dir -r backened/requirement.txt

# Copy app source
COPY . .

# Use PORT env (Render sets this automatically)
ENV PORT=10000

# Run with eventlet worker for Socket.IO compatibility (ensure eventlet in requirements)
CMD ["gunicorn", "-k", "eventlet", "-w", "1", "backened.app:app", "--bind", "0.0.0.0:$PORT"]
