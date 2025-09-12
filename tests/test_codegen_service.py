"""
Test cases for CodegenService functionality.

Tests the Claude Code SDK integration and artifact generation.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock, AsyncMock

from libs.codegen_service import CodegenService, CodegenError


class TestCodegenService:
    """Test suite for CodegenService."""
    
    @pytest.fixture
    def codegen_service(self):
        """Create a CodegenService instance for testing."""
        return CodegenService()
    
    @pytest.fixture
    def sample_plan(self):
        """Create a sample MLOps plan for testing."""
        return {
            "pattern_name": "Serverless ML Stack",
            "architecture_type": "serverless",
            "estimated_monthly_cost": 420,
            "key_services": {
                "lambda": "Serverless compute",
                "s3": "Data storage",
                "sagemaker": "Model hosting"
            },
            "implementation_phases": [
                "Setup infrastructure",
                "Deploy models",
                "Add monitoring"
            ]
        }
    
    @pytest.mark.asyncio
    async def test_generate_mlops_repository_success_with_claude_sdk(self, codegen_service, sample_plan):
        """Test successful MLOps repository generation with Claude SDK."""
        # Mock Claude Code SDK
        with patch('libs.codegen_service.ClaudeCodeOptions') as mock_options_class, \
             patch('libs.codegen_service.ClaudeSDKClient') as mock_client_class:
            
            # Mock options
            mock_options = Mock()
            mock_options_class.return_value = mock_options
            
            # Mock the async context manager
            mock_client = AsyncMock()
            mock_client_class.return_value.__aenter__.return_value = mock_client
            mock_client_class.return_value.__aexit__.return_value = None
            
            # Mock client methods
            mock_client.query = AsyncMock()
            
            # Mock streaming response
            mock_messages = [
                {"type": "file_created", "file_info": {"path": "terraform/main.tf", "size": 1024}},
                {"type": "file_created", "file_info": {"path": "src/main.py", "size": 512}},
                {"type": "completion", "status": "done"}
            ]
            
            async def mock_receive():
                for msg in mock_messages:
                    yield msg
            
            mock_client.receive_response.return_value = mock_receive()
            
            # Mock S3 upload (no S3 configured)
            codegen_service.s3_client = None
            
            result = await codegen_service.generate_mlops_repository(sample_plan)
            
            # Verify result structure
            assert "artifacts" in result
            assert "repository_zip" in result
            assert "generated_at" in result
            assert "plan_used" in result
            
            # Verify artifacts
            artifacts = result["artifacts"]
            assert len(artifacts) >= 2  # At least terraform and python files
            
            # Verify repository info
            repo_info = result["repository_zip"]
            assert "zip_key" in repo_info
            assert "size_bytes" in repo_info
            assert repo_info["s3_url"] is None  # No S3 configured
            
            # Verify Claude SDK was called correctly
            mock_client.query.assert_called_once()
            mock_client.receive_response.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_mlops_repository_fallback(self, codegen_service, sample_plan):
        """Test MLOps repository generation using fallback templates when Claude SDK fails."""
        # Mock Claude Code SDK to fail
        with patch('libs.codegen_service.ClaudeCodeOptions') as mock_options_class:
            mock_options_class.side_effect = Exception("Claude SDK not available")
            
            # Mock S3 (not available)
            codegen_service.s3_client = None
            
            result = await codegen_service.generate_mlops_repository(sample_plan)
            
            # Should still succeed with fallback
            assert "artifacts" in result
            artifacts = result["artifacts"]
            assert len(artifacts) >= 3  # terraform, python, ci files
            
            # Check artifact types
            artifact_paths = [a["path"] for a in artifacts]
            assert "terraform/main.tf" in artifact_paths
            assert "src/main.py" in artifact_paths
            assert ".github/workflows/ci.yml" in artifact_paths
    
    
    def test_classify_file_kind(self, codegen_service):
        """Test file classification logic."""
        test_cases = [
            ("terraform/main.tf", "infrastructure"),
            ("src/main.py", "application"),
            ("app.js", "application"),
            (".github/workflows/ci.yml", "ci_cd"),
            ("README.md", "documentation"),
            ("config.yaml", "configuration"),
            ("random.txt", "other")
        ]
        
        for file_path, expected_kind in test_cases:
            assert codegen_service._classify_file_kind(file_path) == expected_kind
    
    def test_create_system_prompt(self, codegen_service, sample_plan):
        """Test system prompt generation."""
        prompt = codegen_service._create_system_prompt(sample_plan)
        
        # Check that key elements are included
        assert "Serverless ML Stack" in prompt
        assert "serverless" in prompt
        assert "lambda" in prompt
        assert "MLOps engineer" in prompt
        assert "production-ready" in prompt
    
    def test_create_generation_prompt(self, codegen_service, sample_plan):
        """Test generation prompt creation."""
        prompt = codegen_service._create_generation_prompt(sample_plan)
        
        # Check that plan details are included
        assert "lambda: Serverless compute" in prompt
        assert "$420/month" in prompt
        assert "terraform/" in prompt
        assert "src/" in prompt
        assert ".github/workflows/" in prompt
    
    def test_generate_terraform_template(self, codegen_service, sample_plan):
        """Test Terraform template generation."""
        terraform_content = codegen_service._generate_terraform_template(sample_plan)
        
        # Check basic Terraform structure
        assert "terraform {" in terraform_content
        assert "provider \"aws\"" in terraform_content
        assert "variable \"aws_region\"" in terraform_content
        assert "Serverless ML Stack" in terraform_content
        
        # Check that services are included
        if "lambda" in sample_plan["key_services"]:
            assert "aws_lambda_function" in terraform_content
        if "s3" in sample_plan["key_services"]:
            assert "aws_s3_bucket" in terraform_content
    
    def test_generate_application_template(self, codegen_service, sample_plan):
        """Test application template generation."""
        app_content = codegen_service._generate_application_template(sample_plan)
        
        # Check basic Python structure
        assert "class MLOpsApplication" in app_content
        assert "def handler(event, context)" in app_content
        assert "Serverless ML Stack" in app_content
        assert "lambda" in app_content  # Service included
    
    def test_generate_ci_template(self, codegen_service, sample_plan):
        """Test CI/CD template generation."""
        ci_content = codegen_service._generate_ci_template(sample_plan)
        
        # Check basic GitHub Actions structure
        assert "name: MLOps CI/CD" in ci_content
        assert "on:" in ci_content
        assert "jobs:" in ci_content
        assert "terraform validate" in ci_content
        assert "pytest" in ci_content
        assert "ruff" in ci_content
    
    @pytest.mark.asyncio
    async def test_s3_upload_success(self, codegen_service):
        """Test successful S3 upload."""
        # Mock boto3 S3 client
        mock_s3_client = Mock()
        mock_s3_client.upload_file.return_value = None
        codegen_service.s3_client = mock_s3_client
        codegen_service.s3_bucket = "test-bucket"
        
        with tempfile.NamedTemporaryFile(suffix='.zip') as temp_file:
            temp_path = Path(temp_file.name)
            zip_key = "test_project_20250101_120000.zip"
            
            s3_url = await codegen_service._upload_to_s3(temp_path, zip_key)
            
            assert s3_url == "s3://test-bucket/artifacts/test_project_20250101_120000.zip"
            mock_s3_client.upload_file.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_s3_upload_failure(self, codegen_service):
        """Test S3 upload failure handling."""
        from botocore.exceptions import ClientError
        
        # Mock boto3 S3 client to fail
        mock_s3_client = Mock()
        mock_s3_client.upload_file.side_effect = ClientError(
            error_response={'Error': {'Code': 'NoSuchBucket'}},
            operation_name='upload_file'
        )
        codegen_service.s3_client = mock_s3_client
        codegen_service.s3_bucket = "nonexistent-bucket"
        
        with tempfile.NamedTemporaryFile(suffix='.zip') as temp_file:
            temp_path = Path(temp_file.name)
            zip_key = "test_project_20250101_120000.zip"
            
            s3_url = await codegen_service._upload_to_s3(temp_path, zip_key)
            
            # Should return None on failure
            assert s3_url is None
    
    @pytest.mark.asyncio
    async def test_repository_generation_error_handling(self, codegen_service):
        """Test error handling in repository generation."""
        invalid_plan = {}  # Empty plan should cause issues
        
        # Mock Claude SDK to fail
        with patch('libs.codegen_service.ClaudeSDKClient') as mock_client_class:
            mock_client_class.side_effect = Exception("Critical failure")
            
            # Mock fallback to also fail
            with patch.object(codegen_service, '_fallback_template_generation') as mock_fallback:
                mock_fallback.side_effect = Exception("Fallback also failed")
                
                with pytest.raises(CodegenError):
                    await codegen_service.generate_mlops_repository(invalid_plan)


class TestCodegenServiceIntegration:
    """Integration tests for CodegenService with real file operations."""
    
    @pytest.mark.asyncio
    async def test_end_to_end_repository_creation(self):
        """Test end-to-end repository creation with real file operations."""
        codegen_service = CodegenService()
        
        # Disable S3 for testing
        codegen_service.s3_client = None
        
        sample_plan = {
            "pattern_name": "Test MLOps System",
            "architecture_type": "hybrid",
            "estimated_monthly_cost": 500,
            "key_services": {
                "ec2": "Compute instances",
                "rds": "Database"
            },
            "implementation_phases": ["Deploy", "Test"]
        }
        
        # Use fallback template generation (Claude SDK not available in CI)
        with patch('libs.codegen_service.ClaudeSDKClient') as mock_client:
            mock_client.side_effect = Exception("SDK not available in tests")
            
            result = await codegen_service.generate_mlops_repository(sample_plan)
            
            # Verify the repository was created
            assert result["repository_zip"]["size_bytes"] > 0
            assert "Test MLOps System" in result["plan_used"]
            
            # Verify artifacts were created
            artifacts = result["artifacts"]
            assert len(artifacts) >= 3
            
            # Check that we have different types of files
            kinds = set(artifact["kind"] for artifact in artifacts)
            assert "infrastructure" in kinds
            assert "application" in kinds
            assert "ci_cd" in kinds