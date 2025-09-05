# Security group for App Runner services
resource "aws_security_group" "app_runner" {
  name_prefix = "${var.project}-apprunner-"
  vpc_id      = local.vpc_id

  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-apprunner-sg"
  }
}

# VPC Connector for App Runner to access RDS
resource "aws_apprunner_vpc_connector" "main" {
  vpc_connector_name = "${var.project}-vpc-connector"
  subnets            = local.subnet_ids
  security_groups    = [aws_security_group.app_runner.id]
}

resource "aws_apprunner_service" "api" {
  count = var.api_image != "" ? 1 : 0

  service_name = "${var.project}-api"

  source_configuration {
    image_repository {
      image_identifier      = var.api_image
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
        runtime_environment_variables = {
          DATABASE_URL   = "postgresql://postgres:${var.db_password}@${aws_db_proxy.postgres.endpoint}:5432/postgres"
          S3_BUCKET_NAME = aws_s3_bucket.artifacts.bucket
          AWS_REGION     = var.region
        }
      }
    }
    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.main.arn
    }
  }
}

resource "aws_apprunner_service" "worker" {
  count = var.worker_image != "" ? 1 : 0

  service_name = "${var.project}-worker"

  source_configuration {
    image_repository {
      image_identifier      = var.worker_image
      image_repository_type = "ECR"
      image_configuration {
        port = "8080"
        runtime_environment_variables = {
          DATABASE_URL   = "postgresql://postgres:${var.db_password}@${aws_db_proxy.postgres.endpoint}:5432/postgres"
          S3_BUCKET_NAME = aws_s3_bucket.artifacts.bucket
          AWS_REGION     = var.region
        }
      }
    }
    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  network_configuration {
    egress_configuration {
      egress_type       = "VPC"
      vpc_connector_arn = aws_apprunner_vpc_connector.main.arn
    }
  }
}
