"""
Integration tests for code generation workflow.

Tests the complete code generation and validation pipeline.
"""

import pytest
from unittest.mock import patch, Mock, AsyncMock

from libs.graph import (
    _codegen_async,
    _validators_async,
    _create_validation_test_structure,
)
from libs.agent_framework import MLOpsWorkflowState


class TestCodegenIntegration:
    """Test suite for code generation integration."""

    @pytest.fixture
    def sample_state_with_approved_plan(self):
        """Create a state with an approved plan for code generation."""
        return MLOpsWorkflowState(
            project_id="test_codegen",
            decision_set_id="decision_codegen_001",
            version=1,
            plan={
                "pattern_name": "Serverless ML Pipeline",
                "architecture_type": "serverless",
                "estimated_monthly_cost": 350,
                "key_services": {
                    "lambda": "Serverless functions",
                    "s3": "Data storage",
                    "apigateway": "API endpoints",
                },
                "implementation_phases": [
                    "Setup AWS infrastructure",
                    "Deploy Lambda functions",
                    "Configure API Gateway",
                    "Add monitoring",
                ],
            },
            hitl={
                "status": "approved",
                "comment": "Plan approved for testing",
                "approved_by": "test_manager",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )

    @pytest.fixture
    def sample_state_not_approved(self):
        """Create a state with a non-approved plan."""
        return MLOpsWorkflowState(
            project_id="test_codegen",
            decision_set_id="decision_codegen_002",
            version=1,
            plan={"pattern_name": "Test Pattern", "architecture_type": "hybrid"},
            hitl={
                "status": "pending",
                "comment": "",
                "timestamp": "2025-01-01T00:00:00Z",
            },
        )

    @pytest.mark.asyncio
    async def test_codegen_with_approved_plan(self, sample_state_with_approved_plan):
        """Test code generation with an approved plan."""
        # Mock CodegenService to avoid external dependencies
        with patch("libs.codegen_service.CodegenService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock successful repository generation
            mock_service.generate_mlops_repository = AsyncMock(
                return_value={
                    "artifacts": [
                        {
                            "path": "terraform/main.tf",
                            "kind": "infrastructure",
                            "size_bytes": 1024,
                            "created_at": "2025-01-01T00:00:00Z",
                        },
                        {
                            "path": "src/lambda_handler.py",
                            "kind": "application",
                            "size_bytes": 512,
                            "created_at": "2025-01-01T00:00:00Z",
                        },
                    ],
                    "repository_zip": {
                        "local_path": "/tmp/repo.zip",
                        "s3_url": "s3://test-bucket/artifacts/serverless_ml_pipeline.zip",
                        "zip_key": "serverless_ml_pipeline_20250101_120000.zip",
                        "size_bytes": 2048,
                    },
                    "generated_at": "2025-01-01T00:00:00Z",
                    "plan_used": "Serverless ML Pipeline",
                }
            )

            result = await _codegen_async(sample_state_with_approved_plan)

            # Verify successful code generation
            assert "artifacts" in result
            assert "repository" in result
            assert "error" not in result

            # Verify artifacts
            artifacts = result["artifacts"]
            assert len(artifacts) == 2
            assert any(a["path"] == "terraform/main.tf" for a in artifacts)
            assert any(a["path"] == "src/lambda_handler.py" for a in artifacts)

            # Verify repository info
            repository_info = result["repository"]
            assert repository_info["size_bytes"] == 2048
            assert "s3://test-bucket" in repository_info["s3_url"]
            assert repository_info["zip_key"].startswith("serverless_ml_pipeline")

            # Verify service was called with correct plan
            mock_service.generate_mlops_repository.assert_called_once_with(
                sample_state_with_approved_plan["plan"]
            )

    @pytest.mark.asyncio
    async def test_codegen_with_non_approved_plan(self, sample_state_not_approved):
        """Test code generation with non-approved plan should be skipped."""
        result = await _codegen_async(sample_state_not_approved)

        # Should skip code generation
        assert result["artifacts"] == []
        assert result["repository"] == {}
        assert "error" in result
        assert "not approved" in result["error"]

    @pytest.mark.asyncio
    async def test_codegen_with_missing_plan(self):
        """Test code generation with missing plan."""
        state_without_plan = MLOpsWorkflowState(
            project_id="test_codegen",
            decision_set_id="decision_codegen_003",
            version=1,
            hitl={"status": "approved"},
        )

        result = await _codegen_async(state_without_plan)

        # Should fail due to missing plan
        assert result["artifacts"] == []
        assert result["repository"] == {}
        assert "error" in result
        assert "No plan available" in result["error"]

    @pytest.mark.asyncio
    async def test_codegen_service_failure(self, sample_state_with_approved_plan):
        """Test code generation when service fails."""
        from libs.codegen_service import CodegenError

        # Mock CodegenService to fail
        with patch("libs.codegen_service.CodegenService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.generate_mlops_repository = AsyncMock(
                side_effect=CodegenError("Code generation failed")
            )

            result = await _codegen_async(sample_state_with_approved_plan)

            # Should handle error gracefully
            assert result["artifacts"] == []
            assert result["repository"] == {}
            assert "error" in result
            assert "Code generation failed" in result["error"]

    @pytest.mark.asyncio
    async def test_validators_with_artifacts(self):
        """Test validation with generated artifacts."""
        state_with_artifacts = MLOpsWorkflowState(
            project_id="test_validation",
            decision_set_id="decision_validation_001",
            version=1,
            artifacts=[
                {
                    "path": "terraform/main.tf",
                    "kind": "infrastructure",
                    "size_bytes": 1024,
                    "created_at": "2025-01-01T00:00:00Z",
                },
                {
                    "path": "src/main.py",
                    "kind": "application",
                    "size_bytes": 512,
                    "created_at": "2025-01-01T00:00:00Z",
                },
            ],
            repository={
                "size_bytes": 2048,
                "s3_url": "s3://test-bucket/artifacts/test.zip",
                "zip_key": "test_20250101_120000.zip",
            },
        )

        # Mock ValidationService
        with patch("libs.validation_service.ValidationService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service

            # Mock successful validation
            mock_service.validate_artifacts = AsyncMock(
                return_value={
                    "terraform_validate": {"status": "pass", "issues": []},
                    "ruff_check": {"status": "pass", "issues": []},
                    "security_scan": {
                        "status": "pass",
                        "secrets_found": 0,
                        "issues": [],
                    },
                    "general_checks": {"status": "pass", "issues": []},
                    "overall_status": "pass",
                    "artifacts_validated": 2,
                    "validation_timestamp": "2025-01-01T00:00:00Z",
                }
            )

            result = await _validators_async(state_with_artifacts)

            # Verify validation results
            assert "reports" in result
            reports = result["reports"]

            assert reports["overall_status"] == "pass"
            assert reports["artifacts_validated"] == 2
            assert "repository_info" in reports
            assert reports["repository_info"]["size_bytes"] == 2048

            # Verify validation service was called
            mock_service.validate_artifacts.assert_called_once()

    @pytest.mark.asyncio
    async def test_validators_with_no_artifacts(self):
        """Test validation with no artifacts."""
        state_without_artifacts = MLOpsWorkflowState(
            project_id="test_validation",
            decision_set_id="decision_validation_002",
            version=1,
        )

        result = await _validators_async(state_without_artifacts)

        # Should skip validation
        assert "reports" in result
        reports = result["reports"]

        assert reports["overall_status"] == "skipped"
        assert reports["artifacts_validated"] == 0
        assert "No artifacts available" in reports["message"]

    @pytest.mark.asyncio
    async def test_validators_service_failure(self):
        """Test validation when service fails."""
        from libs.validation_service import ValidationError

        state_with_artifacts = MLOpsWorkflowState(
            project_id="test_validation",
            decision_set_id="decision_validation_003",
            version=1,
            artifacts=[
                {
                    "path": "test.py",
                    "kind": "application",
                    "size_bytes": 100,
                    "created_at": "2025-01-01T00:00:00Z",
                }
            ],
        )

        # Mock ValidationService to fail
        with patch("libs.validation_service.ValidationService") as mock_service_class:
            mock_service = Mock()
            mock_service_class.return_value = mock_service
            mock_service.validate_artifacts = AsyncMock(
                side_effect=ValidationError("Validation failed")
            )

            result = await _validators_async(state_with_artifacts)

            # Should handle error gracefully
            assert "reports" in result
            reports = result["reports"]

            assert reports["overall_status"] == "error"
            assert reports["artifacts_validated"] == 1
            assert "Validation failed" in reports["error"]

    @pytest.mark.asyncio
    async def test_create_validation_test_structure(self):
        """Test the helper function for creating validation test structure."""
        import tempfile
        from pathlib import Path

        artifacts = [
            {
                "path": "terraform/main.tf",
                "kind": "infrastructure",
                "size_bytes": 100,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "path": "src/app.py",
                "kind": "application",
                "size_bytes": 200,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "path": ".github/workflows/ci.yml",
                "kind": "ci_cd",
                "size_bytes": 150,
                "created_at": "2025-01-01T00:00:00Z",
            },
        ]

        state = {}

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            await _create_validation_test_structure(temp_path, artifacts, state)

            # Verify directory structure was created
            assert (temp_path / "terraform").exists()
            assert (temp_path / "src").exists()
            assert (temp_path / ".github" / "workflows").exists()

            # Verify files were created with appropriate content
            terraform_file = temp_path / "terraform" / "main.tf"
            assert terraform_file.exists()
            content = terraform_file.read_text()
            assert "resource" in content
            assert "aws_instance" in content

            python_file = temp_path / "src" / "app.py"
            assert python_file.exists()
            content = python_file.read_text()
            assert "def main" in content
            assert 'print("Hello MLOps")' in content

            ci_file = temp_path / ".github" / "workflows" / "ci.yml"
            assert ci_file.exists()
            content = ci_file.read_text()
            assert "name: MLOps Pipeline" in content
            assert "runs-on: ubuntu-latest" in content

    @pytest.mark.asyncio
    async def test_full_codegen_to_validation_workflow(
        self, sample_state_with_approved_plan
    ):
        """Test complete workflow from code generation to validation."""
        # Mock both services
        with (
            patch("libs.codegen_service.CodegenService") as mock_codegen_service_class,
            patch(
                "libs.validation_service.ValidationService"
            ) as mock_validation_service_class,
        ):
            # Setup codegen mock
            mock_codegen_service = Mock()
            mock_codegen_service_class.return_value = mock_codegen_service
            mock_codegen_service.generate_mlops_repository = AsyncMock(
                return_value={
                    "artifacts": [
                        {
                            "path": "terraform/main.tf",
                            "kind": "infrastructure",
                            "size_bytes": 1024,
                            "created_at": "2025-01-01T00:00:00Z",
                        },
                        {
                            "path": "src/main.py",
                            "kind": "application",
                            "size_bytes": 512,
                            "created_at": "2025-01-01T00:00:00Z",
                        },
                    ],
                    "repository_zip": {
                        "local_path": "/tmp/repo.zip",
                        "s3_url": "s3://test-bucket/artifacts/test.zip",
                        "zip_key": "test_20250101_120000.zip",
                        "size_bytes": 1536,
                    },
                    "generated_at": "2025-01-01T00:00:00Z",
                    "plan_used": "Serverless ML Pipeline",
                }
            )

            # Setup validation mock
            mock_validation_service = Mock()
            mock_validation_service_class.return_value = mock_validation_service
            mock_validation_service.validate_artifacts = AsyncMock(
                return_value={
                    "terraform_validate": {"status": "pass", "issues": []},
                    "ruff_check": {"status": "pass", "issues": []},
                    "security_scan": {
                        "status": "pass",
                        "secrets_found": 0,
                        "issues": [],
                    },
                    "general_checks": {"status": "pass", "issues": []},
                    "overall_status": "pass",
                    "artifacts_validated": 2,
                    "validation_timestamp": "2025-01-01T00:00:00Z",
                }
            )

            # Step 1: Generate code
            codegen_result = await _codegen_async(sample_state_with_approved_plan)

            # Verify code generation succeeded
            assert "artifacts" in codegen_result
            assert "repository" in codegen_result
            assert len(codegen_result["artifacts"]) == 2

            # Step 2: Update state with generated artifacts
            updated_state = sample_state_with_approved_plan.copy()
            updated_state.update(codegen_result)

            # Step 3: Validate generated code
            validation_result = await _validators_async(updated_state)

            # Verify validation succeeded
            assert "reports" in validation_result
            reports = validation_result["reports"]
            assert reports["overall_status"] == "pass"
            assert reports["artifacts_validated"] == 2
            assert "repository_info" in reports

            # Verify both services were called appropriately
            mock_codegen_service.generate_mlops_repository.assert_called_once()
            mock_validation_service.validate_artifacts.assert_called_once()
