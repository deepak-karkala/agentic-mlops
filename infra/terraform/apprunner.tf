resource "aws_apprunner_service" "api" {
  service_name = "${var.project}-api"

  source_configuration {
    image_repository {
      image_identifier      = var.api_image
      image_repository_type = "ECR"
      image_configuration {
        port = "8000"
      }
    }
    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  service_role_arn = aws_iam_role.api_service.arn
}

resource "aws_apprunner_service" "worker" {
  service_name = "${var.project}-worker"

  source_configuration {
    image_repository {
      image_identifier      = var.worker_image
      image_repository_type = "ECR"
      image_configuration {
        port = "8080"
      }
    }
    auto_deployments_enabled = false
  }

  instance_configuration {
    cpu    = "1024"
    memory = "2048"
  }

  service_role_arn = aws_iam_role.worker_service.arn
}
