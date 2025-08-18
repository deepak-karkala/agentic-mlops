data "aws_iam_policy_document" "apprunner_assume_role" {
  statement {
    effect = "Allow"
    principals {
      type        = "Service"
      identifiers = ["build.apprunner.amazonaws.com", "tasks.apprunner.amazonaws.com"]
    }
    actions = ["sts:AssumeRole"]
  }
}

resource "aws_iam_role" "api_service" {
  name               = "${var.project}-api-role"
  assume_role_policy = data.aws_iam_policy_document.apprunner_assume_role.json
}

resource "aws_iam_role" "worker_service" {
  name               = "${var.project}-worker-role"
  assume_role_policy = data.aws_iam_policy_document.apprunner_assume_role.json
}

resource "aws_iam_role_policy_attachment" "api_ecr" {
  role       = aws_iam_role.api_service.name
  policy_arn = "arn:aws:iam::aws:policy/AWSAppRunnerServicePolicyForECRAccess"
}

resource "aws_iam_role_policy_attachment" "worker_ecr" {
  role       = aws_iam_role.worker_service.name
  policy_arn = "arn:aws:iam::aws:policy/AWSAppRunnerServicePolicyForECRAccess"
}

data "aws_iam_policy_document" "api_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:*",
      "rds:*",
      "secretsmanager:GetSecretValue"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "api_policy" {
  name   = "${var.project}-api-policy"
  role   = aws_iam_role.api_service.id
  policy = data.aws_iam_policy_document.api_policy.json
}

data "aws_iam_policy_document" "worker_policy" {
  statement {
    effect = "Allow"
    actions = [
      "s3:*",
      "rds:*",
      "secretsmanager:GetSecretValue"
    ]
    resources = ["*"]
  }
}

resource "aws_iam_role_policy" "worker_policy" {
  name   = "${var.project}-worker-policy"
  role   = aws_iam_role.worker_service.id
  policy = data.aws_iam_policy_document.worker_policy.json
}

# Role for RDS Proxy to access Secrets Manager

data "aws_iam_policy_document" "rds_proxy_assume_role" {
  statement {
    actions = ["sts:AssumeRole"]
    principals {
      type        = "Service"
      identifiers = ["rds.amazonaws.com"]
    }
  }
}

resource "aws_iam_role" "rds_proxy" {
  name               = "${var.project}-rds-proxy-role"
  assume_role_policy = data.aws_iam_policy_document.rds_proxy_assume_role.json
}

resource "aws_iam_role_policy_attachment" "rds_proxy" {
  role       = aws_iam_role.rds_proxy.name
  policy_arn = "arn:aws:iam::aws:policy/AmazonRDSFullAccess"
}
