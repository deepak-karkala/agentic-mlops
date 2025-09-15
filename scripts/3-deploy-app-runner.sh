#!/bin/bash

# Phase 3: Agentic MLOps - Deploy App Runner Services
set -e

echo "🚀 Phase 3: Deploying App Runner services for Agentic MLOps Platform"

# Load deployment configuration
if [ ! -f deployment-config.env ]; then
    echo "❌ deployment-config.env not found. Please run previous phases first."
    exit 1
fi

source deployment-config.env

# Check if images are available
if [ -z "$API_IMAGE" ] || [ -z "$FRONTEND_IMAGE" ]; then
    echo "❌ Image URIs not found. Please run ./2-build-and-push.sh first."
    exit 1
fi

echo "📋 Using configuration:"
echo "   Project: $PROJECT_NAME"
echo "   Region: $REGION"
echo "   API Image: $API_IMAGE (includes integrated worker)"
echo "   Frontend Image: $FRONTEND_IMAGE"

# Deploy App Runner services
echo "🏗️  Deploying App Runner services..."
cd infra/terraform

terraform plan \
  -var "artifact_bucket_name=$ARTIFACT_BUCKET" \
  -var "api_image=$API_IMAGE" \
  -var "frontend_image=$FRONTEND_IMAGE" \
  -var "db_username=postgres" \
  -var "db_password=changeme123!" \
  -var "vpc_id=$VPC_ID" \
  -var "private_subnet_ids=[$(echo $SUBNET_IDS | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/']]"

echo "🚀 Applying complete infrastructure..."
read -p "Do you want to deploy the App Runner services? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
  terraform apply \
    -var "artifact_bucket_name=$ARTIFACT_BUCKET" \
    -var "api_image=$API_IMAGE" \
    -var "frontend_image=$FRONTEND_IMAGE" \
    -var "db_username=postgres" \
    -var "db_password=changeme123!" \
    -var "vpc_id=$VPC_ID" \
    -var "private_subnet_ids=[$(echo $SUBNET_IDS | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/')]" \
    -auto-approve
else
  echo "❌ Deployment cancelled"
  exit 1
fi

echo ""
echo "✅ Complete deployment finished successfully!"
echo ""
echo "🌐 Application URLs:"
echo "   Frontend Service: https://$(terraform output -raw frontend_service_url)"
echo "   API Service: https://$(terraform output -raw api_service_url) (includes integrated worker)"
echo ""
echo "🔗 Database Connection:"
echo "   RDS Proxy Endpoint: $(terraform output -raw db_proxy_endpoint)"
echo "   Database Name: postgres"
echo "   Username: postgres"
echo ""
echo "🪣 Storage:"
echo "   S3 Bucket: $(terraform output -raw s3_bucket_name)"
echo ""
echo "🔐 Secrets:"
echo "   Database Credentials: $(terraform output -raw secrets_manager_secret_arn)"
echo ""
echo "📝 Environment Variables needed for your applications:"
echo "   DATABASE_URL=postgresql://postgres:<password>@$(terraform output -raw db_proxy_endpoint):5432/postgres"
echo "   S3_BUCKET_NAME=$(terraform output -raw s3_bucket_name)"
echo "   AWS_REGION=$REGION"

cd ../..