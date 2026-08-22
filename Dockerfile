# Minimal production-oriented Dockerfile structure
FROM python:3.11-slim

WORKDIR /app

# Install system dependencies (often needed for pandas/xgboost)
RUN apt-get update && apt-get install -y libgomp1 && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application logic
COPY api/ api/
COPY app/ app/
COPY src/ src/
COPY models/ models/

EXPOSE 8000
EXPOSE 8501

CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000"]
