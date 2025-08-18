resource "aws_db_subnet_group" "default" {
  name       = "${var.project}-db-subnet-group"
  subnet_ids = var.private_subnet_ids
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
  vpc_security_group_ids  = []
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
  vpc_subnet_ids  = var.private_subnet_ids
  vpc_security_group_ids = []

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
