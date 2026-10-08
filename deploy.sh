#!/bin/bash
set -e

echo "🚀 Starting FraudSense AI Production Deployment"

# Check if .env exists
if [ ! -f ".env" ]; then
    echo "⚠️ .env file not found. Copying from .env.example..."
    cp .env.example .env
    echo "⚠️ PLEASE EDIT .env TO SET YOUR SECRETS BEFORE DEPLOYING PUBLICLY!"
    exit 1
fi

echo "📦 Building and starting Docker containers..."
docker-compose up -d --build

echo "✅ Deployment successful!"
echo "Backend API is running on http://localhost:8000"
echo "Frontend Dashboard is running on http://localhost:5173"
echo "Streamlit UI is running on http://localhost:8501"
