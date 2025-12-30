"""
Code Generation Service using OpenAI API.

Alternative implementation of code generation using OpenAI's GPT models
instead of Claude Code SDK. This allows users to generate MLOps repositories
using OpenAI API when Claude/Anthropic API is not available.
"""

import asyncio
import logging
import os
import tempfile
import shutil
import zipfile
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any, Optional

import boto3
from botocore.exceptions import ClientError

from libs.llm_client import get_llm_client, OpenAIClient

logger = logging.getLogger(__name__)


class OpenAICodegenService:
    """Service for generating MLOps code artifacts using OpenAI API."""

    def __init__(self):
        self.s3_client = None
        self.s3_bucket = os.getenv("S3_BUCKET_NAME")
        self.llm_client: Optional[OpenAIClient] = None

        if self.s3_bucket:
            try:
                self.s3_client = boto3.client("s3")
            except Exception as e:
                logger.warning(f"Failed to initialize S3 client: {e}")

    def _get_llm_client(self) -> OpenAIClient:
        """Get or create LLM client instance."""
        if self.llm_client is None:
            self.llm_client = get_llm_client()
        return self.llm_client

    async def generate_mlops_repository(self, plan: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate a complete MLOps repository based on the approved plan.

        Args:
            plan: The approved MLOps plan containing architecture details

        Returns:
            Dict containing artifact information and file paths
        """
        logger.info(
            "Starting MLOps repository generation with OpenAI",
            extra={
                "pattern": plan.get("pattern_name", "unknown"),
                "services": len(plan.get("key_services", {})),
            },
        )

        try:
            # Create temporary directory for generated code
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)

                # Generate code using OpenAI
                artifacts = await self._generate_code_with_openai(plan, temp_path)

                # Create reports directory
                reports_dir = temp_path / "reports"
                reports_dir.mkdir(exist_ok=True)

                # Create repository ZIP
                zip_path = temp_path / "mlops_repository.zip"
                zip_key = await self._create_repository_zip(temp_path, zip_path, plan)

                # Persist ZIP locally for download
                persisted_zip = self._persist_zip(zip_path, zip_key)

                # Upload to S3 if available
                s3_url = None
                if self.s3_client and self.s3_bucket:
                    s3_url = await self._upload_to_s3(zip_path, zip_key)

                return {
                    "artifacts": artifacts,
                    "repository_zip": {
                        "local_path": str(persisted_zip),
                        "s3_url": s3_url,
                        "zip_key": zip_key,
                        "size_bytes": persisted_zip.stat().st_size
                        if persisted_zip.exists()
                        else 0,
                    },
                    "generated_at": datetime.now(timezone.utc).isoformat(),
                    "plan_used": plan.get("pattern_name", "unknown"),
                    "generator": "openai",
                }

        except Exception as e:
            logger.exception("Failed to generate MLOps repository with OpenAI")
            raise CodegenError(f"Repository generation failed: {str(e)}")

    def _persist_zip(self, zip_path: Path, zip_key: str) -> Path:
        artifacts_dir = Path(
            os.getenv("ARTIFACTS_DIR", "./artifacts")
        ).resolve()
        artifacts_dir.mkdir(parents=True, exist_ok=True)
        target_path = artifacts_dir / zip_key
        shutil.copyfile(zip_path, target_path)
        return target_path

    async def _generate_code_with_openai(
        self, plan: Dict[str, Any], output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Generate code files using OpenAI API."""
        logger.info("Generating code with OpenAI API")

        try:
            # Generate components separately for better quality
            artifacts = await self._generate_decomposed_components(plan, output_dir)
            logger.info(
                f"Generated {len(artifacts)} code artifacts using OpenAI decomposed approach"
            )
            return artifacts

        except Exception as e:
            logger.exception("OpenAI code generation failed")
            raise CodegenError(f"OpenAI generation failed: {str(e)}")

    async def _generate_decomposed_components(
        self, plan: Dict[str, Any], output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Generate MLOps components using multiple focused OpenAI calls."""
        artifacts = []

        # Define components to generate
        components = [
            {
                "name": "infrastructure",
                "subdir": "terraform",
                "prompt_builder": self._create_infrastructure_prompt,
                "file_patterns": ["*.tf"],
            },
            {
                "name": "application",
                "subdir": "src",
                "prompt_builder": self._create_application_prompt,
                "file_patterns": ["*.py", "requirements.txt", "Dockerfile"],
            },
            {
                "name": "ci_cd",
                "subdir": ".github/workflows",
                "prompt_builder": self._create_cicd_prompt,
                "file_patterns": ["*.yml", "*.yaml"],
            },
            {
                "name": "documentation",
                "subdir": ".",
                "prompt_builder": self._create_documentation_prompt,
                "file_patterns": ["README.md", "DEPLOYMENT.md"],
            },
        ]

        for component in components:
            try:
                logger.info(f"Generating {component['name']} component with OpenAI")
                component_artifacts = await self._generate_single_component(
                    plan, output_dir, component
                )
                artifacts.extend(component_artifacts)
                logger.info(
                    f"Generated {len(component_artifacts)} files for {component['name']}"
                )

            except Exception as e:
                logger.warning(
                    f"Failed to generate {component['name']} component: {e}"
                )
                # Continue with other components

        return artifacts

    async def _generate_single_component(
        self, plan: Dict[str, Any], output_dir: Path, component: Dict[str, Any]
    ) -> List[Dict[str, Any]]:
        """Generate a single MLOps component using OpenAI."""
        target_dir = output_dir / component["subdir"]
        target_dir.mkdir(parents=True, exist_ok=True)

        # Create generation prompt
        prompt = component["prompt_builder"](plan)

        # Get LLM client
        client = self._get_llm_client()

        # Generate code with OpenAI
        messages = [
            {
                "role": "system",
                "content": "You are an expert MLOps engineer. Generate production-ready code following best practices. "
                "Return ONLY the file content without any markdown formatting or explanations. "
                "When generating multiple files, separate them with '--- FILE: filename ---' markers.",
            },
            {"role": "user", "content": prompt},
        ]

        response = await client.complete(messages=messages, max_tokens=4000)

        # Parse response and create files
        artifacts = self._parse_and_write_files(response, target_dir, output_dir)

        return artifacts

    def _parse_and_write_files(
        self, response: str, target_dir: Path, output_dir: Path
    ) -> List[Dict[str, Any]]:
        """Parse OpenAI response and write files to disk."""
        artifacts = []

        # Check if response contains file markers
        if "--- FILE:" in response:
            # Multi-file response
            file_sections = response.split("--- FILE:")

            for section in file_sections[1:]:  # Skip first empty section
                lines = section.strip().split("\n", 1)
                if len(lines) < 2:
                    continue

                filename = lines[0].strip().replace("---", "").strip()
                content = lines[1].strip()

                # Clean markdown code blocks if present
                content = self._clean_code_blocks(content)

                # Write file
                file_path = target_dir / filename
                file_path.parent.mkdir(parents=True, exist_ok=True)
                file_path.write_text(content)

                # Create artifact entry
                relative_path = file_path.relative_to(output_dir)
                artifacts.append(
                    {
                        "path": str(relative_path),
                        "kind": self._classify_file_kind(str(relative_path)),
                        "size_bytes": file_path.stat().st_size,
                        "created_at": datetime.now(timezone.utc).isoformat(),
                    }
                )

        else:
            # Single file response - determine filename from component
            content = self._clean_code_blocks(response)

            # Determine appropriate filename
            filename = self._determine_filename_from_content(content, target_dir)

            file_path = target_dir / filename
            file_path.write_text(content)

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

    def _clean_code_blocks(self, content: str) -> str:
        """Remove markdown code blocks from content."""
        lines = content.split("\n")
        cleaned_lines = []
        in_code_block = False

        for line in lines:
            if line.strip().startswith("```"):
                in_code_block = not in_code_block
                continue
            if not in_code_block or line.strip():
                cleaned_lines.append(line)

        return "\n".join(cleaned_lines).strip()

    def _determine_filename_from_content(
        self, content: str, target_dir: Path
    ) -> str:
        """Determine appropriate filename based on content and target directory."""
        dir_name = target_dir.name

        if dir_name == "terraform":
            return "main.tf"
        elif dir_name == "src":
            return "main.py"
        elif dir_name == "workflows":
            return "ci.yml"
        elif "README" in content[:100].upper():
            return "README.md"
        else:
            return "generated_file.txt"

    def _create_infrastructure_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for infrastructure code generation."""
        architecture = plan.get("architecture_type", "app_runner")
        budget = plan.get("estimated_monthly_cost", 100)
        services = plan.get("key_services", {})

        return f"""Generate Terraform infrastructure code for an MLOps system with the following requirements:

**Architecture Type:** {architecture}
**Monthly Budget:** ${budget}
**Services:** {', '.join(services.keys())}

Create the following files (use '--- FILE: filename ---' markers to separate):

--- FILE: main.tf ---
[Complete Terraform main configuration with AWS provider, resources for App Runner service, RDS database if needed, S3 buckets for artifacts]

--- FILE: variables.tf ---
[Input variables for region, environment, instance types]

--- FILE: outputs.tf ---
[Output values for service URLs, database endpoints, S3 bucket names]

Requirements:
- Use AWS App Runner for container deployment
- Include RDS PostgreSQL if database is needed
- Add S3 bucket for ML model artifacts
- Use cost-effective configurations within budget
- Follow security best practices (IAM roles, security groups)
- Add proper tags for resource management
"""

    def _create_application_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for application code generation."""
        services = plan.get("key_services", {})
        api_service = services.get("api", "ML inference service")

        return f"""Generate production-ready Python application code for: {api_service}

Create the following files (use '--- FILE: filename ---' markers to separate):

--- FILE: main.py ---
[FastAPI application with:
- Health check endpoint (/health)
- Prediction endpoint (/predict)
- Proper error handling and logging
- Request/response models using Pydantic
- Database connection if needed]

--- FILE: requirements.txt ---
[Python dependencies:
- fastapi
- uvicorn[standard]
- pydantic
- sqlalchemy (if database needed)
- boto3 (for S3 access)
- python-json-logger
- Other ML libraries as needed]

--- FILE: Dockerfile ---
[Multi-stage Docker build:
- Use python:3.11-slim base image
- Install dependencies efficiently
- Copy application code
- Expose port 8000
- Use uvicorn as the server
- Include health check]

Requirements:
- Production-ready code with proper error handling
- Structured logging
- Environment variable configuration
- Optimized Docker image
"""

    def _create_cicd_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for CI/CD pipeline generation."""
        phases = plan.get("implementation_phases", ["build", "test", "deploy"])

        return f"""Generate GitHub Actions workflow for CI/CD pipeline.

Create the following file:

--- FILE: ci.yml ---
[Complete GitHub Actions workflow with:
- Trigger on push to main and pull requests
- Jobs: test, build, deploy
- Test job: Python linting (ruff), unit tests (pytest), Terraform validation
- Build job: Build and push Docker image to AWS ECR
- Deploy job: Deploy to AWS App Runner (only on main branch)
- Use AWS credentials from GitHub secrets
- Proper job dependencies and conditions]

Implementation phases: {', '.join(phases)}

Requirements:
- Use latest GitHub Actions versions
- Include all necessary AWS setup steps
- Add proper caching for dependencies
- Use environment variables for configuration
- Follow security best practices for credentials
"""

    def _create_documentation_prompt(self, plan: Dict[str, Any]) -> str:
        """Create prompt for documentation generation."""
        pattern_name = plan.get("pattern_name", "MLOps System")
        architecture = plan.get("architecture_type", "app_runner")
        services = plan.get("key_services", {})

        return f"""Generate comprehensive documentation for the MLOps project.

Create the following files (use '--- FILE: filename ---' markers to separate):

--- FILE: README.md ---
[Complete README with:
- Project title: {pattern_name}
- Overview and features
- Architecture diagram (text/ASCII)
- Prerequisites (Python 3.11+, AWS account, Terraform, Docker)
- Quick start instructions
- Local development setup
- Environment variables configuration
- Testing instructions
- Deployment guide
- Project structure
- Contributing guidelines]

--- FILE: DEPLOYMENT.md ---
[Deployment guide with:
- AWS prerequisites and setup
- Terraform deployment steps
- Environment configuration
- CI/CD setup with GitHub Actions
- Monitoring and logging
- Troubleshooting common issues
- Rollback procedures]

Project Details:
- Pattern: {pattern_name}
- Architecture: {architecture}
- Services: {', '.join(services.keys())}

Requirements:
- Clear, actionable instructions
- Include all necessary commands
- Security best practices
- Production readiness checklist
"""

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
        elif any(
            name in path_lower for name in ["config", ".env", ".yaml", ".json"]
        ):
            return "configuration"
        else:
            return "other"

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


class CodegenError(Exception):
    """Custom exception for code generation errors."""

    pass
