#!/bin/bash

# Phase 1: Agentic MLOps Platform - Infrastructure Setup
# Creates: ECR repositories, RDS, S3, IAM roles (but NOT App Runner services yet)
set -e

# Configuration
PROJECT_NAME="agentic-mlops"
REGION="us-east-1"
BUCKET_NAME="${PROJECT_NAME}-terraform-state-$(date +%s)"
ARTIFACT_BUCKET="${PROJECT_NAME}-artifacts-$(date +%s)"

echo "🚀 Phase 1: Setting up core infrastructure for Agentic MLOps Platform"

# Step 1: Check prerequisites
echo "📋 Checking prerequisites..."
if ! command -v aws &> /dev/null; then
    echo "❌ AWS CLI not installed. Please install it first."
    exit 1
fi

if ! command -v terraform &> /dev/null; then
    echo "❌ Terraform not installed. Please install it first."
    exit 1
fi

if ! aws sts get-caller-identity &> /dev/null; then
    echo "❌ AWS credentials not configured. Run 'aws configure' first."
    exit 1
fi

echo "✅ Prerequisites check passed"

# Step 2: Create S3 bucket for Terraform state
echo "🪣 Creating S3 bucket for Terraform state..."
aws s3api create-bucket --bucket $BUCKET_NAME --region $REGION
aws s3api put-bucket-versioning --bucket $BUCKET_NAME --versioning-configuration Status=Enabled

echo "✅ Created Terraform state bucket: $BUCKET_NAME"

# Step 3: Get default VPC and subnets (for MVP)
echo "🌐 Getting default VPC and subnet information..."
VPC_ID=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query 'Vpcs[0].VpcId' --output text)
SUBNET_IDS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=$VPC_ID" --query 'Subnets[].SubnetId' --output text | tr '\t' ',')

echo "📍 Using VPC: $VPC_ID"
echo "📍 Using Subnets: $SUBNET_IDS"

# Step 4: Save deployment config for next phases
echo "💾 Saving deployment configuration..."
cat > deployment-config.env << EOF
PROJECT_NAME="$PROJECT_NAME"
REGION="$REGION"
BUCKET_NAME="$BUCKET_NAME"
ARTIFACT_BUCKET="$ARTIFACT_BUCKET"
VPC_ID="$VPC_ID"
SUBNET_IDS="$SUBNET_IDS"
EOF

echo "✅ Configuration saved to deployment-config.env"

# Step 5: Initialize Terraform
echo "🏗️  Initializing Terraform..."
cd infra/terraform

terraform init \
  -backend-config="bucket=$BUCKET_NAME" \
  -backend-config="key=terraform.tfstate" \
  -backend-config="region=$REGION"

# Step 6: Deploy infrastructure without App Runner services
echo "📋 Planning infrastructure deployment (Phase 1)..."
terraform plan \
  -var "artifact_bucket_name=$ARTIFACT_BUCKET" \
  -var "api_image=" \
  -var "worker_image=" \
  -var "db_username=postgres" \
  -var "db_password=changeme123!" \
  -var "vpc_id=$VPC_ID" \
  -var "private_subnet_ids=[$(echo $SUBNET_IDS | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/']]" \
  -target="aws_ecr_repository.api" \
  -target="aws_ecr_repository.worker" \
  -target="aws_ecr_lifecycle_policy.api" \
  -target="aws_ecr_lifecycle_policy.worker" \
  -target="aws_s3_bucket.artifacts" \
  -target="aws_db_subnet_group.default" \
  -target="aws_security_group.rds" \
  -target="aws_security_group.app_runner" \
  -target="aws_db_instance.postgres" \
  -target="aws_secretsmanager_secret.db_credentials" \
  -target="aws_secretsmanager_secret_version.db_credentials" \
  -target="aws_db_proxy.postgres" \
  -target="aws_db_proxy_target.db" \
  -target="aws_iam_role.api_service" \
  -target="aws_iam_role.worker_service" \
  -target="aws_iam_role.rds_proxy" \
  -target="aws_iam_role_policy.api_policy" \
  -target="aws_iam_role_policy.worker_policy" \
  -target="aws_iam_role_policy_attachment.api_ecr" \
  -target="aws_iam_role_policy_attachment.worker_ecr" \
  -target="aws_iam_role_policy_attachment.rds_proxy"

echo "🚀 Applying infrastructure configuration (Phase 1)..."
read -p "Do you want to continue with the infrastructure deployment? (y/N): " confirm
if [[ $confirm == [yY] || $confirm == [yY][eE][sS] ]]; then
  terraform apply \
    -var "artifact_bucket_name=$ARTIFACT_BUCKET" \
    -var "api_image=" \
    -var "worker_image=" \
    -var "db_username=postgres" \
    -var "db_password=changeme123!" \
    -var "vpc_id=$VPC_ID" \
    -var "private_subnet_ids=[$(echo $SUBNET_IDS | sed 's/,/","/g' | sed 's/^/"/' | sed 's/$/"/'")]" \
    -target="aws_ecr_repository.api" \
    -target="aws_ecr_repository.worker" \
    -target="aws_ecr_lifecycle_policy.api" \
    -target="aws_ecr_lifecycle_policy.worker" \
    -target="aws_s3_bucket.artifacts" \
    -target="aws_db_subnet_group.default" \
    -target="aws_security_group.rds" \
    -target="aws_security_group.app_runner" \
    -target="aws_db_instance.postgres" \
    -target="aws_secretsmanager_secret.db_credentials" \
    -target="aws_secretsmanager_secret_version.db_credentials" \
    -target="aws_db_proxy.postgres" \
    -target="aws_db_proxy_target.db" \
    -target="aws_iam_role.api_service" \
    -target="aws_iam_role.worker_service" \
    -target="aws_iam_role.rds_proxy" \
    -target="aws_iam_role_policy.api_policy" \
    -target="aws_iam_role_policy.worker_policy" \
    -target="aws_iam_role_policy_attachment.api_ecr" \
    -target="aws_iam_role_policy_attachment.worker_ecr" \
    -target="aws_iam_role_policy_attachment.rds_proxy" \
    -auto-approve
else
  echo "❌ Deployment cancelled"
  exit 1
fi

cd ../..

echo "✅ Phase 1 infrastructure deployed successfully!"
echo ""
echo "📝 Next steps:"
echo "   1. Run: ./2-build-and-push.sh (to build and push Docker images)"
echo "   2. Run: ./3-deploy-app-runner.sh (to deploy App Runner services)"
echo ""
echo "🔍 ECR Repository URLs:"
cd infra/terraform
echo "   API: $(terraform output -raw api_ecr_repository_url)"
echo "   Worker: $(terraform output -raw worker_ecr_repository_url)"
cd ../..