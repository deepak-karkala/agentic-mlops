"""
Test cases for ValidationService functionality.

Tests the static validation checks for generated MLOps code.
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch

from libs.validation_service import ValidationService


class TestValidationService:
    """Test suite for ValidationService."""

    @pytest.fixture
    def validation_service(self):
        """Create a ValidationService instance for testing."""
        return ValidationService()

    @pytest.fixture
    def sample_artifacts(self):
        """Create sample artifacts for testing."""
        return [
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
            {
                "path": ".github/workflows/ci.yml",
                "kind": "ci_cd",
                "size_bytes": 256,
                "created_at": "2025-01-01T00:00:00Z",
            },
        ]

    @pytest.mark.asyncio
    async def test_validate_artifacts_success(
        self, validation_service, sample_artifacts
    ):
        """Test successful artifact validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create test files
            await self._create_valid_test_files(temp_path, sample_artifacts)

            # Mock external commands to return success
            with patch.object(validation_service, "_run_command") as mock_run:
                mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

                result = await validation_service.validate_artifacts(
                    temp_path, sample_artifacts
                )

                # Check result structure
                assert "terraform_validate" in result
                assert "ruff_check" in result
                assert "security_scan" in result
                assert "general_checks" in result
                assert "overall_status" in result
                assert "artifacts_validated" in result

                # Should pass with no issues
                assert result["overall_status"] == "pass"
                assert result["artifacts_validated"] == len(sample_artifacts)

    @pytest.mark.asyncio
    async def test_terraform_validation_success(
        self, validation_service, sample_artifacts
    ):
        """Test successful Terraform validation."""
        terraform_artifacts = [
            a for a in sample_artifacts if a["kind"] == "infrastructure"
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create terraform directory and files
            terraform_dir = temp_path / "terraform"
            terraform_dir.mkdir()
            (terraform_dir / "main.tf").write_text("""
resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
  
  tags = {
    Name = "Example"
  }
}
            """)

            # Mock successful terraform commands
            with patch.object(validation_service, "_run_command") as mock_run:
                mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

                result = await validation_service._run_terraform_validation(
                    temp_path, terraform_artifacts
                )

                assert result["status"] == "pass"
                assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_terraform_validation_failure(
        self, validation_service, sample_artifacts
    ):
        """Test Terraform validation failure."""
        terraform_artifacts = [
            a for a in sample_artifacts if a["kind"] == "infrastructure"
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create terraform directory
            terraform_dir = temp_path / "terraform"
            terraform_dir.mkdir()
            (terraform_dir / "main.tf").write_text("invalid terraform syntax {")

            # Mock failing terraform commands
            with patch.object(validation_service, "_run_command") as mock_run:

                def mock_command(cmd, cwd):
                    if "terraform" in cmd and "validate" in cmd:
                        return {
                            "returncode": 1,
                            "stdout": "",
                            "stderr": "Error: Invalid configuration syntax",
                        }
                    return {"returncode": 0, "stdout": "", "stderr": ""}

                mock_run.side_effect = mock_command

                result = await validation_service._run_terraform_validation(
                    temp_path, terraform_artifacts
                )

                assert result["status"] == "fail"
                assert len(result["issues"]) > 0
                assert any("validation" in issue["type"] for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_python_validation_success(
        self, validation_service, sample_artifacts
    ):
        """Test successful Python validation."""
        python_artifacts = [a for a in sample_artifacts if a["kind"] == "application"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid Python files
            src_dir = temp_path / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("""
import os
from datetime import datetime


def main():
    print("Hello MLOps")


if __name__ == "__main__":
    main()
            """)

            # Mock successful ruff commands
            with patch.object(validation_service, "_run_command") as mock_run:
                mock_run.return_value = {"returncode": 0, "stdout": "", "stderr": ""}

                result = await validation_service._run_python_validation(
                    temp_path, python_artifacts
                )

                assert result["status"] == "pass"
                assert len(result["issues"]) == 0

    @pytest.mark.asyncio
    async def test_python_validation_lint_errors(
        self, validation_service, sample_artifacts
    ):
        """Test Python validation with linting errors."""
        python_artifacts = [a for a in sample_artifacts if a["kind"] == "application"]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create Python file with issues
            src_dir = temp_path / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("import os\nimport sys  # unused import\n")

            # Mock ruff returning lint errors
            with patch.object(validation_service, "_run_command") as mock_run:

                def mock_command(cmd, cwd):
                    if "ruff" in cmd and "check" in cmd:
                        return {
                            "returncode": 1,
                            "stdout": '[{"message": "Unused import", "code": "F401", "filename": "src/main.py", "location": {"row": 2}}]',
                            "stderr": "",
                        }
                    return {"returncode": 0, "stdout": "", "stderr": ""}

                mock_run.side_effect = mock_command

                result = await validation_service._run_python_validation(
                    temp_path, python_artifacts
                )

                assert result["status"] == "warning"  # F401 is a warning
                assert len(result["issues"]) > 0
                assert any("lint" in issue["type"] for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_security_validation_secrets_found(
        self, validation_service, sample_artifacts
    ):
        """Test security validation finding secrets."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create file with potential secret
            src_dir = temp_path / "src"
            src_dir.mkdir()
            (src_dir / "config.py").write_text("""
# This file contains secrets (for testing)
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"
            """)

            result = await validation_service._run_security_validation(
                temp_path, sample_artifacts
            )

            assert result["status"] == "fail"
            assert result["secrets_found"] >= 2  # At least 2 secrets found
            assert len(result["issues"]) >= 2
            assert any("secret" in issue["type"] for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_security_validation_no_secrets(
        self, validation_service, sample_artifacts
    ):
        """Test security validation with no secrets found."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create clean files
            await self._create_valid_test_files(temp_path, sample_artifacts)

            result = await validation_service._run_security_validation(
                temp_path, sample_artifacts
            )

            assert result["status"] in ["pass", "warning"]  # May have other warnings
            assert result["secrets_found"] == 0

    @pytest.mark.asyncio
    async def test_general_validation_missing_files(
        self, validation_service, sample_artifacts
    ):
        """Test general validation with missing required files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create some files but not all required ones
            src_dir = temp_path / "src"
            src_dir.mkdir()
            (src_dir / "main.py").write_text("print('hello')")
            # Note: README.md and terraform/main.tf are missing

            result = await validation_service._run_general_validation(
                temp_path, sample_artifacts
            )

            assert result["status"] == "warning"
            assert len(result["issues"]) >= 1
            assert any("missing_file" in issue["type"] for issue in result["issues"])

    @pytest.mark.asyncio
    async def test_general_validation_large_files(self, validation_service):
        """Test general validation with large files."""
        large_artifacts = [
            {
                "path": "large_file.py",
                "kind": "application",
                "size_bytes": 2 * 1024 * 1024,  # 2MB - larger than 1MB limit
                "created_at": "2025-01-01T00:00:00Z",
            }
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            result = await validation_service._run_general_validation(
                temp_path, large_artifacts
            )

            assert result["status"] == "warning"
            assert any("large_file" in issue["type"] for issue in result["issues"])

    def test_determine_overall_status(self, validation_service):
        """Test overall status determination logic."""
        # Test error status (highest priority)
        results_with_error = {
            "terraform_validate": {"status": "pass"},
            "ruff_check": {"status": "error"},
            "security_scan": {"status": "warning"},
        }
        assert (
            validation_service._determine_overall_status(results_with_error) == "error"
        )

        # Test fail status
        results_with_fail = {
            "terraform_validate": {"status": "pass"},
            "ruff_check": {"status": "fail"},
            "security_scan": {"status": "warning"},
        }
        assert validation_service._determine_overall_status(results_with_fail) == "fail"

        # Test warning status
        results_with_warning = {
            "terraform_validate": {"status": "pass"},
            "ruff_check": {"status": "pass"},
            "security_scan": {"status": "warning"},
        }
        assert (
            validation_service._determine_overall_status(results_with_warning)
            == "warning"
        )

        # Test pass status
        results_all_pass = {
            "terraform_validate": {"status": "pass"},
            "ruff_check": {"status": "pass"},
            "security_scan": {"status": "pass"},
        }
        assert validation_service._determine_overall_status(results_all_pass) == "pass"

    @pytest.mark.asyncio
    async def test_run_command_success(self, validation_service):
        """Test successful command execution."""
        result = await validation_service._run_command(["echo", "test"], ".")

        assert result["returncode"] == 0
        assert "test" in result["stdout"]
        assert result["stderr"] == ""

    @pytest.mark.asyncio
    async def test_run_command_failure(self, validation_service):
        """Test command execution failure."""
        result = await validation_service._run_command(["false"], ".")

        assert result["returncode"] == 1
        assert result["stdout"] == ""

    async def _create_valid_test_files(self, temp_path: Path, artifacts):
        """Helper to create valid test files."""
        # Create README.md (required file)
        (temp_path / "README.md").write_text(
            "# MLOps Project\n\nGenerated by Agentic MLOps Platform"
        )

        # Create terraform files
        terraform_dir = temp_path / "terraform"
        terraform_dir.mkdir(exist_ok=True)
        (terraform_dir / "main.tf").write_text("""
resource "aws_instance" "example" {
  ami           = "ami-12345678"
  instance_type = "t2.micro"
}
        """)

        # Create Python files
        src_dir = temp_path / "src"
        src_dir.mkdir(exist_ok=True)
        (src_dir / "main.py").write_text("""
import os


def main():
    print("Hello MLOps")


if __name__ == "__main__":
    main()
        """)

        # Create CI files
        github_dir = temp_path / ".github" / "workflows"
        github_dir.mkdir(parents=True, exist_ok=True)
        (github_dir / "ci.yml").write_text("""
name: CI
on: [push]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
        """)


class TestValidationServiceIntegration:
    """Integration tests for ValidationService."""

    @pytest.mark.asyncio
    async def test_end_to_end_validation(self):
        """Test end-to-end validation workflow."""
        validation_service = ValidationService()

        artifacts = [
            {
                "path": "README.md",
                "kind": "documentation",
                "size_bytes": 100,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "path": "terraform/main.tf",
                "kind": "infrastructure",
                "size_bytes": 200,
                "created_at": "2025-01-01T00:00:00Z",
            },
            {
                "path": "src/app.py",
                "kind": "application",
                "size_bytes": 150,
                "created_at": "2025-01-01T00:00:00Z",
            },
        ]

        with tempfile.TemporaryDirectory() as temp_dir:
            temp_path = Path(temp_dir)

            # Create valid files
            (temp_path / "README.md").write_text("# Test Project")

            terraform_dir = temp_path / "terraform"
            terraform_dir.mkdir()
            (terraform_dir / "main.tf").write_text("""
resource "aws_instance" "test" {
  ami = "ami-12345678"
}
            """)

            src_dir = temp_path / "src"
            src_dir.mkdir()
            (src_dir / "app.py").write_text("print('hello world')")

            # Mock external commands for CI environment
            with patch.object(validation_service, "_run_command") as mock_run:
                # Mock terraform commands to pass
                def mock_command(cmd, cwd):
                    if "terraform" in cmd:
                        if "init" in cmd:
                            return {
                                "returncode": 0,
                                "stdout": "Terraform initialized",
                                "stderr": "",
                            }
                        elif "validate" in cmd:
                            return {"returncode": 0, "stdout": "Success", "stderr": ""}
                        elif "fmt" in cmd:
                            return {"returncode": 0, "stdout": "", "stderr": ""}
                    elif "ruff" in cmd:
                        return {"returncode": 0, "stdout": "", "stderr": ""}
                    return {"returncode": 0, "stdout": "", "stderr": ""}

                mock_run.side_effect = mock_command

                result = await validation_service.validate_artifacts(
                    temp_path, artifacts
                )

                # Should pass all validations
                assert result["overall_status"] == "pass"
                assert result["artifacts_validated"] == len(artifacts)
                assert "validation_timestamp" in result

                # Check individual validation results
                assert result["terraform_validate"]["status"] == "pass"
                assert result["ruff_check"]["status"] == "pass"
                assert result["security_scan"]["status"] == "pass"
                assert result["general_checks"]["status"] == "pass"
