"""
OpenAI LLM Client

Robust OpenAI API integration for the agentic MLOps system.
Provides structured output parsing, retry logic, and cost management.
"""

from __future__ import annotations

import json
import os
from typing import Any, Dict, List, Optional, Type, TypeVar, Union, AsyncGenerator
from dataclasses import dataclass
from datetime import datetime, timezone
import logging

import openai
from openai import AsyncOpenAI
from pydantic import BaseModel, ValidationError
import backoff

# Configure logging
logger = logging.getLogger(__name__)

# Type variable for structured responses
T = TypeVar("T", bound=BaseModel)


@dataclass
class LLMUsageMetrics:
    """Track LLM API usage for cost management."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0
    estimated_cost_usd: float = 0.0
    model: str = ""
    timestamp: str = ""


class LLMClientError(Exception):
    """Base exception for LLM client errors."""

    pass


class LLMValidationError(LLMClientError):
    """Exception for structured output validation failures."""

    pass


class LLMRateLimitError(LLMClientError):
    """Exception for rate limiting issues."""

    pass


class OpenAIClient:
    """
    Robust OpenAI API client with structured output support.

    Features:
    - Automatic retry with exponential backoff
    - Structured output parsing with Pydantic validation
    - Token usage tracking and cost estimation
    - Multiple model support with fallback
    - Rate limiting and error handling
    """

    # Model pricing per 1M tokens (approximate, update regularly)
    MODEL_PRICING = {
        "gpt-5": {"input": 1.25, "output": 10.0},
        "gpt-5-mini": {"input": 0.25, "output": 2.0},
        "gpt-5-nano": {"input": 0.05, "output": 0.4},
    }

    def __init__(
        self,
        api_key: Optional[str] = None,
        default_model: str = "gpt-5-nano",
        fallback_model: str = "gpt-5-nano",
        max_retries: int = 3,
        timeout: float = 60.0,
    ):
        """
        Initialize OpenAI client.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            default_model: Primary model to use
            fallback_model: Fallback model if primary fails
            max_retries: Maximum retry attempts
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise LLMClientError("OpenAI API key not provided")

        self.default_model = default_model
        self.fallback_model = fallback_model
        self.max_retries = max_retries
        self.timeout = timeout

        # Initialize async client
        self.client = AsyncOpenAI(api_key=self.api_key, timeout=timeout)

        # Usage tracking
        self.usage_history: List[LLMUsageMetrics] = []

    async def complete(
        self,
        messages: List[Dict[str, str]],
        response_format: Optional[Type[T]] = None,
        model: Optional[str] = None,
        max_tokens: Optional[int] = None,
        stream: bool = False,
    ) -> Union[str, T, AsyncGenerator]:
        """
        Complete a chat conversation with structured output support.

        Args:
            messages: List of messages in OpenAI format
            response_format: Pydantic model for structured output
            model: Model to use (defaults to default_model)
            max_tokens: Maximum tokens in response
            stream: Whether to stream the response

        Returns:
            Raw string response, parsed Pydantic object, or async generator if streaming
        """
        model = model or self.default_model

        try:
            if response_format:
                return await self._complete_structured(
                    messages, response_format, model, max_tokens
                )
            elif stream:
                return await self._complete_streaming(
                    messages, model, max_tokens
                )
            else:
                return await self._complete_basic(
                    messages, model, max_tokens
                )

        except (LLMRateLimitError, LLMValidationError) as e:
            # Don't use fallback for rate limits or validation errors
            raise e
        except Exception as e:
            logger.error(f"LLM completion failed: {str(e)}")

            # Try fallback model if primary model failed
            if model != self.fallback_model:
                logger.info(f"Retrying with fallback model: {self.fallback_model}")
                return await self.complete(
                    messages,
                    response_format,
                    self.fallback_model,
                    max_tokens,
                    stream,
                )

            raise LLMClientError(f"LLM completion failed: {str(e)}")

    @backoff.on_exception(
        backoff.expo,
        (openai.RateLimitError, openai.APITimeoutError, openai.APIConnectionError),
        max_tries=3,
        base=2,
        max_value=60,
    )
    async def _complete_basic(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int],
    ) -> str:
        """Basic completion without structured output."""
        try:
            # Build parameters, excluding None values
            params = {
                "model": model,
                "messages": messages,
            }
            self._add_max_tokens_param(params, model, max_tokens)

            response = await self.client.chat.completions.create(**params)

            # Track usage
            usage = response.usage
            self._track_usage(usage, model)

            return response.choices[0].message.content

        except openai.RateLimitError as e:
            raise LLMRateLimitError(f"Rate limit exceeded: {str(e)}")
        except (openai.APITimeoutError, openai.APIConnectionError) as e:
            raise LLMClientError(f"API connection error: {str(e)}")

    async def _complete_structured(
        self,
        messages: List[Dict[str, str]],
        response_format: Type[T],
        model: str,
        max_tokens: Optional[int],
    ) -> T:
        """
        Completion with structured output parsing.

        Automatically adds JSON schema instructions and validates response.
        """
        # Add structured output instructions
        schema_prompt = self._build_schema_prompt(response_format)
        enhanced_messages = messages.copy()

        # Add schema instructions to system message or create new one
        if enhanced_messages and enhanced_messages[0]["role"] == "system":
            enhanced_messages[0]["content"] += f"\n\n{schema_prompt}"
        else:
            enhanced_messages.insert(0, {"role": "system", "content": schema_prompt})

        # Attempt structured completion with retries
        for attempt in range(self.max_retries):
            try:
                raw_response = await self._complete_basic(
                    enhanced_messages, model, max_tokens
                )

                # Parse and validate structured response
                return self._parse_structured_response(raw_response, response_format)

            except (LLMValidationError, json.JSONDecodeError) as e:
                logger.warning(
                    f"Structured parsing failed (attempt {attempt + 1}): {str(e)}"
                )

                if attempt == self.max_retries - 1:
                    raise LLMValidationError(
                        f"Failed to parse structured response after {self.max_retries} attempts: {str(e)}"
                    )

                # Add correction instruction for retry
                enhanced_messages.append(
                    {
                        "role": "user",
                        "content": f"The previous response had invalid JSON format. Please provide a valid JSON response matching the required schema. Error: {str(e)}",
                    }
                )

        raise LLMValidationError("Max retries exceeded for structured output")

    async def _complete_streaming(
        self,
        messages: List[Dict[str, str]],
        model: str,
        max_tokens: Optional[int],
    ):
        """Streaming completion generator."""
        try:
            # Build parameters, excluding None values
            params = {
                "model": model,
                "messages": messages,
                "stream": True,
            }
            self._add_max_tokens_param(params, model, max_tokens)

            stream = await self.client.chat.completions.create(**params)

            async for chunk in stream:
                if chunk.choices[0].delta.content is not None:
                    yield chunk.choices[0].delta.content

        except Exception as e:
            raise LLMClientError(f"Streaming completion failed: {str(e)}")

    def _build_schema_prompt(self, response_format: Type[BaseModel]) -> str:
        """Build JSON schema prompt for structured output."""
        schema = response_format.model_json_schema()

        return f"""
IMPORTANT: You must respond with valid JSON that exactly matches this schema.
Do not include any text before or after the JSON response.

Required JSON Schema:
{json.dumps(schema, indent=2)}

Example response format:
{json.dumps(self._generate_example_response(response_format), indent=2)}
"""

    def _generate_example_response(
        self, response_format: Type[BaseModel]
    ) -> Dict[str, Any]:
        """Generate example response for the schema."""
        try:
            # Try to create an example instance
            example = response_format.model_validate({})
            return example.model_dump()
        except ValidationError:
            # If validation fails, return schema structure
            schema = response_format.model_json_schema()
            return {prop: "example_value" for prop in schema.get("properties", {})}

    def _parse_structured_response(
        self, raw_response: str, response_format: Type[T]
    ) -> T:
        """Parse and validate structured JSON response."""
        try:
            # Clean response (remove markdown code blocks if present)
            cleaned_response = raw_response.strip()
            if cleaned_response.startswith("```json"):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith("```"):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()

            # Parse JSON
            parsed_data = json.loads(cleaned_response)

            # Validate with Pydantic
            validated_response = response_format.model_validate(parsed_data)
            return validated_response

        except json.JSONDecodeError as e:
            raise LLMValidationError(f"Invalid JSON in response: {str(e)}")
        except ValidationError as e:
            raise LLMValidationError(f"Response validation failed: {str(e)}")

    def _track_usage(self, usage: Any, model: str):
        """Track token usage and cost."""
        if not usage:
            return

        prompt_tokens = usage.prompt_tokens or 0
        completion_tokens = usage.completion_tokens or 0
        total_tokens = usage.total_tokens or (prompt_tokens + completion_tokens)

        # Estimate cost
        pricing = self.MODEL_PRICING.get(model, {"input": 0.001, "output": 0.002})
        estimated_cost = (prompt_tokens / 1000000) * pricing["input"] + (
            completion_tokens / 1000000
        ) * pricing["output"]

        # Record usage
        usage_record = LLMUsageMetrics(
            prompt_tokens=prompt_tokens,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            estimated_cost_usd=estimated_cost,
            model=model,
            timestamp=datetime.now(timezone.utc).isoformat(),
        )

        self.usage_history.append(usage_record)

        logger.info(
            f"LLM Usage - Model: {model}, Tokens: {total_tokens}, "
            f"Estimated Cost: ${estimated_cost:.4f}"
        )

    def _add_max_tokens_param(
        self, params: Dict[str, Any], model: str, max_tokens: Optional[int]
    ) -> None:
        if max_tokens is None:
            return
        if model.startswith("gpt-5"):
            params["max_completion_tokens"] = max_tokens
        else:
            params["max_tokens"] = max_tokens

    def get_usage_summary(self, hours: int = 24) -> Dict[str, Any]:
        """Get usage summary for the last N hours."""
        cutoff = datetime.now(timezone.utc).timestamp() - (hours * 3600)

        recent_usage = [
            usage
            for usage in self.usage_history
            if datetime.fromisoformat(
                usage.timestamp.replace("Z", "+00:00")
            ).timestamp()
            > cutoff
        ]

        if not recent_usage:
            return {
                "total_tokens": 0,
                "total_cost_usd": 0.0,
                "request_count": 0,
                "models_used": [],
            }

        return {
            "total_tokens": sum(u.total_tokens for u in recent_usage),
            "total_cost_usd": sum(u.estimated_cost_usd for u in recent_usage),
            "request_count": len(recent_usage),
            "models_used": list(set(u.model for u in recent_usage)),
            "cost_by_model": {
                model: sum(
                    u.estimated_cost_usd for u in recent_usage if u.model == model
                )
                for model in set(u.model for u in recent_usage)
            },
        }

    async def validate_api_key(self) -> bool:
        """Validate API key with a simple test request."""
        try:
            response = await self.client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[{"role": "user", "content": "Hello"}],
                max_tokens=5,
            )
            return bool(response.choices[0].message.content)
        except Exception as e:
            logger.error(f"API key validation failed: {str(e)}")
            return False


# Global client instance (lazy initialization)
_client_instance: Optional[OpenAIClient] = None


def get_llm_client(
    api_key: Optional[str] = None, default_model: Optional[str] = None
) -> OpenAIClient:
    """
    Get global LLM client instance.

    Args:
        api_key: OpenAI API key (optional)
        default_model: Default model to use (optional, will read from OPENAI_MODEL env var)

    Returns:
        Configured OpenAI client instance
    """
    global _client_instance

    if _client_instance is None:
        # Use environment variable if no default_model is provided
        if default_model is None:
            default_model = os.getenv("OPENAI_MODEL")
            if not default_model:
                raise ValueError("OPENAI_MODEL environment variable must be set")

        _client_instance = OpenAIClient(api_key=api_key, default_model=default_model)

    return _client_instance


# Convenience function for quick completions
async def complete_with_llm(
    prompt: str,
    response_format: Optional[Type[T]] = None,
    model: Optional[str] = None,
) -> Union[str, T]:
    """
    Quick completion function for simple use cases.

    Args:
        prompt: User prompt
        response_format: Optional Pydantic model for structured output
        model: Model to use

    Returns:
        Raw string or parsed structured response
    """
    client = get_llm_client()

    # Use environment variable if no model is provided
    if model is None:
        model = os.getenv("OPENAI_MODEL")
        if not model:
            raise ValueError("OPENAI_MODEL environment variable must be set")

    messages = [{"role": "user", "content": prompt}]

    return await client.complete(
        messages=messages,
        response_format=response_format,
        model=model,
    )
