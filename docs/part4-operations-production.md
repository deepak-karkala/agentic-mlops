# Part 4: Operations & Production
# Agentic MLOps Platform

**Version:** 1.0
**Date:** January 2025
**Classification:** Operations & Production Guide

---

## Table of Contents
1. [Deployment Architecture](#1-deployment-architecture)
2. [Security & Performance](#2-security--performance)
3. [Testing Strategy](#3-testing-strategy)
4. [Error Handling Strategy](#4-error-handling-strategy)
5. [Monitoring & Observability](#5-monitoring--observability)

---

## 1. Deployment Architecture

### 1.1 Current Production Architecture

#### 1.1.1 AWS Infrastructure Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                        AWS Cloud (us-east-1)                     │
│                                                                   │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │                     Public Internet                       │   │
│  │                            │                              │   │
│  │                            ▼                              │   │
│  │  ┌──────────────────────────────────────────────────┐   │   │
│  │  │          CloudFront CDN (Future)                 │   │   │
│  │  └────────────────┬─────────────────────────────────┘   │   │
│  │                   │                                       │   │
│  │         ┌─────────┴─────────┐                            │   │
│  │         ▼                   ▼                            │   │
│  │  ┌─────────────┐     ┌─────────────┐                    │   │
│  │  │ App Runner  │     │ App Runner  │                    │   │
│  │  │  Frontend   │     │  API+Worker │                    │   │
│  │  │  (Next.js)  │     │  (FastAPI)  │                    │   │
│  │  └──────┬──────┘     └──────┬──────┘                    │   │
│  │         │                    │                            │   │
│  │         │                    │ SSE Streaming             │   │
│  │         └────────────────────┘                            │   │
│  │                              │                            │   │
│  └──────────────────────────────┼────────────────────────────┘   │
│                                 │                                │
│  ┌──────────────────────────────┼────────────────────────────┐   │
│  │              VPC (Default)   ▼                            │   │
│  │                    ┌─────────────────┐                    │   │
│  │                    │  VPC Connector  │                    │   │
│  │                    └────────┬────────┘                    │   │
│  │                             │                             │   │
│  │           ┌─────────────────┼─────────────────┐          │   │
│  │           ▼                 ▼                 ▼          │   │
│  │    ┌────────────┐   ┌────────────┐   ┌────────────┐    │   │
│  │    │   RDS      │   │    RDS     │   │     S3     │    │   │
│  │    │ PostgreSQL │◄──│   Proxy    │   │  Artifacts │    │   │
│  │    │            │   │            │   │            │    │   │
│  │    └────────────┘   └────────────┘   └────────────┘    │   │
│  │                                                           │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
│  ┌───────────────────────────────────────────────────────────┐   │
│  │                   Supporting Services                      │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │  CloudWatch  │  │     IAM      │  │     ECR      │   │   │
│  │  │     Logs     │  │    Roles     │  │  Registries  │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  │                                                             │   │
│  │  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐   │   │
│  │  │   Secrets    │  │     KMS      │  │   X-Ray      │   │   │
│  │  │   Manager    │  │  Encryption  │  │   Tracing    │   │   │
│  │  │  (Future)    │  │   (Future)   │  │   (Future)   │   │   │
│  │  └──────────────┘  └──────────────┘  └──────────────┘   │   │
│  └───────────────────────────────────────────────────────────┘   │
│                                                                   │
└───────────────────────────────────────────────────────────────────┘
```

#### 1.1.2 Service Communication Flow

```
User Browser
    │
    ├──── HTTP/HTTPS ────► App Runner (Frontend)
    │                            │
    │                            │ Static Assets
    │                            │ Server-Side Rendering
    │                            ▼
    │                      Next.js Server
    │
    └──── HTTP/HTTPS ────► App Runner (API+Worker)
          SSE Streaming          │
                                 ├──► REST API Endpoints
                                 ├──► SSE Streaming
                                 ├──► Background Worker
                                 │
                                 ├──► RDS Proxy
                                 │      │
                                 │      └──► PostgreSQL
                                 │           - Job Queue
                                 │           - Decision Sets
                                 │           - LangGraph Checkpoints
                                 │
                                 ├──► S3 Bucket
                                 │      - Generated Artifacts
                                 │      - Code Repositories
                                 │
                                 ├──► OpenAI API
                                 │      - Agent Reasoning
                                 │
                                 ├──► Anthropic API
                                 │      - Code Generation
                                 │
                                 └──► LangSmith API
                                        - Agent Tracing
```

### 1.2 Deployment Process

#### 1.2.1 Infrastructure Deployment (Terraform)

```bash
# scripts/1-deploy-infrastructure.sh
#!/bin/bash
set -e

echo "=== Deploying Agentic MLOps Infrastructure ==="

# Step 1: Create S3 backend for Terraform state
echo "Creating S3 backend for Terraform state..."
BUCKET_NAME="agentic-mlops-terraform-state-$(date +%s)"
aws s3 mb "s3://${BUCKET_NAME}" --region us-east-1

# Step 2: Initialize Terraform
cd infra/terraform
terraform init \
  -backend-config="bucket=${BUCKET_NAME}" \
  -backend-config="key=terraform.tfstate" \
  -backend-config="region=us-east-1"

# Step 3: Get VPC and subnet information
DEFAULT_VPC=$(aws ec2 describe-vpcs --filters "Name=is-default,Values=true" --query "Vpcs[0].VpcId" --output text)
SUBNETS=$(aws ec2 describe-subnets --filters "Name=vpc-id,Values=${DEFAULT_VPC}" --query "Subnets[*].SubnetId" --output text | tr '\t' ',')

echo "Using VPC: ${DEFAULT_VPC}"
echo "Using Subnets: ${SUBNETS}"

# Step 4: Plan and apply infrastructure
terraform plan \
  -var="vpc_id=${DEFAULT_VPC}" \
  -var="subnet_ids=${SUBNETS}" \
  -out=tfplan

terraform apply tfplan

echo "=== Infrastructure deployment complete ==="
```

**Key Resources Created:**
- ECR repositories for API and Frontend images
- RDS PostgreSQL database with automated backups
- RDS Proxy for connection pooling
- S3 bucket for artifacts with versioning
- VPC connector for App Runner
- IAM roles with least-privilege policies
- Security groups for network isolation

#### 1.2.2 Container Build & Push

```bash
# scripts/2-build-and-push.sh
#!/bin/bash
set -e

echo "=== Building and Pushing Containers ==="

AWS_REGION="us-east-1"
AWS_ACCOUNT_ID=$(aws sts get-caller-identity --query Account --output text)

# Authenticate with ECR
echo "Authenticating with ECR..."
aws ecr get-login-password --region ${AWS_REGION} | \
  docker login --username AWS --password-stdin \
  ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com

# Get ECR repository URIs from Terraform
cd infra/terraform
API_REPO=$(terraform output -raw api_ecr_repository_url)
FRONTEND_REPO=$(terraform output -raw frontend_ecr_repository_url)
cd ../..

# Build API image
echo "Building API image..."
docker build -t agentic-mlops-api:latest -f api/Dockerfile .
docker tag agentic-mlops-api:latest ${API_REPO}:latest
docker tag agentic-mlops-api:latest ${API_REPO}:$(git rev-parse --short HEAD)
docker push ${API_REPO}:latest
docker push ${API_REPO}:$(git rev-parse --short HEAD)

# Build Frontend image
echo "Building Frontend image..."
docker build -t agentic-mlops-frontend:latest -f frontend/Dockerfile ./frontend
docker tag agentic-mlops-frontend:latest ${FRONTEND_REPO}:latest
docker tag agentic-mlops-frontend:latest ${FRONTEND_REPO}:$(git rev-parse --short HEAD)
docker push ${FRONTEND_REPO}:latest
docker push ${FRONTEND_REPO}:$(git rev-parse --short HEAD)

# Save image URIs for App Runner deployment
echo "API_IMAGE=${API_REPO}:latest" > deployment-config.env
echo "FRONTEND_IMAGE=${FRONTEND_REPO}:latest" >> deployment-config.env

echo "=== Container build and push complete ==="
```

#### 1.2.3 App Runner Deployment

```bash
# scripts/3-deploy-app-runner.sh
#!/bin/bash
set -e

echo "=== Deploying App Runner Services ==="

# Source image URIs
source deployment-config.env

cd infra/terraform

# Update Terraform variables with new images
terraform apply \
  -var="api_image_uri=${API_IMAGE}" \
  -var="frontend_image_uri=${FRONTEND_IMAGE}" \
  -auto-approve

# Get service URLs
API_URL=$(terraform output -raw api_service_url)
FRONTEND_URL=$(terraform output -raw frontend_service_url)

echo ""
echo "=== Deployment Complete ==="
echo "Frontend URL: ${FRONTEND_URL}"
echo "API URL: ${API_URL}"
echo "API Docs: ${API_URL}/docs"

cd ../..
```

### 1.3 High Availability & Disaster Recovery

#### 1.3.1 Current HA Configuration

**App Runner:**
- Auto-scaling: 1-10 instances based on CPU/memory
- Health checks: HTTP endpoint monitoring
- Automatic failover: Instance replacement on failure
- Multi-AZ deployment: Automatic by AWS

**RDS PostgreSQL:**
- Multi-AZ deployment: Automatic failover
- Automated backups: Daily snapshots (7-day retention)
- Point-in-time recovery: Up to backup retention period
- Connection pooling: RDS Proxy for resilience

**S3:**
- 11 9's durability (99.999999999%)
- Versioning enabled: Recover deleted objects
- Cross-region replication: Not currently enabled

#### 1.3.2 Disaster Recovery Strategy (Recommended Implementation)

**RTO (Recovery Time Objective): 1 hour**
**RPO (Recovery Point Objective): 5 minutes**

```terraform
# infra/terraform/rds-dr.tf (RECOMMENDED ADDITION)
resource "aws_db_instance_automated_backups_replication" "rds_backup_replication" {
  source_db_instance_arn = aws_db_instance.postgres.arn
  retention_period       = 14  # Extend to 14 days for compliance
}

# Cross-region read replica for disaster recovery
resource "aws_db_instance" "postgres_replica" {
  identifier             = "agentic-mlops-postgres-replica"
  replicate_source_db    = aws_db_instance.postgres.identifier
  instance_class         = aws_db_instance.postgres.instance_class

  # Deploy in different region
  provider = aws.disaster_recovery  # Configure DR region provider

  backup_retention_period = 14
  skip_final_snapshot    = false
  final_snapshot_identifier = "agentic-mlops-postgres-replica-final"

  tags = {
    Name        = "Agentic MLOps Postgres Replica"
    Environment = "disaster-recovery"
  }
}

# S3 cross-region replication
resource "aws_s3_bucket_replication_configuration" "artifacts_replication" {
  bucket = aws_s3_bucket.artifacts.id
  role   = aws_iam_role.replication.arn

  rule {
    id     = "replicate-artifacts"
    status = "Enabled"

    destination {
      bucket        = aws_s3_bucket.artifacts_replica.arn
      storage_class = "STANDARD_IA"  # Cheaper storage for DR
    }
  }
}
```

**DR Runbook:**
```bash
#!/bin/bash
# scripts/disaster-recovery.sh

echo "=== Agentic MLOps Disaster Recovery Procedure ==="

# 1. Promote read replica to primary
aws rds promote-read-replica \
  --db-instance-identifier agentic-mlops-postgres-replica \
  --region us-west-2

# 2. Update RDS Proxy to point to new primary
aws rds-proxy update-db-proxy \
  --db-proxy-name agentic-mlops-rds-proxy \
  --db-instance-identifier agentic-mlops-postgres-replica

# 3. Update Terraform state with new configuration
cd infra/terraform
terraform import aws_db_instance.postgres agentic-mlops-postgres-replica

# 4. Redeploy App Runner services with updated DATABASE_URL
terraform apply -var="disaster_recovery=true"

# 5. Verify services
./scripts/test-e2e.sh

echo "=== Disaster Recovery Complete ==="
```

---

## 2. Security & Performance

### 2.1 Security Architecture

#### 2.1.1 Authentication & Authorization (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Not implemented
**Priority:** High
**Implementation Plan:**

```python
# libs/auth.py (NEW FILE TO CREATE)
from fastapi import HTTPException, Security
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
import jwt
from datetime import datetime, timedelta
from typing import Optional

# JWT Configuration
JWT_SECRET = os.getenv("JWT_SECRET")  # Store in AWS Secrets Manager
JWT_ALGORITHM = "HS256"
JWT_EXPIRATION_HOURS = 24

security = HTTPBearer()

class User:
    """User model for authentication."""
    def __init__(self, user_id: str, email: str, roles: list[str]):
        self.user_id = user_id
        self.email = email
        self.roles = roles

def create_access_token(user: User) -> str:
    """Create JWT access token."""
    payload = {
        "user_id": user.user_id,
        "email": user.email,
        "roles": user.roles,
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRATION_HOURS),
        "iat": datetime.utcnow(),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_token(token: str) -> User:
    """Verify and decode JWT token."""
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return User(
            user_id=payload["user_id"],
            email=payload["email"],
            roles=payload["roles"]
        )
    except jwt.ExpiredSignatureError:
        raise HTTPException(status_code=401, detail="Token expired")
    except jwt.InvalidTokenError:
        raise HTTPException(status_code=401, detail="Invalid token")

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Security(security)
) -> User:
    """FastAPI dependency for protected endpoints."""
    return verify_token(credentials.credentials)

def require_role(required_role: str):
    """Decorator for role-based access control."""
    def decorator(func):
        async def wrapper(*args, current_user: User = Security(get_current_user), **kwargs):
            if required_role not in current_user.roles:
                raise HTTPException(status_code=403, detail="Insufficient permissions")
            return await func(*args, current_user=current_user, **kwargs)
        return wrapper
    return decorator
```

**Updated API with Authentication:**
```python
# api/main.py (MODIFICATIONS)
from libs.auth import get_current_user, require_role, User

# Protect endpoints
@app.post("/api/chat/async", response_model=AsyncChatResponse)
async def chat_async(
    req: ChatRequest,
    current_user: User = Security(get_current_user),  # Require auth
    db: Session = Depends(get_db)
) -> AsyncChatResponse:
    """Authenticated async chat endpoint."""
    logger.info(f"Chat request from user: {current_user.email}")

    # Create decision set with user tracking
    decision_set = create_decision_set_for_thread(
        db, thread_id, user_prompt, user_id=current_user.user_id
    )
    # ... rest of implementation

# Admin-only endpoints
@app.get("/api/admin/users")
@require_role("admin")
async def list_users(current_user: User = Security(get_current_user)):
    """Admin endpoint to list users."""
    pass
```

**AWS Cognito Integration (Recommended):**
```python
# libs/auth_cognito.py (ALTERNATIVE IMPLEMENTATION)
import boto3
from jose import jwt, JWTError
from fastapi import HTTPException

# AWS Cognito configuration
COGNITO_REGION = os.getenv("AWS_REGION", "us-east-1")
COGNITO_USER_POOL_ID = os.getenv("COGNITO_USER_POOL_ID")
COGNITO_CLIENT_ID = os.getenv("COGNITO_CLIENT_ID")

# Get Cognito JWT public keys
cognito_client = boto3.client("cognito-idp", region_name=COGNITO_REGION)
jwks_url = f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}/.well-known/jwks.json"

async def verify_cognito_token(token: str) -> User:
    """Verify AWS Cognito JWT token."""
    try:
        # Fetch JWKs and verify signature
        keys = requests.get(jwks_url).json()["keys"]

        # Decode and verify token
        unverified_header = jwt.get_unverified_header(token)
        rsa_key = next((key for key in keys if key["kid"] == unverified_header["kid"]), None)

        if not rsa_key:
            raise HTTPException(status_code=401, detail="Invalid token")

        payload = jwt.decode(
            token,
            rsa_key,
            algorithms=["RS256"],
            audience=COGNITO_CLIENT_ID,
            issuer=f"https://cognito-idp.{COGNITO_REGION}.amazonaws.com/{COGNITO_USER_POOL_ID}"
        )

        return User(
            user_id=payload["sub"],
            email=payload["email"],
            roles=payload.get("cognito:groups", [])
        )
    except JWTError as e:
        raise HTTPException(status_code=401, detail=f"Token validation failed: {str(e)}")
```

**Terraform for Cognito:**
```terraform
# infra/terraform/cognito.tf (NEW FILE TO CREATE)
resource "aws_cognito_user_pool" "main" {
  name = "agentic-mlops-users"

  password_policy {
    minimum_length    = 12
    require_lowercase = true
    require_uppercase = true
    require_numbers   = true
    require_symbols   = true
  }

  mfa_configuration = "OPTIONAL"

  account_recovery_setting {
    recovery_mechanism {
      name     = "verified_email"
      priority = 1
    }
  }

  tags = {
    Name        = "Agentic MLOps User Pool"
    Environment = var.environment
  }
}

resource "aws_cognito_user_pool_client" "main" {
  name         = "agentic-mlops-client"
  user_pool_id = aws_cognito_user_pool.main.id

  explicit_auth_flows = [
    "ALLOW_USER_PASSWORD_AUTH",
    "ALLOW_REFRESH_TOKEN_AUTH"
  ]

  generate_secret = true
}

output "cognito_user_pool_id" {
  value = aws_cognito_user_pool.main.id
}

output "cognito_client_id" {
  value = aws_cognito_user_pool_client.main.id
}
```

#### 2.1.2 API Rate Limiting (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Not implemented
**Priority:** High
**Implementation Plan:**

```python
# libs/rate_limiting.py (NEW FILE TO CREATE)
from fastapi import HTTPException, Request
from collections import defaultdict
from datetime import datetime, timedelta
import asyncio

class RateLimiter:
    """
    Token bucket rate limiter with per-user and per-IP tracking.

    Strategy:
    - Token bucket algorithm for smooth rate limiting
    - Per-user limits: 100 req/min, 1000 req/hour
    - Per-IP limits: 20 req/min (anonymous users)
    - Burst allowance: 150% of rate limit
    """

    def __init__(self):
        self.user_buckets = defaultdict(lambda: {"tokens": 100, "last_update": datetime.now()})
        self.ip_buckets = defaultdict(lambda: {"tokens": 20, "last_update": datetime.now()})

        # Rate limit configuration
        self.user_rate = 100  # tokens per minute
        self.ip_rate = 20  # tokens per minute
        self.user_burst = 150  # max tokens
        self.ip_burst = 30  # max tokens

    def _refill_bucket(self, bucket: dict, rate: int, burst: int):
        """Refill tokens based on elapsed time."""
        now = datetime.now()
        elapsed = (now - bucket["last_update"]).total_seconds() / 60.0  # minutes

        # Add tokens based on rate and elapsed time
        bucket["tokens"] = min(
            burst,
            bucket["tokens"] + (rate * elapsed)
        )
        bucket["last_update"] = now

    async def check_rate_limit(self, request: Request, user_id: str = None):
        """
        Check if request is within rate limits.

        Args:
            request: FastAPI request object
            user_id: Optional user ID (use IP if anonymous)

        Raises:
            HTTPException: 429 if rate limit exceeded
        """
        if user_id:
            # Authenticated user: use user-based rate limit
            bucket = self.user_buckets[user_id]
            self._refill_bucket(bucket, self.user_rate, self.user_burst)

            if bucket["tokens"] < 1:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Try again in 1 minute.",
                    headers={"Retry-After": "60"}
                )

            bucket["tokens"] -= 1
        else:
            # Anonymous user: use IP-based rate limit
            client_ip = request.client.host
            bucket = self.ip_buckets[client_ip]
            self._refill_bucket(bucket, self.ip_rate, self.ip_burst)

            if bucket["tokens"] < 1:
                raise HTTPException(
                    status_code=429,
                    detail="Rate limit exceeded. Please authenticate or try again later.",
                    headers={"Retry-After": "60"}
                )

            bucket["tokens"] -= 1

# Global rate limiter instance
rate_limiter = RateLimiter()

# FastAPI dependency
async def rate_limit_dependency(
    request: Request,
    user: User = Security(get_current_user, scopes=[])
):
    """FastAPI dependency for rate limiting."""
    user_id = user.user_id if user else None
    await rate_limiter.check_rate_limit(request, user_id)
```

**Apply Rate Limiting to Endpoints:**
```python
# api/main.py (MODIFICATIONS)
from libs.rate_limiting import rate_limit_dependency

@app.post("/api/chat/async")
async def chat_async(
    req: ChatRequest,
    _: None = Depends(rate_limit_dependency),  # Apply rate limiting
    current_user: User = Security(get_current_user),
    db: Session = Depends(get_db)
):
    """Rate-limited async chat endpoint."""
    pass
```

**Redis-based Rate Limiting (Production):**
```python
# libs/rate_limiting_redis.py (PRODUCTION IMPLEMENTATION)
import redis.asyncio as redis
from fastapi import HTTPException

class RedisRateLimiter:
    """Production-ready rate limiter using Redis."""

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int
    ):
        """
        Sliding window rate limiting with Redis.

        Args:
            key: Unique identifier (user_id or IP)
            limit: Maximum requests per window
            window_seconds: Time window in seconds
        """
        now = datetime.now().timestamp()
        window_start = now - window_seconds

        # Use Redis sorted set for sliding window
        pipe = self.redis.pipeline()

        # Remove old entries
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, window_seconds)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= limit:
            raise HTTPException(
                status_code=429,
                detail=f"Rate limit exceeded: {limit} requests per {window_seconds}s",
                headers={"Retry-After": str(window_seconds)}
            )
```

#### 2.1.3 Input Validation & Sanitization

**Current State:** ✅ Partially implemented (Pydantic validation)
**Enhancements Needed:**

```python
# libs/security.py (NEW FILE TO CREATE)
import re
from typing import Any
from fastapi import HTTPException

class InputValidator:
    """Enhanced input validation and sanitization."""

    @staticmethod
    def sanitize_sql(value: str) -> str:
        """Prevent SQL injection."""
        # Remove dangerous SQL keywords
        dangerous_patterns = [
            r";\s*DROP",
            r";\s*DELETE",
            r";\s*UPDATE",
            r"--",
            r"/\*",
            r"\*/",
            r"xp_",
            r"sp_"
        ]

        for pattern in dangerous_patterns:
            if re.search(pattern, value, re.IGNORECASE):
                raise HTTPException(
                    status_code=400,
                    detail="Invalid input: potential SQL injection detected"
                )

        return value

    @staticmethod
    def sanitize_prompt(prompt: str) -> str:
        """Sanitize user prompts to prevent prompt injection."""
        # Maximum prompt length
        MAX_PROMPT_LENGTH = 10000

        if len(prompt) > MAX_PROMPT_LENGTH:
            raise HTTPException(
                status_code=400,
                detail=f"Prompt too long: maximum {MAX_PROMPT_LENGTH} characters"
            )

        # Remove control characters
        prompt = re.sub(r'[\x00-\x1f\x7f-\x9f]', '', prompt)

        # Detect potential prompt injection patterns
        injection_patterns = [
            r"ignore previous instructions",
            r"disregard.*above",
            r"forget.*instructions",
            r"new instructions:",
            r"system.*:",
        ]

        for pattern in injection_patterns:
            if re.search(pattern, prompt, re.IGNORECASE):
                # Log warning but don't reject (could be legitimate)
                logger.warning(f"Potential prompt injection detected: {pattern}")

        return prompt.strip()

    @staticmethod
    def validate_json_payload(payload: dict, max_depth: int = 10) -> dict:
        """Validate JSON payload depth to prevent DoS attacks."""

        def check_depth(obj: Any, current_depth: int = 0):
            if current_depth > max_depth:
                raise HTTPException(
                    status_code=400,
                    detail=f"JSON payload too deeply nested: maximum depth {max_depth}"
                )

            if isinstance(obj, dict):
                for value in obj.values():
                    check_depth(value, current_depth + 1)
            elif isinstance(obj, list):
                for item in obj:
                    check_depth(item, current_depth + 1)

        check_depth(payload)
        return payload
```

**Apply Validation:**
```python
# api/main.py (MODIFICATIONS)
from libs.security import InputValidator

validator = InputValidator()

@app.post("/api/chat/async")
async def chat_async(req: ChatRequest, ...):
    # Extract user prompt
    user_prompt = req.messages[-1].content

    # Sanitize prompt
    user_prompt = validator.sanitize_prompt(user_prompt)

    # Validate JSON payload
    payload = validator.validate_json_payload(req.dict())

    # Continue processing...
```

#### 2.1.4 Secret Management (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Environment variables only
**Priority:** High
**Implementation Plan:**

```terraform
# infra/terraform/secrets.tf (NEW FILE TO CREATE)
resource "aws_secretsmanager_secret" "openai_api_key" {
  name        = "agentic-mlops/openai-api-key"
  description = "OpenAI API key for LLM agents"

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "openai_api_key" {
  secret_id     = aws_secretsmanager_secret.openai_api_key.id
  secret_string = var.openai_api_key  # Passed via Terraform variables
}

resource "aws_secretsmanager_secret" "anthropic_api_key" {
  name        = "agentic-mlops/anthropic-api-key"
  description = "Anthropic API key for Claude Code generation"

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "anthropic_api_key" {
  secret_id     = aws_secretsmanager_secret.anthropic_api_key.id
  secret_string = var.anthropic_api_key
}

resource "aws_secretsmanager_secret" "jwt_secret" {
  name        = "agentic-mlops/jwt-secret"
  description = "JWT secret for token signing"

  recovery_window_in_days = 7
}

resource "aws_secretsmanager_secret_version" "jwt_secret" {
  secret_id     = aws_secretsmanager_secret.jwt_secret.id
  secret_string = var.jwt_secret
}

# IAM policy for App Runner to access secrets
resource "aws_iam_policy" "secrets_access" {
  name        = "agentic-mlops-secrets-access"
  description = "Allow App Runner to access Secrets Manager"

  policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Effect = "Allow"
        Action = [
          "secretsmanager:GetSecretValue",
          "secretsmanager:DescribeSecret"
        ]
        Resource = [
          aws_secretsmanager_secret.openai_api_key.arn,
          aws_secretsmanager_secret.anthropic_api_key.arn,
          aws_secretsmanager_secret.jwt_secret.arn
        ]
      }
    ]
  })
}

resource "aws_iam_role_policy_attachment" "apprunner_secrets" {
  role       = aws_iam_role.apprunner_instance_role.name
  policy_arn = aws_iam_policy.secrets_access.arn
}
```

**Fetch Secrets at Runtime:**
```python
# libs/secrets.py (NEW FILE TO CREATE)
import boto3
import json
from functools import lru_cache

class SecretsManager:
    """AWS Secrets Manager integration."""

    def __init__(self, region: str = "us-east-1"):
        self.client = boto3.client("secretsmanager", region_name=region)

    @lru_cache(maxsize=128)
    def get_secret(self, secret_name: str) -> str:
        """
        Fetch secret from AWS Secrets Manager with caching.

        Args:
            secret_name: Name of the secret

        Returns:
            Secret value as string
        """
        try:
            response = self.client.get_secret_value(SecretId=secret_name)
            return response["SecretString"]
        except Exception as e:
            logger.error(f"Failed to fetch secret {secret_name}: {e}")
            # Fallback to environment variable
            return os.getenv(secret_name.split("/")[-1].upper().replace("-", "_"))

    def get_secret_json(self, secret_name: str) -> dict:
        """Fetch and parse JSON secret."""
        secret_string = self.get_secret(secret_name)
        return json.loads(secret_string)

# Global secrets manager
secrets_manager = SecretsManager()

# Helper functions
def get_openai_api_key() -> str:
    """Get OpenAI API key from Secrets Manager."""
    if os.getenv("ENVIRONMENT") == "production":
        return secrets_manager.get_secret("agentic-mlops/openai-api-key")
    return os.getenv("OPENAI_API_KEY")

def get_anthropic_api_key() -> str:
    """Get Anthropic API key from Secrets Manager."""
    if os.getenv("ENVIRONMENT") == "production":
        return secrets_manager.get_secret("agentic-mlops/anthropic-api-key")
    return os.getenv("ANTHROPIC_API_KEY")

def get_jwt_secret() -> str:
    """Get JWT secret from Secrets Manager."""
    if os.getenv("ENVIRONMENT") == "production":
        return secrets_manager.get_secret("agentic-mlops/jwt-secret")
    return os.getenv("JWT_SECRET", "dev-secret-change-me")
```

**Update LLM Clients:**
```python
# libs/llm_client.py (MODIFICATIONS)
from libs.secrets import get_openai_api_key, get_anthropic_api_key

# Instead of:
# client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Use:
client = OpenAI(api_key=get_openai_api_key())
claude = ClaudeCode(api_key=get_anthropic_api_key())
```

### 2.2 Performance Optimization

#### 2.2.1 Database Query Optimization (RECOMMENDED IMPLEMENTATION)

**Current State:** ✅ Basic indexes
**Enhancements Needed:**

```python
# libs/models.py (ADD INDEXES)

# Add composite indexes for common queries
from sqlalchemy import Index

class Job(Base):
    __tablename__ = "jobs"

    # ... existing columns ...

    # Add composite index for job claiming query
    __table_args__ = (
        Index(
            'idx_job_claim_optimization',
            'status', 'priority', 'created_at',
            postgresql_where=(status == 'queued'),  # Partial index
        ),
        Index(
            'idx_job_worker_lease',
            'worker_id', 'lease_expires_at',
            postgresql_where=(status == 'running'),
        ),
    )

class DecisionSet(Base):
    __tablename__ = "decision_sets"

    # ... existing columns ...

    __table_args__ = (
        Index('idx_decision_set_user_lookup', 'user_id', 'created_at'),
        Index('idx_decision_set_status', 'status', 'updated_at'),
    )
```

**Query Optimization Patterns:**
```python
# libs/job_service.py (OPTIMIZATIONS)

def get_user_jobs(self, user_id: str, limit: int = 50) -> List[Job]:
    """
    Optimized query to get user's recent jobs.

    Optimizations:
    - Use index on (user_id, created_at)
    - Limit results to reduce memory
    - Use joinedload for eager loading relationships
    """
    from sqlalchemy.orm import joinedload

    return (
        self.session.query(Job)
        .join(DecisionSet)
        .filter(DecisionSet.user_id == user_id)
        .options(joinedload(Job.decision_set))  # Eager load to avoid N+1
        .order_by(Job.created_at.desc())
        .limit(limit)
        .all()
    )

def get_job_statistics(self, user_id: str) -> dict:
    """
    Optimized aggregation query for job statistics.

    Uses SQL aggregation instead of loading all rows.
    """
    from sqlalchemy import func

    stats = (
        self.session.query(
            Job.status,
            func.count(Job.id).label('count'),
            func.avg(
                func.extract('epoch', Job.completed_at - Job.started_at)
            ).label('avg_duration_seconds')
        )
        .join(DecisionSet)
        .filter(DecisionSet.user_id == user_id)
        .group_by(Job.status)
        .all()
    )

    return {
        stat.status: {
            "count": stat.count,
            "avg_duration_seconds": stat.avg_duration_seconds
        }
        for stat in stats
    }
```

**Connection Pooling Optimization:**
```python
# libs/database.py (ENHANCEMENTS)

def create_database_engine():
    """
    Create optimized database engine with connection pooling.

    Pool Configuration:
    - pool_size: 10 connections (base)
    - max_overflow: 20 connections (burst)
    - pool_timeout: 30s (wait time)
    - pool_recycle: 3600s (1 hour - prevent stale connections)
    - pool_pre_ping: True (check connection health)
    """
    database_url = os.getenv("DATABASE_URL", "sqlite:///./agentic_mlops.db")

    if "postgresql" in database_url:
        engine = create_engine(
            database_url,
            pool_size=10,
            max_overflow=20,
            pool_timeout=30,
            pool_recycle=3600,
            pool_pre_ping=True,
            echo=False,
            # Connection pool optimization
            poolclass=QueuePool,
            pool_reset_on_return='rollback',
        )
    else:
        # SQLite configuration
        engine = create_engine(
            database_url,
            connect_args={"check_same_thread": False},
            echo=False
        )

    return engine
```

#### 2.2.2 Redis Caching Layer (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Not implemented
**Priority:** Medium
**Implementation Plan:**

```terraform
# infra/terraform/elasticache.tf (NEW FILE TO CREATE)
resource "aws_elasticache_subnet_group" "redis" {
  name       = "agentic-mlops-redis-subnet-group"
  subnet_ids = var.subnet_ids
}

resource "aws_security_group" "redis" {
  name        = "agentic-mlops-redis-sg"
  description = "Security group for Redis cluster"
  vpc_id      = var.vpc_id

  ingress {
    description = "Redis from App Runner"
    from_port   = 6379
    to_port     = 6379
    protocol    = "tcp"
    cidr_blocks = [var.vpc_cidr]
  }

  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

resource "aws_elasticache_cluster" "redis" {
  cluster_id           = "agentic-mlops-redis"
  engine               = "redis"
  node_type            = "cache.t3.micro"  # Start small, scale as needed
  num_cache_nodes      = 1
  parameter_group_name = "default.redis7"
  engine_version       = "7.0"
  port                 = 6379

  subnet_group_name    = aws_elasticache_subnet_group.redis.name
  security_group_ids   = [aws_security_group.redis.id]

  tags = {
    Name        = "Agentic MLOps Redis"
    Environment = var.environment
  }
}

output "redis_endpoint" {
  value = aws_elasticache_cluster.redis.cache_nodes[0].address
}
```

**Redis Cache Implementation:**
```python
# libs/cache.py (NEW FILE TO CREATE)
import redis.asyncio as redis
import json
import hashlib
from typing import Optional, Any
from functools import wraps

class CacheManager:
    """
    Redis-based caching with automatic serialization.

    Cache Strategy:
    - Agent outputs: 1 hour TTL (agents are deterministic)
    - User sessions: 24 hour TTL
    - Template data: 7 day TTL (rarely changes)
    - LLM responses: 1 hour TTL (cost optimization)
    """

    def __init__(self, redis_url: str):
        self.redis = redis.from_url(redis_url)

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        value = await self.redis.get(key)
        if value:
            return json.loads(value)
        return None

    async def set(
        self,
        key: str,
        value: Any,
        ttl_seconds: int = 3600
    ):
        """Set value in cache with TTL."""
        await self.redis.set(
            key,
            json.dumps(value),
            ex=ttl_seconds
        )

    async def delete(self, key: str):
        """Delete key from cache."""
        await self.redis.delete(key)

    async def get_many(self, keys: list[str]) -> dict:
        """Get multiple keys (pipeline for efficiency)."""
        if not keys:
            return {}

        pipe = self.redis.pipeline()
        for key in keys:
            pipe.get(key)

        values = await pipe.execute()
        return {
            key: json.loads(value) if value else None
            for key, value in zip(keys, values)
        }

    def cache_key(self, prefix: str, *args, **kwargs) -> str:
        """Generate cache key from function arguments."""
        # Create deterministic key from arguments
        key_parts = [prefix]
        key_parts.extend(str(arg) for arg in args)
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))

        key_string = ":".join(key_parts)

        # Hash if too long
        if len(key_string) > 200:
            key_hash = hashlib.sha256(key_string.encode()).hexdigest()[:16]
            return f"{prefix}:{key_hash}"

        return key_string

def cached(ttl_seconds: int = 3600, prefix: str = "cache"):
    """
    Decorator for caching function results.

    Usage:
        @cached(ttl_seconds=3600, prefix="agent_output")
        async def expensive_agent_call(state):
            # ... expensive operation
            return result
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            cache = get_cache_manager()

            # Generate cache key
            cache_key = cache.cache_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_value = await cache.get(cache_key)
            if cached_value is not None:
                logger.info(f"Cache hit: {cache_key}")
                return cached_value

            # Cache miss: execute function
            logger.info(f"Cache miss: {cache_key}")
            result = await func(*args, **kwargs)

            # Store in cache
            await cache.set(cache_key, result, ttl_seconds)

            return result

        return wrapper
    return decorator

# Global cache manager
_cache_manager = None

def get_cache_manager() -> CacheManager:
    """Get singleton cache manager."""
    global _cache_manager
    if _cache_manager is None:
        redis_url = os.getenv("REDIS_URL", "redis://localhost:6379")
        _cache_manager = CacheManager(redis_url)
    return _cache_manager
```

**Apply Caching to Agents:**
```python
# libs/llm_planner_agent.py (ENHANCEMENTS)
from libs.cache import cached

class LLMPlannerAgent(BaseLLMAgent):

    @cached(ttl_seconds=3600, prefix="planner_output")
    async def execute(self, state: MLOpsWorkflowState, trigger: TriggerType):
        """
        Execute planning with caching.

        Cache Strategy:
        - Cache key: hash of constraints
        - TTL: 1 hour
        - Invalidation: Manual (admin endpoint)
        """
        # Implementation remains the same
        # Caching happens automatically via decorator
        pass
```

**Cache Warming on Startup:**
```python
# api/main.py (ADD STARTUP TASK)

@app.on_event("startup")
async def warm_cache():
    """Warm cache with frequently accessed data."""
    cache = get_cache_manager()

    # Pre-cache templates
    from data.mlops_templates import MLOPS_TEMPLATES
    await cache.set("templates:all", MLOPS_TEMPLATES, ttl_seconds=604800)  # 7 days

    # Pre-cache capability patterns
    # await cache.set("patterns:all", CAPABILITY_PATTERNS, ttl_seconds=86400)

    logger.info("Cache warming complete")
```

#### 2.2.3 CDN Integration (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Not implemented
**Priority:** Medium
**Implementation Plan:**

```terraform
# infra/terraform/cloudfront.tf (NEW FILE TO CREATE)
resource "aws_cloudfront_distribution" "frontend" {
  enabled             = true
  is_ipv6_enabled     = true
  comment             = "Agentic MLOps Frontend CDN"
  default_root_object = "index.html"
  price_class         = "PriceClass_100"  # US, Canada, Europe

  origin {
    domain_name = aws_apprunner_service.frontend.service_url
    origin_id   = "apprunner-frontend"

    custom_origin_config {
      http_port              = 80
      https_port             = 443
      origin_protocol_policy = "https-only"
      origin_ssl_protocols   = ["TLSv1.2"]
    }
  }

  default_cache_behavior {
    allowed_methods  = ["GET", "HEAD", "OPTIONS"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "apprunner-frontend"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 3600  # 1 hour
    max_ttl                = 86400  # 24 hours
    compress               = true
  }

  # Cache static assets aggressively
  ordered_cache_behavior {
    path_pattern     = "/_next/static/*"
    allowed_methods  = ["GET", "HEAD"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "apprunner-frontend"

    forwarded_values {
      query_string = false
      cookies {
        forward = "none"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 31536000  # 1 year
    default_ttl            = 31536000
    max_ttl                = 31536000
    compress               = true
  }

  # Don't cache API requests
  ordered_cache_behavior {
    path_pattern     = "/api/*"
    allowed_methods  = ["DELETE", "GET", "HEAD", "OPTIONS", "PATCH", "POST", "PUT"]
    cached_methods   = ["GET", "HEAD"]
    target_origin_id = "apprunner-frontend"

    forwarded_values {
      query_string = true
      headers      = ["Authorization", "Content-Type"]
      cookies {
        forward = "all"
      }
    }

    viewer_protocol_policy = "redirect-to-https"
    min_ttl                = 0
    default_ttl            = 0
    max_ttl                = 0
  }

  restrictions {
    geo_restriction {
      restriction_type = "none"
    }
  }

  viewer_certificate {
    cloudfront_default_certificate = true
    # For custom domain:
    # acm_certificate_arn      = aws_acm_certificate.frontend.arn
    # ssl_support_method       = "sni-only"
    # minimum_protocol_version = "TLSv1.2_2021"
  }

  tags = {
    Name        = "Agentic MLOps Frontend CDN"
    Environment = var.environment
  }
}

output "cloudfront_domain_name" {
  value = aws_cloudfront_distribution.frontend.domain_name
}
```

---

## 3. Testing Strategy

### 3.1 Testing Pyramid

```
                    ┌─────────────┐
                    │   E2E Tests │  5%
                    │  Playwright │
                    └─────────────┘
                  ┌───────────────────┐
                  │ Integration Tests │  15%
                  │  API, Agents, DB  │
                  └───────────────────┘
              ┌─────────────────────────────┐
              │        Unit Tests           │  80%
              │  Models, Utils, Components  │
              └─────────────────────────────┘
```

### 3.2 Unit Testing

#### 3.2.1 Backend Unit Tests

```python
# tests/test_models.py
import pytest
from datetime import datetime, timezone
from libs.models import Project, DecisionSet, Job, JobStatus

def test_project_creation():
    """Test project model creation."""
    project = Project(
        id="proj_123",
        name="Test Project",
        description="Test description",
        created_at=datetime.now(timezone.utc),
        updated_at=datetime.now(timezone.utc)
    )

    assert project.id == "proj_123"
    assert project.name == "Test Project"
    assert isinstance(project.created_at, datetime)

def test_decision_set_relationships():
    """Test decision set relationships."""
    project = Project(id="proj_123", name="Test")
    decision_set = DecisionSet(
        id="ds_456",
        project_id=project.id,
        thread_id="thread_789",
        user_prompt="Design an MLOps system",
        status="active"
    )

    assert decision_set.project_id == project.id
    assert decision_set.thread_id == "thread_789"

# tests/test_job_service.py
import pytest
from libs.job_service import JobService
from libs.models import Job, JobStatus, DecisionSet

@pytest.fixture
def job_service(db_session):
    """Fixture for job service."""
    return JobService(db_session)

def test_create_job(job_service, db_session):
    """Test job creation."""
    # Create decision set first
    decision_set = DecisionSet(
        id="ds_123",
        project_id="proj_123",
        thread_id="thread_123",
        user_prompt="Test",
        status="active"
    )
    db_session.add(decision_set)
    db_session.commit()

    # Create job
    job = job_service.create_job(
        decision_set_id="ds_123",
        job_type="ml_workflow",
        payload={"test": "data"},
        priority=1
    )

    assert job.status == JobStatus.QUEUED
    assert job.priority == 1
    assert job.payload == {"test": "data"}

def test_claim_job(job_service, db_session):
    """Test job claiming with FOR UPDATE SKIP LOCKED."""
    # Create and save jobs
    decision_set = DecisionSet(
        id="ds_123",
        project_id="proj_123",
        thread_id="thread_123",
        user_prompt="Test",
        status="active"
    )
    db_session.add(decision_set)

    job1 = Job(
        id="job_1",
        decision_set_id="ds_123",
        job_type="ml_workflow",
        status=JobStatus.QUEUED,
        payload={}
    )
    db_session.add(job1)
    db_session.commit()

    # Claim job
    claimed_job = job_service.claim_job("worker_1", lease_duration=5)

    assert claimed_job is not None
    assert claimed_job.id == "job_1"
    assert claimed_job.status == JobStatus.RUNNING
    assert claimed_job.worker_id == "worker_1"
    assert claimed_job.lease_expires_at is not None

def test_claim_job_skip_locked(job_service, db_session):
    """Test that claimed jobs are skipped."""
    # Create jobs
    decision_set = DecisionSet(
        id="ds_123",
        project_id="proj_123",
        thread_id="thread_123",
        user_prompt="Test",
        status="active"
    )
    db_session.add(decision_set)

    job1 = Job(
        id="job_1",
        decision_set_id="ds_123",
        job_type="ml_workflow",
        status=JobStatus.RUNNING,  # Already claimed
        worker_id="worker_1",
        payload={}
    )
    job2 = Job(
        id="job_2",
        decision_set_id="ds_123",
        job_type="ml_workflow",
        status=JobStatus.QUEUED,  # Available
        payload={}
    )
    db_session.add_all([job1, job2])
    db_session.commit()

    # Second worker should get job_2, not job_1
    claimed_job = job_service.claim_job("worker_2", lease_duration=5)

    assert claimed_job is not None
    assert claimed_job.id == "job_2"
    assert claimed_job.worker_id == "worker_2"
```

#### 3.2.2 Frontend Unit Tests

```typescript
// frontend/components/streaming/__tests__/reason-card.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ReasonCard } from '../reason-card';

describe('ReasonCard', () => {
  const mockReasonCard = {
    agent: 'planner',
    node: 'planner',
    reasoning: 'Selected architecture based on scalability requirements',
    decision: 'Use microservices pattern',
    confidence: 0.85,
    inputs: { constraints: { scalability: 'high' } },
    outputs: { pattern: 'microservices' },
    timestamp: '2025-01-15T10:30:00Z',
  };

  it('renders reason card with basic info', () => {
    render(<ReasonCard {...mockReasonCard} />);

    expect(screen.getByText('planner')).toBeInTheDocument();
    expect(screen.getByText(/Selected architecture/)).toBeInTheDocument();
    expect(screen.getByText('85% confident')).toBeInTheDocument();
  });

  it('expands to show details on click', () => {
    render(<ReasonCard {...mockReasonCard} />);

    // Initially collapsed
    expect(screen.queryByText('Inputs')).not.toBeInTheDocument();

    // Click to expand
    const expandButton = screen.getByText('Show more');
    fireEvent.click(expandButton);

    // Now expanded
    expect(screen.getByText('Inputs')).toBeInTheDocument();
    expect(screen.getByText('Outputs')).toBeInTheDocument();
  });

  it('shows correct confidence badge variant', () => {
    const { rerender } = render(<ReasonCard {...mockReasonCard} confidence={0.9} />);
    let badge = screen.getByText('90% confident');
    expect(badge).toHaveClass('badge-success');  // High confidence

    rerender(<ReasonCard {...mockReasonCard} confidence={0.6} />);
    badge = screen.getByText('60% confident');
    expect(badge).toHaveClass('badge-warning');  // Lower confidence
  });
});

// frontend/hooks/__tests__/useStreamingEvents.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { useStreamingEvents } from '../useStreamingEvents';

// Mock EventSource
class MockEventSource {
  addEventListener = jest.fn();
  close = jest.fn();
  onopen = null;
  onerror = null;
}

global.EventSource = MockEventSource as any;

describe('useStreamingEvents', () => {
  it('establishes SSE connection', async () => {
    const { result } = renderHook(() =>
      useStreamingEvents({ decisionSetId: 'ds_123', autoConnect: true })
    );

    await waitFor(() => {
      expect(EventSource).toHaveBeenCalledWith(
        expect.stringContaining('/api/streams/ds_123')
      );
    });
  });

  it('handles reason card events', async () => {
    const { result } = renderHook(() =>
      useStreamingEvents({ decisionSetId: 'ds_123', autoConnect: true })
    );

    // Simulate reason card event
    const mockEvent = {
      data: JSON.stringify({
        type: 'reason-card',
        decision_set_id: 'ds_123',
        timestamp: '2025-01-15T10:30:00Z',
        data: { agent: 'planner', reasoning: 'Test' }
      })
    };

    // Trigger event handler
    const eventSource = EventSource.mock.instances[0];
    const reasonCardHandler = eventSource.addEventListener.mock.calls.find(
      (call) => call[0] === 'reason-card'
    )[1];
    reasonCardHandler(mockEvent);

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1);
      expect(result.current.events[0].type).toBe('reason-card');
    });
  });

  it('deduplicates events', async () => {
    const { result } = renderHook(() =>
      useStreamingEvents({ decisionSetId: 'ds_123', autoConnect: true })
    );

    const mockEvent = {
      data: JSON.stringify({
        type: 'reason-card',
        decision_set_id: 'ds_123',
        timestamp: '2025-01-15T10:30:00Z',
        data: { agent: 'planner' }
      })
    };

    // Send same event twice
    const eventSource = EventSource.mock.instances[0];
    const handler = eventSource.addEventListener.mock.calls[0][1];
    handler(mockEvent);
    handler(mockEvent);  // Duplicate

    await waitFor(() => {
      expect(result.current.events).toHaveLength(1);  // Only one event
    });
  });
});
```

### 3.3 Integration Testing

```python
# tests/test_llm_workflow_integration.py
import pytest
from libs.graph import build_full_graph
from libs.models import DecisionSet
from langchain_core.messages import HumanMessage

@pytest.mark.integration
@pytest.mark.slow
async def test_full_workflow_execution(db_session):
    """
    Test complete workflow from intake to code generation.

    This is a long-running test that exercises the entire system.
    """
    # Build graph
    graph = build_full_graph()

    # Create decision set
    decision_set = DecisionSet(
        id="ds_test_123",
        project_id="proj_test_123",
        thread_id="thread_test_123",
        user_prompt="Design an MLOps system for real-time fraud detection with budget of $5000/month",
        status="active"
    )
    db_session.add(decision_set)
    db_session.commit()

    # Initial state
    state = {
        "messages": [HumanMessage(content=decision_set.user_prompt)],
        "decision_set_id": decision_set.id
    }

    config = {"configurable": {"thread_id": decision_set.thread_id}}

    # Execute workflow
    final_state = await graph.ainvoke(state, config)

    # Assertions
    assert "constraints" in final_state
    assert final_state["constraints"] is not None

    assert "coverage_score" in final_state
    assert final_state["coverage_score"] >= 0.7  # Should meet threshold

    assert "plan" in final_state
    assert final_state["plan"] is not None

    assert "cost_estimate" in final_state
    assert final_state["cost_estimate"]["monthly_usd"] <= 5000  # Within budget

    assert "execution_order" in final_state
    expected_nodes = ["intake_extract", "coverage_check", "planner", "critic_tech", "critic_cost"]
    assert all(node in final_state["execution_order"] for node in expected_nodes)
```

### 3.4 End-to-End Testing

```typescript
// frontend/e2e/complete-workflow.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Complete MLOps Design Workflow', () => {
  test('user can design MLOps system end-to-end', async ({ page }) => {
    // 1. Navigate to landing page
    await page.goto('/');
    await expect(page.locator('h1')).toContainText('Agentic MLOps');

    // 2. Select a template
    const templateCard = page.locator('[data-testid="template-card-realtime"]');
    await templateCard.click();
    await expect(templateCard).toHaveClass(/selected/);

    // 3. Click "Run Live"
    await page.locator('[data-testid="run-live-button"]').click();

    // 4. Verify chat interface is visible
    await expect(page.locator('[data-testid="chat-interface"]')).toBeVisible();

    // 5. Verify template prompt is pre-filled
    const chatInput = page.locator('[data-testid="chat-input"]');
    await expect(chatInput).toHaveValue(/real-time fraud detection/i);

    // 6. Send message
    await page.locator('[data-testid="send-button"]').click();

    // 7. Verify job creation
    await expect(page.locator('[data-testid="job-status"]')).toBeVisible();
    await expect(page.locator('[data-testid="job-status"]')).toContainText('Processing');

    // 8. Verify SSE connection established
    await expect(page.locator('[data-testid="connection-status"]')).toContainText('Connected');

    // 9. Wait for first reason card
    await page.waitForSelector('[data-testid="reason-card"]', { timeout: 30000 });
    const firstReasonCard = page.locator('[data-testid="reason-card"]').first();
    await expect(firstReasonCard).toBeVisible();
    await expect(firstReasonCard).toContainText(/intake/i);

    // 10. Verify workflow progress
    const progressBar = page.locator('[data-testid="workflow-progress"]');
    await expect(progressBar).toBeVisible();
    await expect(progressBar).toContainText(/0%|[1-9]/);  // Progress > 0%

    // 11. Verify multiple reason cards appear
    await page.waitForSelector('[data-testid="reason-card"]:nth-child(2)', { timeout: 60000 });
    const reasonCards = page.locator('[data-testid="reason-card"]');
    await expect(reasonCards).toHaveCount(2, { timeout: 90000 });

    // 12. Expand reason card to see details
    await firstReasonCard.click();
    await expect(firstReasonCard.locator('[data-testid="reason-card-inputs"]')).toBeVisible();
    await expect(firstReasonCard.locator('[data-testid="reason-card-outputs"]')).toBeVisible();

    // 13. Verify workflow completion (this may take several minutes)
    await page.waitForSelector('[data-testid="workflow-complete"]', { timeout: 300000 });
    await expect(page.locator('[data-testid="job-status"]')).toContainText('Completed');

    // 14. Verify final message with results
    const finalMessage = page.locator('[data-testid="message"]').last();
    await expect(finalMessage).toContainText(/design complete|architecture/i);

    // 15. Verify download artifacts button
    await expect(page.locator('[data-testid="download-artifacts"]')).toBeVisible();
  });

  test('HITL workflow with questions', async ({ page }) => {
    await page.goto('/');

    // Send vague prompt that will trigger questions
    await page.locator('[data-testid="chat-input"]').fill('I need an MLOps system');
    await page.locator('[data-testid="send-button"]').click();

    // Wait for questions to be presented
    await page.waitForSelector('[data-testid="hitl-questions"]', { timeout: 60000 });

    const questionsForm = page.locator('[data-testid="hitl-questions"]');
    await expect(questionsForm).toBeVisible();

    // Verify multiple questions
    const questions = questionsForm.locator('[data-testid="question"]');
    await expect(questions).toHaveCount(3, { timeout: 5000 });

    // Answer questions
    await page.locator('[data-testid="question-0-input"]').fill('Real-time predictions');
    await page.locator('[data-testid="question-1-input"]').fill('$3000');
    await page.locator('[data-testid="question-2-input"]').fill('AWS');

    // Submit answers
    await page.locator('[data-testid="submit-answers"]').click();

    // Verify workflow continues
    await expect(page.locator('[data-testid="workflow-resumed"]')).toBeVisible({ timeout: 10000 });
    await expect(page.locator('[data-testid="job-status"]')).toContainText('Processing');
  });

  test('error handling and recovery', async ({ page }) => {
    // Simulate network error
    await page.route('**/api/chat/async', route => route.abort());

    await page.goto('/');
    await page.locator('[data-testid="chat-input"]').fill('Test message');
    await page.locator('[data-testid="send-button"]').click();

    // Verify error message
    await expect(page.locator('[data-testid="error-message"]')).toBeVisible();
    await expect(page.locator('[data-testid="error-message"]')).toContainText(/network error|failed to send/i);

    // Clear route and retry
    await page.unroute('**/api/chat/async');
    await page.locator('[data-testid="retry-button"]').click();

    // Verify success
    await expect(page.locator('[data-testid="job-status"]')).toBeVisible();
  });
});
```

---

## 4. Error Handling Strategy

### 4.1 Error Classification

```python
# libs/errors.py (NEW FILE TO CREATE)
from enum import Enum
from typing import Optional
from fastapi import HTTPException

class ErrorCategory(Enum):
    """Error categories for classification and handling."""
    USER_ERROR = "user_error"  # Invalid input, auth failure
    SYSTEM_ERROR = "system_error"  # Database, network, infrastructure
    EXTERNAL_ERROR = "external_error"  # LLM API, S3, external services
    BUSINESS_ERROR = "business_error"  # Policy violations, budget exceeded

class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"  # Retry will likely succeed
    MEDIUM = "medium"  # May require intervention
    HIGH = "high"  # Critical, requires immediate attention
    CRITICAL = "critical"  # System failure, page ops

class AgenticMLOpsError(Exception):
    """Base exception for all application errors."""

    def __init__(
        self,
        message: str,
        category: ErrorCategory,
        severity: ErrorSeverity,
        retry_able: bool = False,
        details: Optional[dict] = None
    ):
        super().__init__(message)
        self.message = message
        self.category = category
        self.severity = severity
        self.retryable = retry_able
        self.details = details or {}

class UserInputError(AgenticMLOpsError):
    """Invalid user input."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.USER_ERROR,
            severity=ErrorSeverity.LOW,
            retryable=False,
            details=details
        )

class LLMError(AgenticMLOpsError):
    """LLM API error."""
    def __init__(self, message: str, retryable: bool = True, details: Optional[dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_ERROR,
            severity=ErrorSeverity.MEDIUM,
            retryable=retryable,
            details=details
        )

class DatabaseError(AgenticMLOpsError):
    """Database operation error."""
    def __init__(self, message: str, details: Optional[dict] = None):
        super().__init__(
            message=message,
            category=ErrorCategory.SYSTEM_ERROR,
            severity=ErrorSeverity.HIGH,
            retryable=True,
            details=details
        )

class PolicyViolationError(AgenticMLOpsError):
    """Business policy violation."""
    def __init__(self, message: str, violations: list[str]):
        super().__init__(
            message=message,
            category=ErrorCategory.BUSINESS_ERROR,
            severity=ErrorSeverity.MEDIUM,
            retryable=False,
            details={"violations": violations}
        )
```

### 4.2 Error Handling Patterns

#### 4.2.1 Retry with Exponential Backoff

```python
# libs/retry.py (ENHANCED VERSION)
import asyncio
import logging
from typing import TypeVar, Callable, Optional
from functools import wraps
import backoff

logger = logging.getLogger(__name__)

T = TypeVar('T')

def retry_with_backoff(
    max_tries: int = 3,
    base_delay: float = 1.0,
    max_delay: float = 60.0,
    exceptions: tuple = (Exception,),
    on_failure: Optional[Callable] = None
):
    """
    Retry decorator with exponential backoff.

    Args:
        max_tries: Maximum number of attempts
        base_delay: Initial delay in seconds
        max_delay: Maximum delay between retries
        exceptions: Tuple of exceptions to catch
        on_failure: Callback function on final failure

    Usage:
        @retry_with_backoff(max_tries=3, exceptions=(openai.APIError,))
        async def call_openai():
            return await client.chat.completions.create(...)
    """
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            @backoff.on_exception(
                backoff.expo,
                exceptions,
                max_tries=max_tries,
                max_value=max_delay,
                on_backoff=lambda details: logger.warning(
                    f"Retrying {func.__name__} after {details['wait']:.2f}s "
                    f"(attempt {details['tries']}/{max_tries})"
                )
            )
            async def with_backoff():
                try:
                    return await func(*args, **kwargs)
                except exceptions as e:
                    if on_failure:
                        on_failure(e)
                    raise

            return await with_backoff()

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            @backoff.on_exception(
                backoff.expo,
                exceptions,
                max_tries=max_tries,
                max_value=max_delay
            )
            def with_backoff():
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if on_failure:
                        on_failure(e)
                    raise

            return with_backoff()

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper

    return decorator
```

**Apply to LLM Calls:**
```python
# libs/llm_client.py (ENHANCEMENTS)
from libs.retry import retry_with_backoff
from openai import APIError, RateLimitError, APITimeoutError

class LLMClient:
    """Enhanced LLM client with error handling."""

    @retry_with_backoff(
        max_tries=3,
        exceptions=(RateLimitError, APITimeoutError),
        on_failure=lambda e: logger.error(f"LLM call failed after retries: {e}")
    )
    async def create_completion(self, messages: list, model: str = "gpt-4"):
        """Create completion with automatic retry."""
        try:
            return await self.client.chat.completions.create(
                model=model,
                messages=messages,
                timeout=30.0
            )
        except APIError as e:
            # Wrap in custom error
            raise LLMError(
                message=f"OpenAI API error: {str(e)}",
                retryable=e.status_code in [429, 500, 502, 503, 504],
                details={"status_code": e.status_code}
            )
```

#### 4.2.2 Circuit Breaker Pattern (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Not implemented
**Priority:** Medium
**Implementation Plan:**

```python
# libs/circuit_breaker.py (NEW FILE TO CREATE)
from enum import Enum
from datetime import datetime, timedelta
from typing import Callable, Optional
import asyncio

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"  # Normal operation
    OPEN = "open"  # Failing, reject requests
    HALF_OPEN = "half_open"  # Testing if service recovered

class CircuitBreaker:
    """
    Circuit breaker for external service calls.

    Pattern:
    - CLOSED: Normal operation, track failures
    - OPEN: Too many failures, reject requests immediately
    - HALF_OPEN: After timeout, allow test request

    Configuration:
    - failure_threshold: 5 failures trigger OPEN
    - recovery_timeout: 60s before trying HALF_OPEN
    - success_threshold: 2 successes to close circuit
    """

    def __init__(
        self,
        failure_threshold: int = 5,
        recovery_timeout: int = 60,
        success_threshold: int = 2
    ):
        self.failure_threshold = failure_threshold
        self.recovery_timeout = recovery_timeout
        self.success_threshold = success_threshold

        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self._lock = asyncio.Lock()

    async def call(self, func: Callable, *args, **kwargs):
        """
        Execute function with circuit breaker protection.

        Raises:
            CircuitOpenError: If circuit is open
        """
        async with self._lock:
            # Check if we should transition to HALF_OPEN
            if self.state == CircuitState.OPEN:
                if self._should_attempt_reset():
                    logger.info("Circuit breaker transitioning to HALF_OPEN")
                    self.state = CircuitState.HALF_OPEN
                    self.success_count = 0
                else:
                    raise CircuitOpenError(
                        f"Circuit breaker is OPEN. Try again in "
                        f"{self._time_until_retry()}s"
                    )

        try:
            # Execute function
            result = await func(*args, **kwargs)

            # Record success
            async with self._lock:
                await self._on_success()

            return result

        except Exception as e:
            # Record failure
            async with self._lock:
                await self._on_failure()
            raise

    async def _on_success(self):
        """Handle successful call."""
        self.failure_count = 0

        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            if self.success_count >= self.success_threshold:
                logger.info("Circuit breaker transitioning to CLOSED")
                self.state = CircuitState.CLOSED
                self.success_count = 0

    async def _on_failure(self):
        """Handle failed call."""
        self.failure_count += 1
        self.last_failure_time = datetime.now()

        if self.state == CircuitState.HALF_OPEN:
            # Failed during test, go back to OPEN
            logger.warning("Circuit breaker test failed, returning to OPEN")
            self.state = CircuitState.OPEN
            self.success_count = 0

        elif self.failure_count >= self.failure_threshold:
            logger.error(
                f"Circuit breaker threshold exceeded "
                f"({self.failure_count} failures), transitioning to OPEN"
            )
            self.state = CircuitState.OPEN

    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to try HALF_OPEN."""
        if not self.last_failure_time:
            return True

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        return elapsed >= self.recovery_timeout

    def _time_until_retry(self) -> int:
        """Calculate seconds until retry is allowed."""
        if not self.last_failure_time:
            return 0

        elapsed = (datetime.now() - self.last_failure_time).total_seconds()
        remaining = max(0, self.recovery_timeout - elapsed)
        return int(remaining)

class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass

# Global circuit breakers for external services
_circuit_breakers = {}

def get_circuit_breaker(service_name: str) -> CircuitBreaker:
    """Get or create circuit breaker for service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = CircuitBreaker()
    return _circuit_breakers[service_name]
```

**Apply Circuit Breaker:**
```python
# libs/llm_client.py (ENHANCEMENTS)
from libs.circuit_breaker import get_circuit_breaker, CircuitOpenError

class LLMClient:
    def __init__(self):
        self.circuit_breaker = get_circuit_breaker("openai")

    async def create_completion(self, messages: list, model: str = "gpt-4"):
        """Create completion with circuit breaker protection."""
        try:
            return await self.circuit_breaker.call(
                self._create_completion_internal,
                messages,
                model
            )
        except CircuitOpenError as e:
            # Circuit is open, return cached response or error
            logger.error(f"OpenAI circuit breaker is open: {e}")
            raise LLMError(
                message="OpenAI service temporarily unavailable",
                retryable=True,
                details={"circuit_breaker": "open"}
            )

    async def _create_completion_internal(self, messages: list, model: str):
        """Internal completion call (wrapped by circuit breaker)."""
        return await self.client.chat.completions.create(
            model=model,
            messages=messages
        )
```

#### 4.2.3 Graceful Degradation

```python
# libs/fallback.py (NEW FILE TO CREATE)
from typing import Optional, Callable, Any
import logging

logger = logging.getLogger(__name__)

class FallbackStrategy:
    """
    Graceful degradation with fallback strategies.

    Strategies:
    1. Cached response: Return last successful response
    2. Default response: Return sensible default
    3. Simplified version: Use simpler/cheaper LLM
    4. Mock response: Return mock data for testing
    """

    @staticmethod
    async def with_cache_fallback(
        primary_func: Callable,
        cache_key: str,
        *args,
        **kwargs
    ) -> Any:
        """Try primary function, fall back to cache on failure."""
        from libs.cache import get_cache_manager
        cache = get_cache_manager()

        try:
            # Try primary function
            result = await primary_func(*args, **kwargs)

            # Cache successful result
            await cache.set(cache_key, result, ttl_seconds=3600)

            return result

        except Exception as e:
            logger.warning(f"Primary function failed, trying cache: {e}")

            # Try cache
            cached_result = await cache.get(cache_key)
            if cached_result:
                logger.info(f"Returning cached result for {cache_key}")
                return cached_result

            # No cache available
            raise

    @staticmethod
    async def with_model_fallback(
        messages: list,
        primary_model: str = "gpt-4",
        fallback_model: str = "gpt-3.5-turbo"
    ):
        """Try primary model, fall back to cheaper model."""
        from libs.llm_client import LLMClient
        client = LLMClient()

        try:
            # Try primary model
            return await client.create_completion(messages, primary_model)

        except Exception as e:
            logger.warning(
                f"Primary model {primary_model} failed, "
                f"falling back to {fallback_model}: {e}"
            )

            # Try fallback model
            return await client.create_completion(messages, fallback_model)
```

**Apply Graceful Degradation:**
```python
# libs/llm_planner_agent.py (ENHANCEMENTS)
from libs.fallback import FallbackStrategy

class LLMPlannerAgent(BaseLLMAgent):
    async def execute(self, state: MLOpsWorkflowState, trigger: TriggerType):
        """Execute with graceful degradation."""

        # Try with cache fallback
        cache_key = f"planner:{hash(str(state.get('constraints')))}"

        try:
            return await FallbackStrategy.with_cache_fallback(
                self._execute_internal,
                cache_key,
                state,
                trigger
            )
        except Exception as e:
            logger.error(f"Planner agent failed with all fallbacks: {e}")

            # Return partial result with error
            return AgentResult(
                success=False,
                state_updates={"plan": None},
                reason_card=self._create_error_reason_card(str(e)),
                error_message=str(e)
            )
```

### 4.3 Error Logging and Alerting

```python
# libs/error_tracking.py (NEW FILE TO CREATE)
import logging
from typing import Optional
from datetime import datetime

logger = logging.getLogger(__name__)

class ErrorTracker:
    """
    Centralized error tracking and alerting.

    Features:
    - Structured error logging
    - Error rate tracking
    - Alert triggering
    - Error aggregation
    """

    def __init__(self):
        self.error_counts = {}  # Track error frequencies

    async def track_error(
        self,
        error: Exception,
        context: dict,
        user_id: Optional[str] = None,
        decision_set_id: Optional[str] = None
    ):
        """
        Track error with context.

        Args:
            error: Exception that occurred
            context: Additional context (request data, state, etc.)
            user_id: User who encountered error
            decision_set_id: Decision set being processed
        """
        error_type = type(error).__name__
        error_message = str(error)

        # Increment error counter
        if error_type not in self.error_counts:
            self.error_counts[error_type] = 0
        self.error_counts[error_type] += 1

        # Structured logging
        logger.error(
            f"Error tracked: {error_type}",
            extra={
                "error_type": error_type,
                "error_message": error_message,
                "user_id": user_id,
                "decision_set_id": decision_set_id,
                "context": context,
                "timestamp": datetime.now().isoformat(),
                "error_count": self.error_counts[error_type]
            },
            exc_info=True
        )

        # Check if we should alert
        if self.error_counts[error_type] > 10:  # Threshold
            await self._send_alert(error_type, self.error_counts[error_type])

    async def _send_alert(self, error_type: str, count: int):
        """Send alert for high error rate."""
        # In production, integrate with:
        # - PagerDuty
        # - Slack
        # - Email
        # - CloudWatch Alarms

        logger.critical(
            f"HIGH ERROR RATE ALERT: {error_type} occurred {count} times",
            extra={
                "alert": True,
                "error_type": error_type,
                "count": count
            }
        )

# Global error tracker
_error_tracker = None

def get_error_tracker() -> ErrorTracker:
    """Get singleton error tracker."""
    global _error_tracker
    if _error_tracker is None:
        _error_tracker = ErrorTracker()
    return _error_tracker
```

---

## 5. Monitoring & Observability

### 5.1 Logging Strategy

#### 5.1.1 Structured Logging (Current Implementation)

```python
# api/main.py (CURRENT)
import logging
import json

# JSON logging for CloudWatch in production
if os.getenv("ENVIRONMENT") == "production":
    LOGGING_CONFIG = {
        "version": 1,
        "formatters": {
            "json": {
                "format": "%(asctime)s %(name)s %(levelname)s %(message)s",
                "class": "pythonjsonlogger.jsonlogger.JsonFormatter",
            }
        },
        "handlers": {
            "console": {
                "class": "logging.StreamHandler",
                "formatter": "json",
            }
        },
        "root": {
            "level": os.getenv("LOG_LEVEL", "INFO"),
            "handlers": ["console"]
        }
    }
    logging.config.dictConfig(LOGGING_CONFIG)

# Log with structured data
logger.info(
    "Job claimed",
    extra={
        "job_id": job.id,
        "worker_id": worker_id,
        "decision_set_id": decision_set.id,
        "thread_id": thread_id
    }
)
```

#### 5.1.2 Enhanced Logging with Correlation IDs

```python
# libs/logging_utils.py (NEW FILE TO CREATE)
import logging
import contextvars
from typing import Optional

# Context variable for correlation ID
correlation_id_var = contextvars.ContextVar('correlation_id', default=None)

class CorrelationIdFilter(logging.Filter):
    """Add correlation ID to all log records."""

    def filter(self, record):
        record.correlation_id = correlation_id_var.get() or "unknown"
        return True

def setup_logging():
    """Setup enhanced logging with correlation IDs."""
    # Add filter to root logger
    correlation_filter = CorrelationIdFilter()
    logging.getLogger().addFilter(correlation_filter)

    # Update format to include correlation ID
    for handler in logging.getLogger().handlers:
        if hasattr(handler, 'formatter'):
            handler.formatter._fmt += " [%(correlation_id)s]"

def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context."""
    correlation_id_var.set(correlation_id)

def get_correlation_id() -> Optional[str]:
    """Get correlation ID for current context."""
    return correlation_id_var.get()
```

**Apply Correlation IDs:**
```python
# api/main.py (ENHANCEMENTS)
from libs.logging_utils import set_correlation_id
import uuid

@app.middleware("http")
async def correlation_id_middleware(request: Request, call_next):
    """Add correlation ID to all requests."""
    # Generate or extract correlation ID
    correlation_id = request.headers.get("X-Correlation-ID") or str(uuid.uuid4())

    # Set in context
    set_correlation_id(correlation_id)

    # Add to response headers
    response = await call_next(request)
    response.headers["X-Correlation-ID"] = correlation_id

    return response
```

### 5.2 Metrics Collection (RECOMMENDED IMPLEMENTATION)

**Current State:** ❌ Minimal CloudWatch metrics
**Priority:** High
**Implementation Plan:**

```python
# libs/metrics.py (NEW FILE TO CREATE)
from dataclasses import dataclass
from datetime import datetime
from typing import Dict, List, Optional
import asyncio

@dataclass
class Metric:
    """Metric data point."""
    name: str
    value: float
    unit: str
    timestamp: datetime
    dimensions: Dict[str, str]

class MetricsCollector:
    """
    Collect and publish custom metrics.

    Metrics to track:
    - Request latency
    - Job processing time
    - Agent execution time
    - LLM API latency
    - Error rates
    - SSE connection count
    """

    def __init__(self):
        self.metrics: List[Metric] = []
        self._lock = asyncio.Lock()

    async def record_counter(
        self,
        name: str,
        value: float = 1.0,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record counter metric."""
        metric = Metric(
            name=name,
            value=value,
            unit="Count",
            timestamp=datetime.now(),
            dimensions=dimensions or {}
        )

        async with self._lock:
            self.metrics.append(metric)

    async def record_gauge(
        self,
        name: str,
        value: float,
        unit: str = "None",
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record gauge metric."""
        metric = Metric(
            name=name,
            value=value,
            unit=unit,
            timestamp=datetime.now(),
            dimensions=dimensions or {}
        )

        async with self._lock:
            self.metrics.append(metric)

    async def record_timer(
        self,
        name: str,
        duration_ms: float,
        dimensions: Optional[Dict[str, str]] = None
    ):
        """Record timing metric."""
        await self.record_gauge(
            name=name,
            value=duration_ms,
            unit="Milliseconds",
            dimensions=dimensions
        )

    async def publish_to_cloudwatch(self):
        """Publish metrics to CloudWatch."""
        if not self.metrics:
            return

        import boto3
        cloudwatch = boto3.client('cloudwatch')

        async with self._lock:
            # Prepare metric data for CloudWatch
            metric_data = [
                {
                    'MetricName': m.name,
                    'Value': m.value,
                    'Unit': m.unit,
                    'Timestamp': m.timestamp,
                    'Dimensions': [
                        {'Name': k, 'Value': v}
                        for k, v in m.dimensions.items()
                    ]
                }
                for m in self.metrics
            ]

            # Publish in batches (CloudWatch limit: 20 metrics per call)
            for i in range(0, len(metric_data), 20):
                batch = metric_data[i:i+20]
                cloudwatch.put_metric_data(
                    Namespace='AgenticMLOps',
                    MetricData=batch
                )

            # Clear published metrics
            self.metrics.clear()

# Global metrics collector
_metrics_collector = None

def get_metrics_collector() -> MetricsCollector:
    """Get singleton metrics collector."""
    global _metrics_collector
    if _metrics_collector is None:
        _metrics_collector = MetricsCollector()
    return _metrics_collector

# Decorator for timing functions
def timed(metric_name: str, dimensions: Optional[Dict[str, str]] = None):
    """Decorator to time function execution."""
    def decorator(func):
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = await func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics = get_metrics_collector()
                await metrics.record_timer(metric_name, duration_ms, dimensions)

        @wraps(func)
        def sync_wrapper(*args, **kwargs):
            start = time.time()
            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start) * 1000
                metrics = get_metrics_collector()
                asyncio.create_task(
                    metrics.record_timer(metric_name, duration_ms, dimensions)
                )

        return async_wrapper if asyncio.iscoroutinefunction(func) else sync_wrapper
    return decorator
```

**Apply Metrics:**
```python
# api/main.py (ENHANCEMENTS)
from libs.metrics import get_metrics_collector, timed

metrics = get_metrics_collector()

@app.post("/api/chat/async")
@timed("api.chat.async.latency")
async def chat_async(req: ChatRequest, ...):
    # Record request
    await metrics.record_counter("api.chat.requests", dimensions={"endpoint": "async"})

    try:
        # ... process request
        await metrics.record_counter("api.chat.success")
        return response
    except Exception as e:
        await metrics.record_counter("api.chat.errors", dimensions={"error_type": type(e).__name__})
        raise

# Background task to publish metrics
@app.on_event("startup")
async def start_metrics_publisher():
    async def publish_loop():
        while True:
            await asyncio.sleep(60)  # Publish every minute
            await metrics.publish_to_cloudwatch()

    asyncio.create_task(publish_loop())
```

### 5.3 CloudWatch Dashboard (RECOMMENDED IMPLEMENTATION)

```terraform
# infra/terraform/cloudwatch_dashboard.tf (NEW FILE TO CREATE)
resource "aws_cloudwatch_dashboard" "main" {
  dashboard_name = "agentic-mlops-dashboard"

  dashboard_body = jsonencode({
    widgets = [
      # API Request Rate
      {
        type = "metric"
        properties = {
          metrics = [
            ["AgenticMLOps", "api.chat.requests", { stat = "Sum", label = "Requests" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "API Request Rate"
        }
      },

      # API Error Rate
      {
        type = "metric"
        properties = {
          metrics = [
            ["AgenticMLOps", "api.chat.errors", { stat = "Sum", label = "Errors" }],
            [".", "api.chat.success", { stat = "Sum", label = "Success" }]
          ]
          period = 300
          stat   = "Sum"
          region = var.aws_region
          title  = "API Error Rate"
        }
      },

      # API Latency
      {
        type = "metric"
        properties = {
          metrics = [
            ["AgenticMLOps", "api.chat.async.latency", { stat = "Average", label = "Avg" }],
            ["...", { stat = "p99", label = "p99" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "API Latency (ms)"
        }
      },

      # Job Queue Depth
      {
        type = "metric"
        properties = {
          metrics = [
            ["AgenticMLOps", "jobs.queued", { stat = "Average" }],
            [".", "jobs.running", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Job Queue Depth"
        }
      },

      # Agent Execution Time
      {
        type = "metric"
        properties = {
          metrics = [
            ["AgenticMLOps", "agent.execution.time", { stat = "Average", label = "Avg" }],
            ["...", { stat = "p99", label = "p99" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Agent Execution Time (ms)"
        }
      },

      # SSE Connections
      {
        type = "metric"
        properties = {
          metrics = [
            ["AgenticMLOps", "sse.connections.active", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Active SSE Connections"
        }
      },

      # Database Connections
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/RDS", "DatabaseConnections", { stat = "Average" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "Database Connections"
        }
      },

      # App Runner CPU
      {
        type = "metric"
        properties = {
          metrics = [
            ["AWS/AppRunner", "CPUUtilization", { stat = "Average", label = "API" }]
          ]
          period = 300
          stat   = "Average"
          region = var.aws_region
          title  = "App Runner CPU Utilization (%)"
        }
      }
    ]
  })
}
```

### 5.4 Alerting (RECOMMENDED IMPLEMENTATION)

```terraform
# infra/terraform/cloudwatch_alarms.tf (NEW FILE TO CREATE)

# High error rate alarm
resource "aws_cloudwatch_metric_alarm" "high_error_rate" {
  alarm_name          = "agentic-mlops-high-error-rate"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "api.chat.errors"
  namespace           = "AgenticMLOps"
  period              = 300
  statistic           = "Sum"
  threshold           = 10
  alarm_description   = "Alert when error rate is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# High API latency alarm
resource "aws_cloudwatch_metric_alarm" "high_api_latency" {
  alarm_name          = "agentic-mlops-high-api-latency"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "api.chat.async.latency"
  namespace           = "AgenticMLOps"
  period              = 300
  statistic           = "Average"
  threshold           = 5000  # 5 seconds
  alarm_description   = "Alert when API latency is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# Database connection saturation
resource "aws_cloudwatch_metric_alarm" "high_db_connections" {
  alarm_name          = "agentic-mlops-high-db-connections"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 2
  metric_name         = "DatabaseConnections"
  namespace           = "AWS/RDS"
  period              = 300
  statistic           = "Average"
  threshold           = 80  # 80% of max connections
  alarm_description   = "Alert when database connections are near limit"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# Job queue backing up
resource "aws_cloudwatch_metric_alarm" "high_job_queue_depth" {
  alarm_name          = "agentic-mlops-high-job-queue-depth"
  comparison_operator = "GreaterThanThreshold"
  evaluation_periods  = 3
  metric_name         = "jobs.queued"
  namespace           = "AgenticMLOps"
  period              = 300
  statistic           = "Average"
  threshold           = 100
  alarm_description   = "Alert when job queue depth is high"
  alarm_actions       = [aws_sns_topic.alerts.arn]
}

# SNS topic for alerts
resource "aws_sns_topic" "alerts" {
  name = "agentic-mlops-alerts"
}

resource "aws_sns_topic_subscription" "alerts_email" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "email"
  endpoint  = var.alert_email
}

# Optional: Slack integration
resource "aws_sns_topic_subscription" "alerts_slack" {
  topic_arn = aws_sns_topic.alerts.arn
  protocol  = "https"
  endpoint  = var.slack_webhook_url
}
```

---

## Summary

This comprehensive Operations & Production guide provides:

1. **Deployment Architecture**: Complete AWS infrastructure with Terraform, deployment scripts, and disaster recovery strategies

2. **Security & Performance**: Implementation plans for authentication/authorization (JWT + AWS Cognito), rate limiting (token bucket + Redis), input validation, secret management (AWS Secrets Manager), query optimization, Redis caching, and CDN integration

3. **Testing Strategy**: Complete testing pyramid with unit tests (80%), integration tests (15%), and E2E tests (5%) with Playwright, including actual test code examples

4. **Error Handling**: Comprehensive error classification, retry with exponential backoff, circuit breaker pattern, graceful degradation strategies, and centralized error tracking

5. **Monitoring & Observability**: Structured logging with correlation IDs, custom metrics collection, CloudWatch dashboards, and alerting system with SNS integration

All recommendations include:
- Current implementation status (✅/❌)
- Priority level (High/Medium/Low)
- Complete implementation code
- Infrastructure as Code (Terraform)
- Integration examples

**Document Status**: Complete
**All 4 Parts Completed Successfully**

---

**Total Documentation Package:**
- Part 1: System Overview & Tech Stack (540+ lines)
- Part 2: Technical Specifications (850+ lines)
- Part 3: Architecture Deep Dive (1200+ lines)
- Part 4: Operations & Production (1800+ lines)

**Grand Total: 4,390+ lines of comprehensive technical documentation**
