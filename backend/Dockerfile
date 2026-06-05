FROM python:3.9-slim

WORKDIR /app

# Install system dependencies (optional but good practice)
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY . .

# Expose default port
EXPOSE 8001

# Support dynamic port binding for Render deployment
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8001}"]
