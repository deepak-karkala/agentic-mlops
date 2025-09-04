# Security group for RDS
resource "aws_security_group" "rds" {
  name_prefix = "${var.project}-rds-"
  vpc_id      = local.vpc_id

  ingress {
    from_port       = 5432
    to_port         = 5432
    protocol        = "tcp"
    security_groups = [aws_security_group.app_runner.id]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }

  tags = {
    Name = "${var.project}-rds-sg"
  }
}

resource "aws_db_subnet_group" "default" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = length(var.private_subnet_ids) > 0 ? var.private_subnet_ids : data.aws_subnets.default.ids
}

resource "aws_db_instance" "postgres" {
  identifier              = "${var.project}-db"
  engine                  = "postgres"
  engine_version          = "15.3"
  instance_class          = "db.t3.micro"
  allocated_storage       = 20
  username                = var.db_username
  password                = var.db_password
  db_subnet_group_name    = aws_db_subnet_group.default.name
  skip_final_snapshot     = true
  publicly_accessible     = false
  vpc_security_group_ids  = [aws_security_group.rds.id]
}

resource "aws_secretsmanager_secret" "db_credentials" {
  name = "${var.project}/db"
}

resource "aws_secretsmanager_secret_version" "db_credentials" {
  secret_id     = aws_secretsmanager_secret.db_credentials.id
  secret_string = jsonencode({ username = var.db_username, password = var.db_password })
}

resource "aws_db_proxy" "postgres" {
  name            = "${var.project}-proxy"
  engine_family   = "POSTGRESQL"
  role_arn        = aws_iam_role.rds_proxy.arn
  vpc_subnet_ids  = local.subnet_ids
  vpc_security_group_ids = [aws_security_group.rds.id]

  auth {
    auth_scheme = "SECRETS"
    description = "db auth"
    iam_auth    = "DISABLED"
    secret_arn  = aws_secretsmanager_secret.db_credentials.arn
  }
}

resource "aws_db_proxy_target" "db" {
  db_proxy_name        = aws_db_proxy.postgres.name
  target_group_name    = "default"
  db_instance_identifier = aws_db_instance.postgres.id
}
