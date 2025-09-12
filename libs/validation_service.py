"""
Validation Service for static code analysis and security checks.

This module implements validation checks for generated MLOps code including
Terraform validation, Python linting, and security scanning.
"""

import asyncio
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating generated code artifacts."""
    
    def __init__(self):
        pass
    
    async def validate_artifacts(self, artifacts_dir: Path, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Run comprehensive validation checks on generated artifacts.
        
        Args:
            artifacts_dir: Path to directory containing artifacts
            artifacts: List of artifact metadata
            
        Returns:
            Dict containing validation results and reports
        """
        logger.info(f"Starting validation of {len(artifacts)} artifacts")
        
        validation_results = {
            "terraform_validate": await self._run_terraform_validation(artifacts_dir, artifacts),
            "ruff_check": await self._run_python_validation(artifacts_dir, artifacts),
            "security_scan": await self._run_security_validation(artifacts_dir, artifacts),
            "general_checks": await self._run_general_validation(artifacts_dir, artifacts),
            "overall_status": "unknown",
            "artifacts_validated": len(artifacts),
            "validation_timestamp": datetime.now(timezone.utc).isoformat(),
        }
        
        # Determine overall status
        validation_results["overall_status"] = self._determine_overall_status(validation_results)
        
        # Generate validation report
        await self._generate_validation_report(artifacts_dir, validation_results)
        
        logger.info(f"Validation completed with status: {validation_results['overall_status']}")
        return validation_results
    
    async def _run_terraform_validation(self, artifacts_dir: Path, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate Terraform files."""
        terraform_files = [a for a in artifacts if a.get("kind") == "infrastructure"]
        
        if not terraform_files:
            return {"status": "skipped", "reason": "No Terraform files found", "issues": []}
        
        logger.info(f"Validating {len(terraform_files)} Terraform files")
        
        try:
            terraform_dir = artifacts_dir / "terraform"
            if not terraform_dir.exists():
                return {"status": "skipped", "reason": "Terraform directory not found", "issues": []}
            
            issues = []
            
            # Check Terraform format
            format_result = await self._run_command(["terraform", "fmt", "-check", "-diff"], str(terraform_dir))
            if format_result["returncode"] != 0:
                issues.append({
                    "type": "format",
                    "severity": "warning",
                    "message": "Terraform files are not properly formatted",
                    "details": format_result["stdout"]
                })
            
            # Run Terraform init
            init_result = await self._run_command(["terraform", "init", "-backend=false"], str(terraform_dir))
            if init_result["returncode"] != 0:
                return {
                    "status": "fail",
                    "issues": [{
                        "type": "init",
                        "severity": "error",
                        "message": "Terraform init failed",
                        "details": init_result["stderr"]
                    }]
                }
            
            # Run Terraform validate
            validate_result = await self._run_command(["terraform", "validate"], str(terraform_dir))
            if validate_result["returncode"] != 0:
                issues.append({
                    "type": "validation",
                    "severity": "error",
                    "message": "Terraform validation failed",
                    "details": validate_result["stderr"]
                })
            
            status = "fail" if any(i["severity"] == "error" for i in issues) else ("warning" if issues else "pass")
            return {"status": status, "issues": issues}
            
        except Exception as e:
            logger.exception("Terraform validation failed")
            return {
                "status": "error",
                "issues": [{
                    "type": "exception",
                    "severity": "error",
                    "message": f"Terraform validation error: {str(e)}"
                }]
            }
    
    async def _run_python_validation(self, artifacts_dir: Path, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Validate Python files using ruff."""
        python_files = [a for a in artifacts if a.get("kind") == "application" and a.get("path", "").endswith(".py")]
        
        if not python_files:
            return {"status": "skipped", "reason": "No Python files found", "issues": []}
        
        logger.info(f"Validating {len(python_files)} Python files")
        
        try:
            issues = []
            
            # Run ruff check
            check_result = await self._run_command(["ruff", "check", "--output-format=json", "."], str(artifacts_dir))
            
            if check_result["returncode"] != 0:
                try:
                    ruff_issues = json.loads(check_result["stdout"])
                    for issue in ruff_issues:
                        # Determine severity based on ruff error codes
                        code = issue.get("code", "")
                        # F401 (unused import), F841 (unused variable), W (warnings) are warnings
                        # E (errors), other F codes are errors
                        is_warning = (code in ["F401", "F841"] or 
                                     code.startswith("W") or
                                     code.startswith("N") or  # pycodestyle naming
                                     code.startswith("D"))    # pydocstyle
                        
                        issues.append({
                            "type": "lint",
                            "severity": "warning" if is_warning else "error",
                            "message": issue.get("message", "Unknown issue"),
                            "file": issue.get("filename", "unknown"),
                            "line": issue.get("location", {}).get("row", 0),
                            "code": issue.get("code", "unknown")
                        })
                except json.JSONDecodeError:
                    issues.append({
                        "type": "lint",
                        "severity": "error",
                        "message": "Failed to parse ruff output",
                        "details": check_result["stdout"]
                    })
            
            # Run ruff format check
            format_result = await self._run_command(["ruff", "format", "--check", "."], str(artifacts_dir))
            if format_result["returncode"] != 0:
                issues.append({
                    "type": "format",
                    "severity": "warning",
                    "message": "Python files are not properly formatted",
                    "details": format_result["stdout"]
                })
            
            status = "fail" if any(i["severity"] == "error" for i in issues) else ("warning" if issues else "pass")
            return {"status": status, "issues": issues}
            
        except Exception as e:
            logger.exception("Python validation failed")
            return {
                "status": "error",
                "issues": [{
                    "type": "exception",
                    "severity": "error",
                    "message": f"Python validation error: {str(e)}"
                }]
            }
    
    async def _run_security_validation(self, artifacts_dir: Path, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run security validation checks."""
        logger.info("Running security validation")
        
        try:
            issues = []
            secrets_found = 0
            
            # Check for common secrets patterns
            secret_patterns = [
                (r'aws_access_key_id\s*=\s*["\']?AKIA[A-Z0-9]{16}["\']?', "AWS Access Key"),
                (r'aws_secret_access_key\s*=\s*["\']?[A-Za-z0-9/+=]{40}["\']?', "AWS Secret Key"),
                (r'["\']sk-[A-Za-z0-9]{32,}["\']', "OpenAI API Key"),
                (r'["\']ghp_[A-Za-z0-9]{36}["\']', "GitHub Token"),
                (r'["\'][A-Za-z0-9]{32}["\']', "Generic Secret (32 chars)"),
            ]
            
            for file_path in artifacts_dir.rglob("*"):
                if file_path.is_file() and not file_path.name.startswith("."):
                    try:
                        content = file_path.read_text(encoding='utf-8', errors='ignore')
                        
                        for pattern, secret_type in secret_patterns:
                            matches = re.findall(pattern, content, re.IGNORECASE)
                            if matches:
                                secrets_found += len(matches)
                                issues.append({
                                    "type": "secret",
                                    "severity": "critical",
                                    "message": f"Potential {secret_type} found",
                                    "file": str(file_path.relative_to(artifacts_dir)),
                                    "pattern": pattern
                                })
                    
                    except Exception as e:
                        logger.warning(f"Could not scan file {file_path}: {e}")
            
            # Check for hardcoded IPs and URLs
            for file_path in artifacts_dir.rglob("*.py"):
                if file_path.is_file():
                    try:
                        content = file_path.read_text()
                        
                        # Check for hardcoded IPs (but allow common ones)
                        ip_pattern = r'\b(?:[0-9]{1,3}\.){3}[0-9]{1,3}\b'
                        ips = re.findall(ip_pattern, content)
                        for ip in ips:
                            if not ip.startswith(('127.', '0.0.0.0', '255.255.255.255')):
                                issues.append({
                                    "type": "hardcoded_ip",
                                    "severity": "warning",
                                    "message": f"Hardcoded IP address found: {ip}",
                                    "file": str(file_path.relative_to(artifacts_dir))
                                })
                    
                    except Exception as e:
                        logger.warning(f"Could not scan Python file {file_path}: {e}")
            
            status = "fail" if secrets_found > 0 or any(i["severity"] == "critical" for i in issues) else ("warning" if issues else "pass")
            
            return {
                "status": status,
                "secrets_found": secrets_found,
                "issues": issues
            }
            
        except Exception as e:
            logger.exception("Security validation failed")
            return {
                "status": "error",
                "secrets_found": 0,
                "issues": [{
                    "type": "exception",
                    "severity": "error",
                    "message": f"Security validation error: {str(e)}"
                }]
            }
    
    async def _run_general_validation(self, artifacts_dir: Path, artifacts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Run general validation checks."""
        logger.info("Running general validation checks")
        
        try:
            issues = []
            
            # Check for required files
            required_files = ["README.md", "terraform/main.tf"]
            for required_file in required_files:
                file_path = artifacts_dir / required_file
                if not file_path.exists():
                    issues.append({
                        "type": "missing_file",
                        "severity": "warning",
                        "message": f"Required file missing: {required_file}"
                    })
            
            # Check file sizes (warn if any file is too large)
            max_size = 1024 * 1024  # 1MB
            for artifact in artifacts:
                if artifact.get("size_bytes", 0) > max_size:
                    issues.append({
                        "type": "large_file",
                        "severity": "warning",
                        "message": f"Large file detected: {artifact.get('path')} ({artifact.get('size_bytes')} bytes)"
                    })
            
            # Check for empty files
            for file_path in artifacts_dir.rglob("*"):
                if file_path.is_file() and file_path.stat().st_size == 0:
                    issues.append({
                        "type": "empty_file",
                        "severity": "warning",
                        "message": f"Empty file: {file_path.relative_to(artifacts_dir)}"
                    })
            
            status = "warning" if issues else "pass"
            return {"status": status, "issues": issues}
            
        except Exception as e:
            logger.exception("General validation failed")
            return {
                "status": "error",
                "issues": [{
                    "type": "exception",
                    "severity": "error",
                    "message": f"General validation error: {str(e)}"
                }]
            }
    
    async def _run_command(self, cmd: List[str], cwd: str) -> Dict[str, Any]:
        """Run a shell command asynchronously."""
        try:
            process = await asyncio.create_subprocess_exec(
                *cmd,
                cwd=cwd,
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.PIPE
            )
            
            stdout, stderr = await process.communicate()
            
            return {
                "returncode": process.returncode,
                "stdout": stdout.decode('utf-8', errors='ignore'),
                "stderr": stderr.decode('utf-8', errors='ignore')
            }
            
        except Exception as e:
            logger.exception(f"Command failed: {' '.join(cmd)}")
            return {
                "returncode": -1,
                "stdout": "",
                "stderr": str(e)
            }
    
    def _determine_overall_status(self, results: Dict[str, Any]) -> str:
        """Determine overall validation status."""
        statuses = []
        
        for key, value in results.items():
            if isinstance(value, dict) and "status" in value:
                status = value["status"]
                if status == "error":
                    return "error"
                elif status == "fail":
                    return "fail"
                statuses.append(status)
        
        if "fail" in statuses:
            return "fail"
        elif "warning" in statuses:
            return "warning"
        elif "pass" in statuses:
            return "pass"
        else:
            return "unknown"
    
    async def _generate_validation_report(self, artifacts_dir: Path, results: Dict[str, Any]) -> None:
        """Generate a comprehensive validation report."""
        reports_dir = artifacts_dir / "reports"
        reports_dir.mkdir(exist_ok=True)
        
        report_file = reports_dir / "validation_report.json"
        
        try:
            with open(report_file, 'w') as f:
                json.dump(results, f, indent=2)
            
            # Also generate a human-readable report
            text_report = reports_dir / "validation_report.md"
            with open(text_report, 'w') as f:
                f.write(self._format_validation_report(results))
            
            logger.info(f"Validation reports generated in {reports_dir}")
            
        except Exception:
            logger.exception("Failed to generate validation report")
    
    def _format_validation_report(self, results: Dict[str, Any]) -> str:
        """Format validation results as markdown report."""
        report = f"""# Code Validation Report

**Overall Status:** {results.get('overall_status', 'unknown').upper()}
**Artifacts Validated:** {results.get('artifacts_validated', 0)}
**Generated:** {results.get('validation_timestamp', 'unknown')}

## Validation Results

"""
        
        sections = {
            "terraform_validate": "Terraform Validation",
            "ruff_check": "Python Code Quality",
            "security_scan": "Security Scan",
            "general_checks": "General Checks"
        }
        
        for key, title in sections.items():
            if key in results:
                section_result = results[key]
                status = section_result.get('status', 'unknown')
                
                report += f"### {title}\n"
                report += f"**Status:** {status.upper()}\n\n"
                
                issues = section_result.get('issues', [])
                if issues:
                    report += "**Issues Found:**\n"
                    for issue in issues:
                        severity = issue.get('severity', 'unknown')
                        message = issue.get('message', 'Unknown issue')
                        report += f"- [{severity.upper()}] {message}\n"
                else:
                    report += "No issues found.\n"
                
                report += "\n"
        
        return report


class ValidationError(Exception):
    """Custom exception for validation errors."""
    pass