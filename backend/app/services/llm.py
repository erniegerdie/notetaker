"""LiteLLM service for structured LLM interactions."""

import json
import logging
from typing import Any, List, Optional, Type, TypeVar, Union

from litellm import acompletion
from pydantic import BaseModel, ValidationError

from app.config import settings

logger = logging.getLogger(__name__)

T = TypeVar("T", bound=BaseModel)


class LLMService:
    """Service for interacting with LLMs via LiteLLM."""

    def __init__(
        self,
        model: Optional[str] = None,
        temperature: float = 0.7,
        max_tokens: Optional[int] = None,
    ):
        """Initialize LLM service.

        Args:
            model: Model identifier (defaults to settings.notes_model)
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens in response
        """
        self.model = model or settings.notes_model
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def chat(
        self,
        messages: List[dict[str, str]],
        *,
        response_model: Optional[Type[T]] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        max_retries: int = 3,
        **kwargs: Any,
    ) -> Union[str, T]:
        """Send chat completion request with optional structured output.

        Args:
            messages: List of message dicts with 'role' and 'content'
            response_model: Optional Pydantic model for structured responses
            temperature: Override default temperature
            max_tokens: Override default max_tokens
            max_retries: Number of retry attempts on failure
            **kwargs: Additional arguments passed to litellm.acompletion

        Returns:
            String content if no response_model, otherwise parsed Pydantic model instance

        Raises:
            ValidationError: If response doesn't match response_model schema
            Exception: On API errors after retries exhausted
        """
        temp = temperature if temperature is not None else self.temperature
        tokens = max_tokens if max_tokens is not None else self.max_tokens

        # Build request arguments
        request_args = {
            "model": self.model,
            "messages": messages,
            "temperature": temp,
            **kwargs,
        }

        if tokens:
            request_args["max_tokens"] = tokens

        # LiteLLM native Pydantic support
        if response_model:
            request_args["response_format"] = response_model

        # Execute with retries
        last_error = None
        for attempt in range(max_retries):
            try:
                logger.debug(
                    "litellm_request",
                    model=self.model,
                    messages_count=len(messages),
                    has_response_model=response_model is not None,
                    attempt=attempt + 1,
                )

                response = await acompletion(**request_args)

                # Parse structured response if model provided
                if response_model:
                    return self._parse_response(response, response_model)

                return response.choices[0].message.content

            except ValidationError as e:
                logger.warning(
                    "litellm_validation_error",
                    error=str(e),
                    attempt=attempt + 1,
                    model_name=response_model.__name__ if response_model else None,
                )
                last_error = e

                # Retry validation errors
                if attempt < max_retries - 1:
                    continue
                raise

            except Exception as e:
                logger.error(
                    "litellm_request_failed",
                    error=str(e),
                    error_type=type(e).__name__,
                    attempt=attempt + 1,
                )
                last_error = e

                # Retry on transient errors
                if attempt < max_retries - 1:
                    continue
                raise

        # Should never reach here, but satisfy type checker
        if last_error:
            raise last_error
        raise RuntimeError("Unexpected error in LLM request")

    def _parse_response(self, response: Any, response_model: Type[T]) -> T:
        """Parse response into Pydantic model.

        LiteLLM supports native Pydantic parsing via response.choices[0].message.parsed.
        Falls back to manual JSON parsing if parsed attribute not available.

        Args:
            response: LiteLLM response object
            response_model: Pydantic model class

        Returns:
            Parsed model instance

        Raises:
            ValidationError: If content doesn't match schema
        """
        logger.debug("parsing_response", model_name=response_model.__name__)

        try:
            # Try native LiteLLM parsed response first
            return response.choices[0].message.parsed
        except AttributeError:
            # Fallback to manual parsing
            content = response.choices[0].message.content

            # Strip markdown code fences if present
            if content.startswith("```json"):
                content = content[7:]
            if content.endswith("```"):
                content = content[:-3]
            content = content.strip()

            try:
                data = json.loads(content)
                return response_model.model_validate(data)
            except json.JSONDecodeError as e:
                logger.error(
                    "json_decode_error",
                    content=content[:200],
                    error=str(e),
                )
                raise ValidationError(f"Invalid JSON response: {e}") from e


# Singleton instance for convenience
_llm_service: Optional[LLMService] = None


def get_llm_service() -> LLMService:
    """Get or create singleton LLM service instance.

    Returns:
        Shared LLMService instance
    """
    global _llm_service
    if _llm_service is None:
        _llm_service = LLMService()
    return _llm_service


async def chat(
    messages: List[dict[str, str]],
    *,
    response_model: Optional[Type[T]] = None,
    **kwargs: Any,
) -> Union[str, T]:
    """Convenience function for chat completion.

    Args:
        messages: List of message dicts with 'role' and 'content'
        response_model: Optional Pydantic model for structured responses
        **kwargs: Additional arguments (temperature, max_tokens, etc.)

    Returns:
        String content if no response_model, otherwise parsed Pydantic model instance
    """
    service = get_llm_service()
    return await service.chat(messages, response_model=response_model, **kwargs)
