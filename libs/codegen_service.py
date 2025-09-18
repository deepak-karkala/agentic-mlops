"""
Code Generation Service using Claude Code SDK.

This module implements the core code generation functionality for MLOps projects
using Claude Code SDK to generate complete infrastructure and application code.
"""

import asyncio
import logging
import os
import tempfile
import zipfile
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import boto3
from botocore.exceptions import ClientError
from claude_code_sdk import ClaudeCodeOptions, ClaudeSDKClient

logger = logging.getLogger(__name__)


class CodegenService:
    """Service for generating and managing MLOps code artifacts."""

    def __init__(self):
        self.s3_client = None
        self.s3_bucket = os.getenv("S3_BUCKET_NAME")
        self._claude_timeout = int(os.getenv("CLAUDE_CODE_TIMEOUT_SECONDS", "60"))

        if self.s3_bucket:
            try:
                self.s3_client = boto3.client("s3")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")

    async def generate_mlops_repository(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete MLOps repository based on the approved plan.

        Args:
            plan: The approved MLOps plan containing architecture details

        Returns:
            Dict containing artifact information and file paths
        """
        logger.info(
            "Starting MLOps repository generation",
            extra={
                "pattern": plan.get("pattern_name", "unknown"),
                "services": len(plan.get("key_services", {})),
            },
        )

        try:
            # Create temporary directory for generated code
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Generate code using Claude Code SDK
                artifacts = await self._generate_code_with_claude(plan, temp_path)

                # Create reports directory
                reports_dir = temp_path / "reports"
                reports_dir.mkdir(exist_ok=True)

                # Create repository ZIP
                zip_path = temp_path / "mlops_repository.zip"
                zip_key = await self._create_repository_zip(temp_path, zip_path, plan)

                # Upload to S3 if available
                s3_url = None
                if self.s3_client and self.s3_bucket:
                    s3_url = await self._upload_to_s3(zip_path, zip_key)

                return {
                    "artifacts": artifacts,
                    "repository_zip": {
                        "local_path": str(zip_path),
                        "s3_url": s3_url,
                        "zip_key": zip_key,
                        "size_bytes": zip_path.stat().st_size
                        if zip_path.exists()
                        else 0,
                    },
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "plan_used": plan.get("pattern_name", "unknown"),
                }

        except Exception as e:
            logger.exception("Failed to generate MLOps repository")
            raise CodegenError(f"Repository generation failed: {str(e)}")

    async def _generate_code_with_claude(
        self, plan: Dict[str, Any], output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Generate code files using Claude Code SDK."""
        logger.info("Generating code with Claude Code SDK")

        # Prepare system prompt for MLOps code generation
        system_prompt = self._create_system_prompt(plan)

        # Define the generation request
        generation_prompt = self._create_generation_prompt(plan)

        try:
            # Use decomposed approach - generate components separately
            artifacts = await self._generate_decomposed_components(plan, output_dir)
            logger.info(f"Generated {len(artifacts)} code artifacts using decomposed approach")
            return artifacts

        except asyncio.TimeoutError:
            logger.warning("Claude Code SDK timed out; falling back to templates")
            return await self._fallback_template_generation(plan, output_dir)
        except Exception:
            logger.exception("Claude Code SDK generation failed")
            # Fallback to template-based generation
            return await self._fallback_template_generation(plan, output_dir)

    async def _generate_decomposed_components(self, plan: Dict[str, Any], output_dir: Path) -> List[Dict[str, Any]]:
        """Generate MLOps components using multiple focused Claude Code SDK calls."""
        artifacts = []

        # Define components to generate
        components = [
            {
                "name": "application",
                "subdir": "src",
                "system_prompt": "You are an expert Python developer specializing in FastAPI and ML services.",
                "user_prompt": self._create_application_prompt(plan),
                "timeout": 120
            },
            {
                "name": "infrastructure",
                "subdir": "terraform",
                "system_prompt": "You are an expert DevOps engineer specializing in AWS and Terraform.",
                "user_prompt": self._create_infrastructure_prompt(plan),
                "timeout": 120
            },
            {
                "name": "ci_cd",
                "subdir": ".github/workflows",
                "system_prompt": "You are an expert DevOps engineer specializing in GitHub Actions and CI/CD.",
                "user_prompt": self._create_cicd_prompt(plan),
                "timeout": 90
            }
        ]

        for component in components:
            try:
                logger.info(f"Generating {component['name']} component")
                component_artifacts = await self._generate_single_component(
                    plan, output_dir, component
                )
                artifacts.extend(component_artifacts)
                logger.info(f"Generated {len(component_artifacts)} files for {component['name']}")

            except Exception as e:
                logger.warning(f"Failed to generate {component['name']} component: {e}")
                # Continue with other components

        return artifacts

    async def _generate_single_component(
        self, plan: Dict[str, Any], output_dir: Path, component: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate a single MLOps component using Claude Code SDK."""
        target_dir = output_dir / component["subdir"]
        target_dir.mkdir(parents=True, exist_ok=True)

        # Track files before generation
        files_before = set(target_dir.glob("**/*"))

        options = ClaudeCodeOptions(
            system_prompt=component["system_prompt"],
            permission_mode='acceptEdits',
            cwd=str(target_dir),
            allowed_tools=["Write", "Read"],
        )

        async with ClaudeSDKClient(options=options) as client:
            await client.query(component["user_prompt"])

            # Consume all responses with timeout
            async def consume_responses():
                async for message in client.receive_response():
                    logger.debug(f"Component {component['name']}: {type(message).__name__}")

            await asyncio.wait_for(consume_responses(), timeout=component["timeout"])

        # Find newly created files
        files_after = set(target_dir.glob("**/*"))
        new_files = [f for f in files_after - files_before if f.is_file()]

        # Create artifacts for new files
        artifacts = []
        for file_path in new_files:
            relative_path = file_path.relative_to(output_dir)
            artifacts.append({
                "path": str(relative_path),
                "kind": self._classify_file_kind(str(relative_path)),
                "size_bytes": file_path.stat().st_size,
                "created_at": datetime.now(timezone.utc).isoformat(),
            })

        return artifacts

    def _create_application_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for application code generation."""
        services = plan.get("key_services", {})
        api_service = services.get("api", "ML inference service")

        return f"""Create a FastAPI application for {api_service}.

Include:
1. main.py - FastAPI app with health check and prediction endpoints
2. requirements.txt - Python dependencies including FastAPI, uvicorn, pydantic
3. Dockerfile - Multi-stage container build

Keep it production-ready but focused. Include proper error handling and logging."""

    def _create_infrastructure_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for infrastructure code generation."""
        architecture = plan.get("architecture_type", "app_runner")
        budget = plan.get("estimated_monthly_cost", 100)

        return f"""Create Terraform configuration for {architecture} architecture.

Budget constraint: ${budget}/month

Include:
1. main.tf - Core AWS resources (App Runner service, RDS database if needed)
2. variables.tf - Input variables
3. outputs.tf - Output values

Focus on cost-effective, secure AWS resources. Use App Runner for container deployment."""

    def _create_cicd_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for CI/CD pipeline generation."""
        phases = plan.get("implementation_phases", ["build", "test", "deploy"])

        return f"""Create GitHub Actions workflow for ML service deployment.

Implementation phases: {', '.join(phases)}

Include:
1. ci.yml - Build, test, and deploy workflow
2. deploy.yml - Production deployment workflow (optional)

Focus on container building, testing, and AWS deployment patterns."""

    async def _fallback_template_generation(
        self, plan: Dict[str, Any], output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Fallback template-based code generation when Claude SDK fails."""
        logger.warning("Using fallback template generation")

        artifacts = []

        # Generate Terraform infrastructure
        terraform_dir = output_dir / "terraform"
        terraform_dir.mkdir(exist_ok=True)

        main_tf = terraform_dir / "main.tf"
        terraform_content = self._generate_terraform_template(plan)
        main_tf.write_text(terraform_content)

        artifacts.append(
            {
                "path": "terraform/main.tf",
                "kind": "infrastructure",
                "size_bytes": len(terraform_content),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Generate application code
        src_dir = output_dir / "src"
        src_dir.mkdir(exist_ok=True)

        main_py = src_dir / "main.py"
        app_content = self._generate_application_template(plan)
        main_py.write_text(app_content)

        artifacts.append(
            {
                "path": "src/main.py",
                "kind": "application",
                "size_bytes": len(app_content),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        # Generate CI/CD configuration
        github_dir = output_dir / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)

        ci_yaml = github_dir / "ci.yml"
        ci_content = self._generate_ci_template(plan)
        ci_yaml.write_text(ci_content)

        artifacts.append(
            {
                "path": ".github/workflows/ci.yml",
                "kind": "ci_cd",
                "size_bytes": len(ci_content),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }
        )

        return artifacts

    def _normalize_sdk_message(self, message: Any) -> Dict[str, Any]:
        """Convert Claude SDK streaming messages into a dict for easier handling."""
        if isinstance(message, dict):
            return message

        if hasattr(message, "model_dump") and callable(message.model_dump):
            try:
                return message.model_dump()
            except Exception:  # pragma: no cover - defensive fallback
                pass

        if is_dataclass(message):
            try:
                return asdict(message)
            except Exception:  # pragma: no cover
                pass

        if hasattr(message, "__dict__"):
            try:
                return dict(message.__dict__)
            except Exception:  # pragma: no cover
                pass

        # Final fallback: wrap raw payload so callers can log / inspect it
        return {"type": None, "raw_message": message}

    def _create_system_prompt(self, plan: Dict[str, Any]) -> str:
        """Create system prompt for Claude Code SDK."""
        pattern_name = plan.get("pattern_name", "MLOps System")
        architecture_type = plan.get("architecture_type", "hybrid")
        key_services = plan.get("key_services", {})

        return f"""You are an expert MLOps engineer tasked with generating a production-ready {pattern_name}.

Architecture Type: {architecture_type}
Key Services: {", ".join(key_services.keys())}

Your task is to generate a complete MLOps repository with:
1. Infrastructure as Code (Terraform) for AWS deployment
2. Application code and services
3. CI/CD pipelines (GitHub Actions)
4. Configuration and documentation

Requirements:
- Use AWS best practices for security and scalability
- Include proper error handling and logging
- Follow infrastructure as code principles
- Generate comprehensive documentation

Focus on creating production-quality code that follows MLOps best practices."""

    def _create_generation_prompt(self, plan: Dict[str, Any]) -> str:
        """Create the main generation prompt."""
        services = plan.get("key_services", {})
        phases = plan.get("implementation_phases", [])
        cost_budget = plan.get("estimated_monthly_cost", 0)

        services_list = "\n".join(
            [f"- {svc}: {desc}" for svc, desc in services.items()]
        )
        phases_list = "\n".join([f"- {phase}" for phase in phases])

        return f"""Generate a complete MLOps repository with the following specifications:

**Services to implement:**
{services_list}

**Implementation phases:**
{phases_list}

**Budget constraint:** ${cost_budget}/month

Please create a repository structure including:

1. **Infrastructure (terraform/)**
   - Main Terraform configuration for AWS
   - Variables and outputs
   - Security groups and IAM roles

2. **Application code (src/)**
   - Main application files
   - API endpoints
   - Data processing pipelines

3. **CI/CD (.github/workflows/)**
   - Build and test workflows
   - Deployment pipelines

4. **Configuration**
   - Environment-specific configs
   - Logging configuration

5. **Documentation**
   - README with setup instructions
   - Deployment guide

Generate all necessary files with proper content, following AWS and MLOps best practices."""

    def _classify_file_kind(self, file_path: str) -> str:
        """Classify the type of generated file."""
        path_lower = file_path.lower()

        if "terraform" in path_lower or file_path.endswith(".tf"):
            return "infrastructure"
        elif any(ext in path_lower for ext in [".py", ".js", ".go", ".java"]):
            return "application"
        elif ".github" in path_lower or "ci" in path_lower:
            return "ci_cd"
        elif any(name in path_lower for name in ["readme", "doc", ".md"]):
            return "documentation"
        elif any(name in path_lower for name in ["config", ".env", ".yaml", ".json"]):
            return "configuration"
        else:
            return "other"

    async def _scan_generated_files(self, output_dir: Path) -> List[Dict[str, Any]]:
        """Scan directory for generated files."""
        artifacts = []

        for file_path in output_dir.rglob("*"):
            if file_path.is_file():
                relative_path = file_path.relative_to(output_dir)
                artifacts.append(
                    {
                        "path": str(relative_path),
                        "kind": self._classify_file_kind(str(relative_path)),
                        "size_bytes": file_path.stat().st_size,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

        return artifacts

    async def _create_repository_zip(
        self, source_dir: Path, zip_path: Path, plan: Dict[str, Any]
    ) -> str:
        """Create a ZIP archive of the generated repository."""
        pattern_name = plan.get("pattern_name", "mlops-project")
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
        zip_key = f"{pattern_name.lower().replace(' ', '-')}_{timestamp}.zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as zipf:
            for file_path in source_dir.rglob("*"):
                if file_path.is_file() and file_path != zip_path:
                    arcname = file_path.relative_to(source_dir)
                    zipf.write(file_path, arcname)

        logger.info(f"Created repository ZIP: {zip_key}")
        return zip_key

    async def _upload_to_s3(self, zip_path: Path, zip_key: str) -> Optional[str]:
        """Upload the repository ZIP to S3."""
        try:
            self.s3_client.upload_file(
                str(zip_path),
                self.s3_bucket,
                f"artifacts/{zip_key}",
                ExtraArgs={"ContentType": "application/zip"},
            )

            s3_url = f"s3://{self.s3_bucket}/artifacts/{zip_key}"
            logger.info(f"Uploaded repository to S3: {s3_url}")
            return s3_url

        except ClientError:
            logger.exception("Failed to upload to S3")
            return None

    def _generate_terraform_template(self, plan: Dict[str, Any]) -> str:
        """Generate basic Terraform template."""
        services = plan.get("key_services", {})

        return f"""# MLOps Infrastructure - {plan.get("pattern_name", "MLOps System")}
# Generated by Agentic MLOps Platform

terraform {{
  required_version = ">= 1.0"
  required_providers {{
    aws = {{
      source  = "hashicorp/aws"
      version = "~> 5.0"
    }}
  }}
}}

provider "aws" {{
  region = var.aws_region
}}

variable "aws_region" {{
  description = "AWS region for resources"
  type        = string
  default     = "us-east-1"
}}

variable "environment" {{
  description = "Environment name"
  type        = string
  default     = "dev"
}}

# Core infrastructure components
{self._generate_terraform_resources(services)}

output "infrastructure_info" {{
  description = "Infrastructure deployment information"
  value = {{
    region      = var.aws_region
    environment = var.environment
    services    = {list(services.keys())}
  }}
}}
"""

    def _generate_terraform_resources(self, services: Dict[str, str]) -> str:
        """Generate Terraform resources based on services."""
        resources = []

        if "lambda" in services or "serverless" in str(services).lower():
            resources.append("""
# Lambda function for serverless compute
resource "aws_lambda_function" "mlops_function" {
  filename         = "function.zip"
  function_name    = "mlops-${var.environment}-function"
  role            = aws_iam_role.lambda_role.arn
  handler         = "main.handler"
  runtime         = "python3.11"
  timeout         = 300

  tags = {
    Environment = var.environment
    Purpose     = "MLOps"
  }
}

resource "aws_iam_role" "lambda_role" {
  name = "mlops-${var.environment}-lambda-role"
  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [
      {
        Action = "sts:AssumeRole"
        Effect = "Allow"
        Principal = {
          Service = "lambda.amazonaws.com"
        }
      }
    ]
  })
}""")

        if "s3" in services:
            resources.append("""
# S3 bucket for data storage
resource "aws_s3_bucket" "mlops_data" {
  bucket = "mlops-${var.environment}-data-${random_id.bucket_suffix.hex}"
  
  tags = {
    Environment = var.environment
    Purpose     = "MLOps Data"
  }
}

resource "random_id" "bucket_suffix" {
  byte_length = 4
}""")

        return "\n".join(resources)

    def _generate_application_template(self, plan: Dict[str, Any]) -> str:
        """Generate basic application template."""
        return f'''"""
MLOps Application - {plan.get("pattern_name", "MLOps System")}
Generated by Agentic MLOps Platform
"""

import logging
import os
from datetime import datetime
from typing import Dict, Any

# Configure logging
logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(name)s %(message)s"
)
logger = logging.getLogger(__name__)


class MLOpsApplication:
    """Main MLOps application class."""
    
    def __init__(self):
        self.config = self.load_config()
        logger.info("MLOps application initialized")
    
    def load_config(self) -> Dict[str, Any]:
        """Load application configuration."""
        return {{
            "environment": os.getenv("ENVIRONMENT", "dev"),
            "aws_region": os.getenv("AWS_REGION", "us-east-1"),
            "services": {list(plan.get("key_services", {}).keys())},
            "initialized_at": datetime.utcnow().isoformat()
        }}
    
    def run(self):
        """Run the main application logic."""
        logger.info("Starting MLOps application")
        
        # Application logic here
        logger.info("MLOps application running successfully")


def handler(event, context):
    """Lambda handler function."""
    app = MLOpsApplication()
    app.run()
    
    return {{
        "statusCode": 200,
        "body": "MLOps application executed successfully"
    }}


if __name__ == "__main__":
    app = MLOpsApplication()
    app.run()
'''

    def _generate_ci_template(self, plan: Dict[str, Any]) -> str:
        """Generate CI/CD template."""
        return f"""# MLOps CI/CD Pipeline - {plan.get("pattern_name", "MLOps System")}
# Generated by Agentic MLOps Platform

name: MLOps CI/CD

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    runs-on: ubuntu-latest
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'
    
    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install -r requirements.txt
        pip install pytest ruff
    
    - name: Lint with ruff
      run: |
        ruff check .
        ruff format --check .
    
    - name: Test with pytest
      run: |
        pytest -v
    
    - name: Terraform validate
      uses: hashicorp/setup-terraform@v2
      with:
        terraform_version: 1.5.0
    
    - name: Terraform format check
      run: |
        cd terraform
        terraform fmt -check
        terraform init
        terraform validate

  deploy:
    needs: test
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    
    steps:
    - uses: actions/checkout@v4
    
    - name: Configure AWS credentials
      uses: aws-actions/configure-aws-credentials@v2
      with:
        aws-access-key-id: ${{{{ secrets.AWS_ACCESS_KEY_ID }}}}
        aws-secret-access-key: ${{{{ secrets.AWS_SECRET_ACCESS_KEY }}}}
        aws-region: us-east-1
    
    - name: Deploy infrastructure
      run: |
        cd terraform
        terraform init
        terraform plan
        terraform apply -auto-approve
    
    - name: Deploy application
      run: |
        # Application deployment logic here
        echo "Deploying MLOps application..."
"""


class CodegenError(Exception):
    """Custom exception for code generation errors."""

    pass
