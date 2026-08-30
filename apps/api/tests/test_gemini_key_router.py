import pytest
from app.providers.llm.base import LLMProvider
from app.providers.llm.gemini_key_router import GeminiKeyRouter
from pydantic import BaseModel


class DummyResponse(BaseModel):
    answer: str


class MockSingleKeyProvider(LLMProvider):
    def __init__(self, slot_id: int, should_fail_429: bool = False, should_fail_generic: bool = False) -> None:
        self.slot_id = slot_id
        self.should_fail_429 = should_fail_429
        self.should_fail_generic = should_fail_generic

    async def generate_structured(self, prompt: str, response_model: type[BaseModel]) -> BaseModel:
        if self.should_fail_429:
            raise RuntimeError("429 RESOURCE_EXHAUSTED: Quota exceeded for metric")
        if self.should_fail_generic:
            raise ValueError("Invalid schema request")
        return DummyResponse(answer=f"Success from Key Slot {self.slot_id}")


@pytest.mark.asyncio
async def test_key_router_case_a_key1_success():
    # CASE A: Key 1 succeeds -> Key 1 used
    def factory(key: str, model: str) -> LLMProvider:
        slot = 1 if "key1" in key else (2 if "key2" in key else 3)
        return MockSingleKeyProvider(slot_id=slot, should_fail_429=False)

    router = GeminiKeyRouter(keys=["key1", "key2", "key3"], provider_factory=factory)
    res = await router.generate_structured("test prompt", DummyResponse)

    assert router.last_used_slot == 1
    assert router.last_fallback_used is False
    assert res.answer == "Success from Key Slot 1"


@pytest.mark.asyncio
async def test_key_router_case_b_key1_exhausted_key2_success():
    # CASE B: Key 1 quota exhausted (429) -> Key 2 used
    def factory(key: str, model: str) -> LLMProvider:
        if "key1" in key:
            return MockSingleKeyProvider(slot_id=1, should_fail_429=True)
        return MockSingleKeyProvider(slot_id=2, should_fail_429=False)

    router = GeminiKeyRouter(keys=["key1", "key2", "key3"], provider_factory=factory)
    res = await router.generate_structured("test prompt", DummyResponse)

    assert router.last_used_slot == 2
    assert router.last_fallback_used is True
    assert res.answer == "Success from Key Slot 2"
    assert router.slots[0].is_healthy is False


@pytest.mark.asyncio
async def test_key_router_case_c_key1_and_2_exhausted_key3_success():
    # CASE C: Key 1 + Key 2 exhausted -> Key 3 used
    def factory(key: str, model: str) -> LLMProvider:
        if "key1" in key:
            return MockSingleKeyProvider(slot_id=1, should_fail_429=True)
        if "key2" in key:
            return MockSingleKeyProvider(slot_id=2, should_fail_429=True)
        return MockSingleKeyProvider(slot_id=3, should_fail_429=False)

    router = GeminiKeyRouter(keys=["key1", "key2", "key3"], provider_factory=factory)
    res = await router.generate_structured("test prompt", DummyResponse)

    assert router.last_used_slot == 3
    assert router.last_fallback_used is True
    assert res.answer == "Success from Key Slot 3"


@pytest.mark.asyncio
async def test_key_router_case_d_all_keys_exhausted():
    # CASE D: All keys exhausted -> safe error
    def factory(key: str, model: str) -> LLMProvider:
        return MockSingleKeyProvider(slot_id=1, should_fail_429=True)

    router = GeminiKeyRouter(keys=["key1", "key2", "key3"], provider_factory=factory)
    with pytest.raises(RuntimeError, match="All configured Gemini API keys failed or were exhausted"):
        await router.generate_structured("test prompt", DummyResponse)

    assert router.last_failure_class == "ALL_KEYS_EXHAUSTED"


@pytest.mark.asyncio
async def test_key_router_case_e_cooldown_expiry():
    # CASE E: Key 1 recovers after cooldown
    def factory(key: str, model: str) -> LLMProvider:
        return MockSingleKeyProvider(slot_id=1, should_fail_429=False)

    router = GeminiKeyRouter(keys=["key1", "key2"], cooldown_seconds=0.01, provider_factory=factory)
    router.slots[0].mark_exhausted(cooldown_seconds=0.01)

    import asyncio
    await asyncio.sleep(0.02)  # Wait for cooldown to expire

    assert router.slots[0].is_healthy is True
    _ = await router.generate_structured("test prompt", DummyResponse)
    assert router.last_used_slot == 1


@pytest.mark.asyncio
async def test_key_router_case_f_non_quota_error_no_rotation():
    # CASE F: Generic non-quota error -> no rotation
    def factory(key: str, model: str) -> LLMProvider:
        return MockSingleKeyProvider(slot_id=1, should_fail_generic=True)

    router = GeminiKeyRouter(keys=["key1", "key2"], provider_factory=factory)
    with pytest.raises(ValueError, match="Invalid schema request"):
        await router.generate_structured("test prompt", DummyResponse)

    assert router.slots[0].is_healthy is True
    assert router.last_failure_class == "NON_QUOTA_ERROR"


@pytest.mark.asyncio
async def test_key_router_case_g_no_keys_configured():
    # CASE G: No keys configured -> explicit configuration error
    router = GeminiKeyRouter(keys=[], provider_factory=lambda k, m: MockSingleKeyProvider(1))
    with pytest.raises(RuntimeError, match="No Gemini API keys configured"):
        await router.generate_structured("test prompt", DummyResponse)
