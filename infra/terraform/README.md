# AWS Infrastructure Bootstrap

Terraform configuration for provisioning the core AWS resources required by the Agentic MLOps MVP.

## Resources

- **App Runner Services** for API and Worker containers.
- **RDS Postgres** instance with an RDS Proxy for connection pooling.
- **S3 Bucket** for storing generated artifacts.
- **IAM Roles** for services and database proxy.

## Usage

```bash
cd infra/terraform
terraform init -backend-config="bucket=STATE_BUCKET" -backend-config="key=terraform.tfstate" -backend-config="region=us-east-1"
terraform apply \
  -var "artifact_bucket_name=YOUR_BUCKET" \
  -var "api_image=ECR_IMAGE_FOR_API" \
  -var "worker_image=ECR_IMAGE_FOR_WORKER" \
  -var "db_username=postgres" \
  -var "db_password=changeme"
```

Additional variables such as `vpc_id` and `private_subnet_ids` may be supplied to place the database in existing networking infrastructure.
