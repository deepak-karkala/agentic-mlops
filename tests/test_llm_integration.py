"""
Tests for LLM client integration and error handling

Validates LLM client functionality, structured output parsing,
retry logic, and error resilience.
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from pydantic import BaseModel
import openai

from libs.llm_client import (
    OpenAIClient,
    LLMClientError,
    LLMValidationError,
    LLMRateLimitError,
    LLMUsageMetrics,
    get_llm_client,
    complete_with_llm,
)


class SampleStructuredOutput(BaseModel):
    """Sample structured output for testing."""

    message: str
    confidence: float
    items: list[str]


class TestOpenAIClient:
    """Test OpenAI client functionality."""

    @pytest.fixture
    def client(self):
        """Create test client."""
        return OpenAIClient(
            api_key="test-key",
            default_model="gpt-4-turbo-preview",
            max_retries=2,
            timeout=30.0,
        )

    def test_client_initialization(self, client):
        """Test client initialization."""
        assert client.api_key == "test-key"
        assert client.default_model == "gpt-4-turbo-preview"
        assert client.max_retries == 2
        assert client.timeout == 30.0

    def test_client_initialization_with_env_key(self):
        """Test client initialization with environment API key."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-test-key"}):
            client = OpenAIClient()
            assert client.api_key == "env-test-key"

    def test_client_initialization_without_key(self):
        """Test client initialization fails without API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(LLMClientError, match="OpenAI API key not provided"):
                OpenAIClient()

    def test_model_pricing_data(self):
        """Test model pricing information is available."""
        assert "gpt-4" in OpenAIClient.MODEL_PRICING
        assert "gpt-3.5-turbo" in OpenAIClient.MODEL_PRICING

        gpt4_pricing = OpenAIClient.MODEL_PRICING["gpt-4"]
        assert "input" in gpt4_pricing
        assert "output" in gpt4_pricing
        assert gpt4_pricing["input"] > 0
        assert gpt4_pricing["output"] > 0

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_basic_completion(self, mock_openai, client):
        """Test basic text completion."""
        # Mock OpenAI response
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Test response"
        mock_response.usage = Mock(
            prompt_tokens=10, completion_tokens=5, total_tokens=15
        )

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        client.client = mock_client

        # Test completion
        messages = [{"role": "user", "content": "Hello"}]
        result = await client.complete(messages)

        assert result == "Test response"
        assert len(client.usage_history) == 1

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_structured_output_completion(self, mock_openai, client):
        """Test structured output completion."""
        # Mock successful structured response
        structured_response = SampleStructuredOutput(
            message="Test structured response",
            confidence=0.85,
            items=["item1", "item2"],
        )

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(
            structured_response.model_dump()
        )
        mock_response.usage = Mock(
            prompt_tokens=20, completion_tokens=15, total_tokens=35
        )

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        client.client = mock_client

        # Test structured completion
        messages = [{"role": "user", "content": "Generate structured data"}]
        result = await client.complete(messages, response_format=SampleStructuredOutput)

        assert isinstance(result, SampleStructuredOutput)
        assert result.message == "Test structured response"
        assert result.confidence == 0.85
        assert len(result.items) == 2

    def test_schema_prompt_building(self, client):
        """Test JSON schema prompt construction."""
        schema_prompt = client._build_schema_prompt(SampleStructuredOutput)

        assert "JSON" in schema_prompt
        assert "schema" in schema_prompt.lower()
        assert "message" in schema_prompt  # Field from schema
        assert "confidence" in schema_prompt

    def test_structured_response_parsing(self, client):
        """Test structured response parsing."""
        # Test valid JSON response
        valid_json = json.dumps(
            {"message": "Test message", "confidence": 0.9, "items": ["a", "b", "c"]}
        )

        result = client._parse_structured_response(valid_json, SampleStructuredOutput)
        assert isinstance(result, SampleStructuredOutput)
        assert result.confidence == 0.9

        # Test JSON with markdown code blocks
        markdown_json = f"```json\n{valid_json}\n```"
        result = client._parse_structured_response(
            markdown_json, SampleStructuredOutput
        )
        assert isinstance(result, SampleStructuredOutput)

    def test_structured_response_parsing_errors(self, client):
        """Test structured response parsing error handling."""
        # Invalid JSON
        with pytest.raises(LLMValidationError, match="Invalid JSON"):
            client._parse_structured_response("invalid json", SampleStructuredOutput)

        # Valid JSON, invalid schema
        invalid_schema_json = json.dumps({"wrong_field": "value"})
        with pytest.raises(LLMValidationError, match="Response validation failed"):
            client._parse_structured_response(
                invalid_schema_json, SampleStructuredOutput
            )

    def test_usage_tracking(self, client):
        """Test usage tracking functionality."""
        # Mock usage data
        mock_usage = Mock(prompt_tokens=100, completion_tokens=50, total_tokens=150)

        client._track_usage(mock_usage, "gpt-4")

        assert len(client.usage_history) == 1
        usage_record = client.usage_history[0]
        assert usage_record.prompt_tokens == 100
        assert usage_record.completion_tokens == 50
        assert usage_record.model == "gpt-4"
        assert usage_record.estimated_cost_usd > 0

    def test_usage_summary(self, client):
        """Test usage summary generation."""
        from datetime import datetime, timezone

        # Use current time for recent usage
        now = datetime.now(timezone.utc)
        recent_time1 = now.replace(microsecond=0).isoformat().replace("+00:00", "Z")
        recent_time2 = (now.replace(microsecond=0)).isoformat().replace("+00:00", "Z")

        # Add some mock usage records with recent timestamps
        usage1 = LLMUsageMetrics(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.01,
            model="gpt-4",
            timestamp=recent_time1,
        )
        usage2 = LLMUsageMetrics(
            prompt_tokens=200,
            completion_tokens=75,
            total_tokens=275,
            estimated_cost_usd=0.02,
            model="gpt-3.5-turbo",
            timestamp=recent_time2,
        )

        client.usage_history = [usage1, usage2]

        summary = client.get_usage_summary(hours=24)

        assert summary["total_tokens"] == 425
        assert summary["total_cost_usd"] == 0.03
        assert summary["request_count"] == 2
        assert len(summary["models_used"]) == 2

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_rate_limit_handling(self, mock_openai, client):
        """Test rate limit error handling."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.RateLimitError(
                message="Rate limit exceeded", response=Mock(), body={}
            )
        )
        client.client = mock_client

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMRateLimitError, match="Rate limit exceeded"):
            await client.complete(messages)

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_fallback_model(self, mock_openai, client):
        """Test fallback to secondary model on primary failure."""
        # Mock primary model failure, fallback success
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Fallback response"
        mock_response.usage = Mock(
            prompt_tokens=10, completion_tokens=5, total_tokens=15
        )

        mock_client = Mock()
        call_count = 0

        async def mock_create(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                # First call (primary model) fails
                raise Exception("Primary model failed")
            else:
                # Second call (fallback model) succeeds
                return mock_response

        mock_client.chat.completions.create = mock_create
        client.client = mock_client

        messages = [{"role": "user", "content": "Test"}]
        result = await client.complete(messages)

        assert result == "Fallback response"
        assert call_count == 2  # Primary failed, fallback succeeded

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_structured_output_retry_logic(self, mock_openai, client):
        """Test retry logic for structured output parsing failures."""
        # First call returns invalid JSON, second call succeeds
        valid_response = json.dumps(
            {
                "message": "Valid response",
                "confidence": 0.8,
                "items": ["retry", "success"],
            }
        )

        mock_responses = [
            # First response - invalid JSON
            Mock(
                choices=[Mock(message=Mock(content="invalid json"))],
                usage=Mock(prompt_tokens=10, completion_tokens=5, total_tokens=15),
            ),
            # Second response - valid JSON
            Mock(
                choices=[Mock(message=Mock(content=valid_response))],
                usage=Mock(prompt_tokens=15, completion_tokens=10, total_tokens=25),
            ),
        ]

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(side_effect=mock_responses)
        client.client = mock_client

        messages = [{"role": "user", "content": "Generate structured data"}]
        result = await client.complete(messages, response_format=SampleStructuredOutput)

        assert isinstance(result, SampleStructuredOutput)
        assert result.message == "Valid response"
        assert len(client.usage_history) == 2  # Both calls tracked

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_api_key_validation(self, mock_openai, client):
        """Test API key validation functionality."""
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "Validation successful"

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        client.client = mock_client

        is_valid = await client.validate_api_key()
        assert is_valid

        # Test validation failure
        mock_client.chat.completions.create = AsyncMock(
            side_effect=Exception("Invalid API key")
        )

        is_valid = await client.validate_api_key()
        assert not is_valid


class TestLLMClientIntegration:
    """Test LLM client integration functions."""

    def test_get_llm_client_singleton(self):
        """Test global LLM client singleton behavior."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            # Clear singleton to avoid interference from other tests
            import libs.llm_client

            libs.llm_client._client_instance = None

            client1 = get_llm_client()
            client2 = get_llm_client()

            # Should return same instance
            assert client1 is client2
            assert client1.default_model == "gpt-4-turbo-preview"

    def test_get_llm_client_with_custom_model(self):
        """Test LLM client creation with custom model."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "test-key"}):
            # Clear singleton
            import libs.llm_client

            libs.llm_client._client_instance = None

            client = get_llm_client(default_model="gpt-3.5-turbo")
            assert client.default_model == "gpt-3.5-turbo"

    @patch("libs.llm_client.get_llm_client")
    async def test_complete_with_llm_convenience_function(self, mock_get_client):
        """Test convenience completion function."""
        # Mock client and response
        mock_client = Mock()
        mock_client.complete = AsyncMock(return_value="Convenience function works")
        mock_get_client.return_value = mock_client

        result = await complete_with_llm(
            prompt="Test prompt", model="gpt-4", temperature=0.5
        )

        assert result == "Convenience function works"

        # Verify correct parameters passed
        mock_client.complete.assert_called_once_with(
            messages=[{"role": "user", "content": "Test prompt"}],
            response_format=None,
            model="gpt-4",
            temperature=0.5,
        )

    @patch("libs.llm_client.get_llm_client")
    async def test_complete_with_llm_structured_output(self, mock_get_client):
        """Test convenience function with structured output."""
        # Mock structured response
        structured_result = SampleStructuredOutput(
            message="Structured convenience response", confidence=0.9, items=["test"]
        )

        mock_client = Mock()
        mock_client.complete = AsyncMock(return_value=structured_result)
        mock_get_client.return_value = mock_client

        result = await complete_with_llm(
            prompt="Generate structured data", response_format=SampleStructuredOutput
        )

        assert isinstance(result, SampleStructuredOutput)
        assert result.message == "Structured convenience response"


class TestLLMClientErrorResilience:
    """Test LLM client error handling and resilience."""

    @pytest.fixture
    def client(self):
        return OpenAIClient(api_key="test-key")

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_network_error_handling(self, mock_openai, client):
        """Test network error handling."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APIConnectionError(
                message="Connection failed", request=Mock()
            )
        )
        client.client = mock_client

        # Set same model for both primary and fallback to avoid fallback logic
        client.default_model = "gpt-4"
        client.fallback_model = "gpt-4"

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMClientError, match="API connection error"):
            await client.complete(messages)

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_timeout_handling(self, mock_openai, client):
        """Test timeout error handling."""
        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(
            side_effect=openai.APITimeoutError(request=Mock())
        )
        client.client = mock_client

        # Set same model for both primary and fallback to avoid fallback logic
        client.default_model = "gpt-4"
        client.fallback_model = "gpt-4"

        messages = [{"role": "user", "content": "Test"}]

        with pytest.raises(LLMClientError, match="API connection error"):
            await client.complete(messages)

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_max_retries_exceeded(self, mock_openai, client):
        """Test behavior when max retries are exceeded."""
        # Mock client that always fails structured parsing
        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = "invalid json response"
        mock_response.usage = Mock(
            prompt_tokens=10, completion_tokens=5, total_tokens=15
        )

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        client.client = mock_client

        # Set same model for both primary and fallback to avoid fallback logic
        client.default_model = "gpt-4"
        client.fallback_model = "gpt-4"

        messages = [{"role": "user", "content": "Generate structured data"}]

        with pytest.raises(
            LLMValidationError,
            match="Failed to parse structured response after 3 attempts",
        ):
            await client.complete(messages, response_format=SampleStructuredOutput)

    def test_usage_metrics_serialization(self):
        """Test usage metrics can be serialized for storage."""
        metrics = LLMUsageMetrics(
            prompt_tokens=100,
            completion_tokens=50,
            total_tokens=150,
            estimated_cost_usd=0.01,
            model="gpt-4",
            timestamp="2024-01-01T00:00:00Z",
        )

        # Should be able to convert to dict for JSON serialization
        metrics_dict = {
            "prompt_tokens": metrics.prompt_tokens,
            "completion_tokens": metrics.completion_tokens,
            "total_tokens": metrics.total_tokens,
            "estimated_cost_usd": metrics.estimated_cost_usd,
            "model": metrics.model,
            "timestamp": metrics.timestamp,
        }

        assert json.dumps(metrics_dict)  # Should not raise exception


class TestRealWorldScenarios:
    """Test realistic usage scenarios."""

    @pytest.fixture
    def client(self):
        return OpenAIClient(api_key="test-key")

    @patch("libs.llm_client.AsyncOpenAI")
    async def test_constraint_extraction_scenario(self, mock_openai, client):
        """Test realistic constraint extraction scenario."""
        # Mock constraint extraction response
        constraints_data = {
            "project_description": "E-commerce recommendation system",
            "budget_band": "growth",
            "deployment_preference": "serverless",
            "workload_types": ["online_inference"],
            "expected_throughput": "medium",
            "data_classification": "internal",
        }

        extraction_result = {
            "constraints": constraints_data,
            "extraction_confidence": 0.82,
            "uncertain_fields": ["availability_target", "team_expertise"],
            "extraction_rationale": "Clear requirements for recommendation system",
            "follow_up_needed": True,
        }

        mock_response = Mock()
        mock_response.choices = [Mock()]
        mock_response.choices[0].message.content = json.dumps(extraction_result)
        mock_response.usage = Mock(
            prompt_tokens=150, completion_tokens=100, total_tokens=250
        )

        mock_client = Mock()
        mock_client.chat.completions.create = AsyncMock(return_value=mock_response)
        client.client = mock_client

        # Test extraction
        from libs.constraint_schema import ConstraintExtractionResult

        messages = [
            {"role": "system", "content": "You are an MLOps analyst."},
            {
                "role": "user",
                "content": "I need a recommendation system for my e-commerce site with moderate traffic.",
            },
        ]

        result = await client.complete(
            messages, response_format=ConstraintExtractionResult
        )

        assert isinstance(result, ConstraintExtractionResult)
        assert result.extraction_confidence == 0.82
        assert result.follow_up_needed
        assert (
            result.constraints.project_description == "E-commerce recommendation system"
        )

    def test_cost_estimation_accuracy(self, client):
        """Test cost estimation accuracy in usage tracking."""
        # Test various model pricing calculations
        models_to_test = [
            ("gpt-4", 1000, 500, 1500),
            ("gpt-3.5-turbo", 2000, 1000, 3000),
            ("gpt-4-turbo-preview", 1500, 750, 2250),
        ]

        for model, prompt_tokens, completion_tokens, total_tokens in models_to_test:
            mock_usage = Mock(
                prompt_tokens=prompt_tokens,
                completion_tokens=completion_tokens,
                total_tokens=total_tokens,
            )

            client._track_usage(mock_usage, model)

            # Verify usage was tracked
            assert len(client.usage_history) > 0
            latest_usage = client.usage_history[-1]

            assert latest_usage.model == model
            assert latest_usage.total_tokens == total_tokens
            assert latest_usage.estimated_cost_usd > 0

            # Cost should be proportional to tokens
            if model in client.MODEL_PRICING:
                expected_cost = (prompt_tokens / 1000) * client.MODEL_PRICING[model][
                    "input"
                ] + (completion_tokens / 1000) * client.MODEL_PRICING[model]["output"]
                assert abs(latest_usage.estimated_cost_usd - expected_cost) < 0.001


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
