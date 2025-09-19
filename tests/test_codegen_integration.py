import asyncio
import os

import pytest

claude_sdk = pytest.importorskip("claude_code_sdk", reason="Claude Code SDK is not installed")

ANTHROPIC_KEY = os.getenv("ANTHROPIC_API_KEY")
if not ANTHROPIC_KEY:
    pytest.skip("ANTHROPIC_API_KEY is not set", allow_module_level=True)


from libs.codegen_service import CodegenService  # noqa: E402  (after skip checks)


@pytest.mark.integration
def test_claude_code_sdk_generates_artifacts(monkeypatch):
    """Verify the Claude Code SDK path produces artifacts without fallback."""

    # Ensure we give the SDK enough time and do not attempt S3 uploads
    monkeypatch.setenv("CLAUDE_CODE_TIMEOUT_SECONDS", os.getenv("CLAUDE_CODE_TIMEOUT_SECONDS", "180"))
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)

    fallback_called = False

    async def fail_fallback(self, plan, output_dir):
        nonlocal fallback_called
        fallback_called = True
        return []

    monkeypatch.setattr(CodegenService, "_fallback_template_generation", fail_fallback)

    plan = {
        "pattern_name": "simple-test",
        "architecture_type": "minimal",
        "key_services": {
            "api": "Simple web service",
        },
        "implementation_phases": ["scaffold"],
        "estimated_monthly_cost": 50,
    }

    service = CodegenService()
    result = asyncio.run(service.generate_mlops_repository(plan))

    assert not fallback_called, "Expected Claude SDK path to complete without fallback"
    artifacts = result.get("artifacts", [])
    assert artifacts, "Claude SDK should return at least one generated artifact"
    assert result.get("repository_zip", {}).get("size_bytes", 0) > 0, "Repository ZIP should be created"
