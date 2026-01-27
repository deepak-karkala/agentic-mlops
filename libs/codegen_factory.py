"""
Code Generation Service Factory

Factory module to create the appropriate code generation service based on
configuration. Supports both Claude Code SDK and OpenAI implementations.
"""

import logging
import os
from typing import Union

logger = logging.getLogger(__name__)


def get_codegen_service() -> Union["CodegenService", "OpenAICodegenService"]:
    """
    Get the appropriate code generation service based on configuration.

    Returns the service implementation based on CODEGEN_PROVIDER environment variable:
    - "claude": Use Claude Code SDK (requires ANTHROPIC_API_KEY)
    - "openai": Use OpenAI API (requires OPENAI_API_KEY)
    - Not set: Auto-detect based on available API keys

    Returns:
        CodegenService or OpenAICodegenService instance

    Raises:
        ValueError: If no valid provider is configured or API keys are missing
    """
    provider = os.getenv("CODEGEN_PROVIDER", "auto").lower()

    # Auto-detect provider based on available API keys
    if provider == "auto":
        has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
        has_openai = bool(os.getenv("OPENAI_API_KEY"))

        if has_anthropic:
            provider = "claude"
            logger.info("Auto-detected Claude Code SDK (ANTHROPIC_API_KEY found)")
        elif has_openai:
            provider = "openai"
            logger.info("Auto-detected OpenAI API (OPENAI_API_KEY found)")
        else:
            raise ValueError(
                "No API keys found. Set ANTHROPIC_API_KEY or OPENAI_API_KEY"
            )

    # Create appropriate service
    if provider == "claude":
        anthropic_key = os.getenv("ANTHROPIC_API_KEY")
        if not anthropic_key:
            raise ValueError(
                "CODEGEN_PROVIDER=claude but ANTHROPIC_API_KEY not set. "
                "Either set the API key or use CODEGEN_PROVIDER=openai"
            )

        try:
            from libs.codegen_service import CodegenService

            logger.info("Using Claude Code SDK for code generation")
            return CodegenService()
        except ImportError as e:
            logger.warning(f"Failed to import Claude Code SDK: {e}")
            raise ValueError(
                "Claude Code SDK not available. Install with: uv add claude-code-sdk"
            )

    elif provider == "openai":
        openai_key = os.getenv("OPENAI_API_KEY")
        if not openai_key:
            raise ValueError(
                "CODEGEN_PROVIDER=openai but OPENAI_API_KEY not set. "
                "Either set the API key or use CODEGEN_PROVIDER=claude"
            )

        from libs.codegen_service_openai import OpenAICodegenService

        logger.info("Using OpenAI API for code generation")
        return OpenAICodegenService()

    else:
        raise ValueError(
            f"Invalid CODEGEN_PROVIDER: {provider}. Must be 'claude', 'openai', or 'auto'"
        )


def get_provider_info() -> dict:
    """
    Get information about the current code generation provider.

    Returns:
        Dict with provider name, availability, and configuration status
    """
    provider = os.getenv("CODEGEN_PROVIDER", "auto")
    has_anthropic = bool(os.getenv("ANTHROPIC_API_KEY"))
    has_openai = bool(os.getenv("OPENAI_API_KEY"))

    # Determine active provider
    active_provider = provider
    if provider == "auto":
        active_provider = "claude" if has_anthropic else "openai" if has_openai else None

    return {
        "configured_provider": provider,
        "active_provider": active_provider,
        "claude_available": has_anthropic,
        "openai_available": has_openai,
        "auto_detection": provider == "auto",
    }
