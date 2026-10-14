FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for XGBoost and binary wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy full application code and models
COPY . .

# Create non-root user and persistent data folder
RUN useradd --create-home --uid 10001 appuser && mkdir -p data && chown -R appuser:appuser /app
USER appuser

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=15s --retries=3 \
  CMD python -c "from urllib.request import urlopen, os; urlopen('http://127.0.0.1:' + os.getenv('PORT', '8000') + '/health', timeout=3)"

# Run FastAPI with dynamic port binding for cloud hosts (Render, Railway, Fly.io)
CMD ["sh", "-c", "uvicorn api.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
