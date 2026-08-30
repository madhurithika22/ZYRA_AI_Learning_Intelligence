import logging
import os
import time
from typing import Any, Callable, TypeVar

from app.providers.llm.base import LLMProvider
from app.providers.llm.gemini_provider import GeminiProvider
from pydantic import BaseModel

T = TypeVar("T", bound=BaseModel)

logger = logging.getLogger(__name__)


class KeySlotStatus:
    """Tracks state and bounded cooldown for an individual Gemini API key slot."""

    def __init__(self, slot: int, api_key: str) -> None:
        self.slot = slot
        self.api_key = api_key
        self.is_exhausted = False
        self.exhausted_until: float = 0.0

    @property
    def is_healthy(self) -> bool:
        if self.is_exhausted:
            if time.time() >= self.exhausted_until:
                self.is_exhausted = False
                self.exhausted_until = 0.0
                return True
            return False
        return True

    def mark_exhausted(self, cooldown_seconds: float = 60.0) -> None:
        self.is_exhausted = True
        self.exhausted_until = time.time() + cooldown_seconds


class GeminiKeyRouter(LLMProvider):
    """Router managing multiple Gemini API keys with 429/quota failure rotation and bounded cooldown."""

    def __init__(
        self,
        keys: list[str] | None = None,
        model_name: str | None = None,
        cooldown_seconds: float = 60.0,
        provider_factory: Callable[[str, str], LLMProvider] | None = None,
    ) -> None:
        if keys is None:
            keys = self._load_keys_from_env()

        self.cooldown_seconds = cooldown_seconds
        self.model_name: str = model_name or os.getenv("GEMINI_MODEL") or "gemini-2.5-flash"
        self.provider_factory = provider_factory or (
            lambda k, m: GeminiProvider(api_key=k, model_name=m)
        )

        self.slots: list[KeySlotStatus] = [
            KeySlotStatus(slot=idx + 1, api_key=k) for idx, k in enumerate(keys) if k.strip()
        ]

        self.last_used_slot: int | None = None
        self.last_fallback_used: bool = False
        self.last_failure_class: str | None = None

    @staticmethod
    def _load_keys_from_env() -> list[str]:
        keys: list[str] = []
        for slot in range(1, 4):
            val = os.getenv(f"GEMINI_API_KEY_{slot}")
            if val and val.strip():
                keys.append(val.strip())

        # Fallback to single GEMINI_API_KEY if no slot keys configured
        if not keys:
            single = os.getenv("GEMINI_API_KEY")
            if single and single.strip():
                keys.append(single.strip())

        return keys

    def get_quota_status(self) -> dict[str, dict[str, Any]]:
        """Safe diagnostic status representation of all key slots without exposing secrets."""
        status: dict[str, dict[str, Any]] = {}
        for slot in range(1, 4):
            key_name = f"Key {slot}"
            slot_obj = next((s for s in self.slots if s.slot == slot), None)
            if not slot_obj:
                status[key_name] = {"configured": False, "status": "unconfigured"}
            elif slot_obj.is_healthy:
                status[key_name] = {"configured": True, "status": "healthy"}
            else:
                remaining = max(0.0, slot_obj.exhausted_until - time.time())
                status[key_name] = {
                    "configured": True,
                    "status": f"exhausted (cooldown {remaining:.0f}s)",
                }
        return status

    async def generate_structured(
        self,
        prompt: str,
        response_model: type[T],
    ) -> T:
        if not self.slots:
            self.last_failure_class = "NO_KEYS_CONFIGURED"
            raise RuntimeError("No Gemini API keys configured. Set GEMINI_API_KEY_1 in environment.")

        healthy_slots = [s for s in self.slots if s.is_healthy]
        if not healthy_slots:
            self.last_failure_class = "ALL_KEYS_EXHAUSTED"
            raise RuntimeError("All configured Gemini API keys are currently exhausted (HTTP 429).")

        first_healthy_slot = healthy_slots[0].slot

        for s in healthy_slots:
            try:
                provider = self.provider_factory(s.api_key, self.model_name)
                result = await provider.generate_structured(prompt, response_model)

                self.last_used_slot = s.slot
                self.last_fallback_used = s.slot != first_healthy_slot
                self.last_failure_class = None
                return result

            except Exception as err:
                err_str = str(err)
                if self._is_quota_failure(err_str):
                    logger.warning(
                        f"Gemini Key Slot {s.slot} hit quota limit: {err_str[:100]}. Marking unavailable."
                    )
                    s.mark_exhausted(self.cooldown_seconds)
                    self.last_failure_class = "RESOURCE_EXHAUSTED_429"
                    continue
                else:
                    self.last_failure_class = "NON_QUOTA_ERROR"
                    raise

        self.last_failure_class = "ALL_KEYS_EXHAUSTED"
        raise RuntimeError("All configured Gemini API keys failed or were exhausted (HTTP 429).")

    @staticmethod
    def _is_quota_failure(err_msg: str) -> bool:
        err_lower = err_msg.lower()
        return any(
            kw in err_lower
            for kw in [
                "429",
                "resource_exhausted",
                "rate limit",
                "quota exceeded",
                "requests per day",
                "503",
                "service unavailable",
            ]
        )
