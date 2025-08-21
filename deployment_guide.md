Here's your complete step-by-step deployment guide:

  Prerequisites (Install if needed):

  # Install Terraform
  brew install terraform

  # Install AWS CLI
  curl "https://awscli.amazonaws.com/AWSCLIV2.pkg" -o "AWSCLIV2.pkg"
  sudo installer -pkg AWSCLIV2.pkg -target /

  # Install Docker Desktop from: https://www.docker.com/products/docker-desktop

  Step 1: Configure AWS Credentials

  aws configure
  # Enter your AWS Access Key ID, Secret Access Key, region (us-east-1), and output format (json)

  Step 2: Run Infrastructure Deployment

  ./deploy.sh

  This will:
  - Create S3 bucket for Terraform state
  - Get default VPC and subnet information
  - Deploy all AWS infrastructure (ECR, RDS, App Runner, etc.)

  Step 3: Build and Deploy Applications (After Step 2)

  ./build-and-push.sh

  This will:
  - Build Docker images for API and Worker
  - Push images to ECR repositories
  - Update App Runner services with new images

  What Gets Created:

  - ECR Repositories: For API and Worker container images
  - RDS Postgres: Database with proxy for connection pooling
  - S3 Bucket: For storing generated artifacts
  - App Runner Services: API and Worker services with VPC connectivity
  - IAM Roles: Proper permissions for all services
  - Security Groups: Network security between services

  Important URLs (Available after deployment):

  # Get service URLs
  cd infra/terraform
  terraform output api_service_url
  terraform output worker_service_url
  terraform output db_proxy_endpoint

  Environment Variables Needed:

  Your applications will need these environment variables:
  - DATABASE_URL: RDS Proxy endpoint
  - S3_BUCKET_NAME: Artifacts bucket name
  - AWS_REGION: us-east-1