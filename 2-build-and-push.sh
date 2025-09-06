#!/bin/bash

# Phase 2: Agentic MLOps - Build and Push Docker Images
set -e

echo "🐳 Phase 2: Building and pushing Docker images for Agentic MLOps Platform"

# Load deployment configuration
if [ ! -f deployment-config.env ]; then
    echo "❌ deployment-config.env not found. Please run ./1-deploy-infrastructure.sh first."
    exit 1
fi

source deployment-config.env

echo "📋 Using configuration:"
echo "   Project: $PROJECT_NAME"
echo "   Region: $REGION"

# Check if Dockerfiles exist
if [ ! -f api/Dockerfile ]; then
    echo "❌ api/Dockerfile not found. Creating a placeholder..."
    mkdir -p api
    cat > api/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY api/ .

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
EOF
    echo "⚠️  Created placeholder api/Dockerfile - you'll need to customize it"
fi

if [ ! -f worker/Dockerfile ]; then
    echo "❌ worker/Dockerfile not found. Creating a placeholder..."
    mkdir -p worker
    cat > worker/Dockerfile << 'EOF'
FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY worker/ .

# Expose port
EXPOSE 8080

# Run the application
CMD ["python", "main.py"]
EOF
    echo "⚠️  Created placeholder worker/Dockerfile - you'll need to customize it"
fi

# Create placeholder requirements.txt if it doesn't exist
if [ ! -f requirements.txt ]; then
    echo "❌ requirements.txt not found. Creating a placeholder..."
    cat > requirements.txt << 'EOF'
fastapi==0.104.1
uvicorn==0.24.0
sqlalchemy==2.0.23
psycopg2-binary==2.9.9
boto3==1.34.0
langgraph==0.0.50
langchain==0.1.0
pydantic==2.5.0
EOF
    echo "⚠️  Created placeholder requirements.txt - you'll need to customize it"
fi

# Get ECR repository URLs from Terraform outputs
echo "🔍 Getting ECR repository URLs..."
cd infra/terraform
API_REPO=$(terraform output -raw api_ecr_repository_url)
WORKER_REPO=$(terraform output -raw worker_ecr_repository_url)
FRONTEND_REPO=$(terraform output -raw frontend_ecr_repository_url)
cd ../..

echo "📍 API Repository: $API_REPO"
echo "📍 Worker Repository: $WORKER_REPO"
echo "📍 Frontend Repository: $FRONTEND_REPO"

# Login to ECR
echo "🔑 Logging into ECR..."
aws ecr get-login-password --region $REGION | docker login --username AWS --password-stdin $API_REPO

# Build API image
echo "🔨 Building API image..."
docker build -f api/Dockerfile -t $API_REPO:latest .

# Build Worker image  
echo "🔨 Building Worker image..."
docker build -f worker/Dockerfile -t $WORKER_REPO:latest .

# Build Frontend image
echo "🔨 Building Frontend image..."
docker build -f frontend/Dockerfile -t $FRONTEND_REPO:latest .

# Push images
echo "📤 Pushing API image..."
docker push $API_REPO:latest

echo "📤 Pushing Worker image..."
docker push $WORKER_REPO:latest

echo "📤 Pushing Frontend image..."
docker push $FRONTEND_REPO:latest

# Save image URIs for next phase
echo "💾 Saving image URIs..."
cat >> deployment-config.env << EOF
API_IMAGE="$API_REPO:latest"
WORKER_IMAGE="$WORKER_REPO:latest"
FRONTEND_IMAGE="$FRONTEND_REPO:latest"
EOF

echo "✅ Docker images built and pushed successfully!"
echo ""
echo "📝 Next step:"
echo "   Run: ./3-deploy-app-runner.sh (to deploy App Runner services with the images)"