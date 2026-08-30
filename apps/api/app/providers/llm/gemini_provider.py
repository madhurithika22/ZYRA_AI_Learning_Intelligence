import os
from typing import TypeVar

from app.providers.llm.base import LLMProvider
from google import genai
from google.genai import types
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)


class GeminiProvider(LLMProvider):
    """Google Gemini provider implementation using google-genai SDK."""

    def __init__(self, api_key: str | None = None, model_name: str | None = None) -> None:
        self.api_key = api_key if api_key is not None else os.getenv("GEMINI_API_KEY")
        self.model_name: str = model_name or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        if not self.api_key:
            raise RuntimeError("GEMINI_API_KEY environment variable is missing for GeminiProvider.")

        client = genai.Client(api_key=self.api_key)

        config = types.GenerateContentConfig(
            response_mime_type="application/json",
            response_schema=response_model,
            automatic_function_calling=types.AutomaticFunctionCallingConfig(disable=True),
        )

        try:
            response = await client.aio.models.generate_content(
                model=self.model_name,
                contents=prompt,
                config=config,
            )
            if not response.text:
                raise ValueError("Gemini returned empty response text.")

            return response_model.model_validate_json(response.text)
        except Exception as err:
            raise RuntimeError(f"Gemini API error ({self.model_name}): {str(err)}") from err
