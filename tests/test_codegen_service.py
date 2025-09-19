import asyncio
import pytest

# Provide a stub Claude SDK so CodegenService can import without the real package
import sys
import types
from dataclasses import dataclass

_sdk_stub = types.ModuleType("claude_code_sdk")


class _StubClaudeCodeOptions:
    def __init__(self, *args, **kwargs):
        self.kwargs = kwargs


class _StubClaudeSDKClient:
    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query(self, prompt: str):
        return None

    async def receive_response(self):  # pragma: no cover - never used directly
        if False:
            yield None


_sdk_stub.ClaudeCodeOptions = _StubClaudeCodeOptions
_sdk_stub.ClaudeSDKClient = _StubClaudeSDKClient
sys.modules.setdefault("claude_code_sdk", _sdk_stub)

from libs.codegen_service import CodegenService


@dataclass
class _MockMessage:
    type: str
    file_info: dict


class _MockClaudeClient:
    def __init__(self, *args, **kwargs):
        self.query_called = False

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc, tb):
        return False

    async def query(self, prompt: str):
        self.query_called = True

    async def receive_response(self):
        yield _MockMessage(
            type="file_created",
            file_info={"path": "src/main.py", "size": 256},
        )


def test_claude_codegen_stream_success(monkeypatch):
    """Ensure Claude Code SDK streaming completes without falling back."""

    # Avoid S3 uploads during test
    monkeypatch.delenv("S3_BUCKET_NAME", raising=False)
    monkeypatch.setenv("CLAUDE_CODE_TIMEOUT_SECONDS", "5")

    # Patch Claude SDK client with mock implementation
    monkeypatch.setattr(
        "libs.codegen_service.ClaudeSDKClient", _MockClaudeClient
    )

    # Fail fast if fallback is unexpectedly invoked
    async def _fail_fallback(self, plan, output_dir):  # pragma: no cover - guard
        raise AssertionError("Fallback generation should not run when Claude succeeds")

    monkeypatch.setattr(
        CodegenService,
        "_fallback_template_generation",
        _fail_fallback,
    )

    plan = {
        "pattern_name": "test-pattern",
        "architecture_type": "app_runner",
        "key_services": {"api": "FastAPI service"},
        "implementation_phases": ["scaffold", "deploy"],
        "estimated_monthly_cost": 100,
    }

    service = CodegenService()
    result = asyncio.run(service.generate_mlops_repository(plan))

    assert result["artifacts"], "Expected artifacts to be returned from Claude stream"
    assert any(
        artifact["path"] == "src/main.py" for artifact in result["artifacts"]
    ), "Claude artifacts should include generated file"
    assert result["repository_zip"].get("size_bytes", 0) >= 0
