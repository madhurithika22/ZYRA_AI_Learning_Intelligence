from uuid import uuid4

import pytest
from app.models.learner import Learner
from app.providers.llm.gemini_provider import GeminiProvider
from app.providers.llm.mock_provider import MockLLMProvider
from app.schemas.conversation import ConversationIntent, GroundedAnswer
from app.services.conversation.conversational_service import ConversationalService
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.mark.asyncio
async def test_create_and_get_conversation_session(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()

    service = ConversationalService(db_session)
    sess = await service.create_session(alex.id, title="Pytest Session")

    assert sess.id is not None
    assert sess.learner_id == alex.id
    assert sess.title == "Pytest Session"

    detail = await service.get_session(sess.id, alex.id)
    assert detail.session.id == sess.id
    assert len(detail.messages) == 0


@pytest.mark.asyncio
async def test_send_conversation_message_grounded(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()

    service = ConversationalService(db_session)
    sess = await service.create_session(alex.id)

    msg = await service.send_message(sess.id, alex.id, "Why is Model Deployment my bottleneck?")

    assert msg.role == "assistant"
    assert msg.intent in (ConversationIntent.BOTTLENECK_EXPLANATION, ConversationIntent.SKILL_STATUS)
    assert msg.content is not None
    assert len(msg.content) > 0
    assert len(msg.sources) > 0


@pytest.mark.asyncio
async def test_send_conversation_message_unsupported(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()

    service = ConversationalService(db_session)
    sess = await service.create_session(alex.id)

    msg = await service.send_message(sess.id, alex.id, "What is the weather tomorrow?")

    assert msg.role == "assistant"
    assert msg.intent == ConversationIntent.UNSUPPORTED
    assert "weather" in msg.content.lower() or "external" in msg.content.lower()


@pytest.mark.asyncio
async def test_deterministic_query_bypasses_llm(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()

    service = ConversationalService(db_session)
    sess = await service.create_session(alex.id)

    msg = await service.send_message(sess.id, alex.id, "What is my current mastery?")

    assert msg.used_llm is False
    assert "mastery" in msg.content.lower() or "target" in msg.content.lower()


@pytest.mark.asyncio
async def test_gemini_provider_missing_key() -> None:
    provider = GeminiProvider(api_key="")
    with pytest.raises(RuntimeError, match="GEMINI_API_KEY environment variable is missing"):
        await provider.generate_structured("test", GroundedAnswer)


@pytest.mark.asyncio
async def test_gemini_failure_returns_safe_error(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()

    failing_provider = MockLLMProvider(override_response=RuntimeError("Simulated Gemini API Timeout"))
    service = ConversationalService(db_session, llm_provider=failing_provider)
    sess = await service.create_session(alex.id)

    msg = await service.send_message(sess.id, alex.id, "Why is Model Deployment my bottleneck?")

    assert msg.used_llm is False
    assert "couldn't generate" in msg.content.lower() or "provider issue" in msg.content.lower()
    assert len(msg.sources) > 0


@pytest.mark.asyncio
async def test_conversation_ownership_security(db_session: AsyncSession) -> None:
    alex = (await db_session.execute(select(Learner).where(Learner.email == "alex.chen@example.com"))).scalar_one()

    service = ConversationalService(db_session)
    sess = await service.create_session(alex.id)

    fake_learner_id = uuid4()

    with pytest.raises(PermissionError, match="Access denied"):
        await service.send_message(sess.id, fake_learner_id, "Test unauthorized")

    with pytest.raises(PermissionError, match="Access denied"):
        await service.get_session(sess.id, fake_learner_id)
