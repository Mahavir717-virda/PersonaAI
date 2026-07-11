import pytest
from uuid import uuid4
from unittest.mock import AsyncMock

from app.brain.schemas.state import BrainState, BrainContext, UserProfileSnapshot, AIMessage, MessageRole
from app.brain.communication.reply_detector import ReplyDetector
from app.brain.communication.intent import IntentDetector
from app.brain.communication.urgency import UrgencyDetector
from app.brain.communication.priority import PriorityDetector
from app.brain.communication.tone import ToneDetector
from app.brain.communication.category import CategoryDetector
from app.brain.communication.confidence import ConfidenceCalculator
from app.brain.communication.classifier import CommunicationClassifier
from app.brain.communication.engine import CommunicationEngine


@pytest.fixture
def default_context() -> BrainContext:
    profile = UserProfileSnapshot(
        user_id=uuid4(),
        timezone="UTC",
        language="en",
        permissions=["read"],
    )
    return BrainContext(
        session_id=uuid4(),
        tenant_id="test-tenant",
        user_profile=profile,
    )


def test_reply_detector_heuristics() -> None:
    """Verify ReplyDetector triggers correctly on key pattern matches."""
    # Test task triggers
    res_task = ReplyDetector.evaluate_triggers("Please send the updated proposal before Friday.")
    assert res_task["contains_task"] is True
    assert res_task["contains_deadline"] is True
    assert res_task["requires_reply"] is True

    # Test meeting triggers
    res_meet = ReplyDetector.evaluate_triggers("Let's schedule a Zoom call tomorrow.")
    assert res_meet["contains_meeting"] is True
    assert res_meet["requires_reply"] is True


def test_standardizing_cleaners() -> None:
    """Verify cleaners fall back gracefully on invalid inputs."""
    assert IntentDetector.clean_intent("request") == "request"
    assert IntentDetector.clean_intent("invalid_intent") == "unknown"

    assert UrgencyDetector.clean_urgency("high") == "high"
    assert UrgencyDetector.clean_urgency("critical") == "low"

    assert PriorityDetector.clean_priority("medium") == "medium"
    assert PriorityDetector.clean_priority("urgent") == "medium"

    assert ToneDetector.clean_tone("professional") == "professional"
    assert ToneDetector.clean_tone("angry") == "neutral"

    assert CategoryDetector.clean_category("work") == "work"
    assert CategoryDetector.clean_category("leisure") == "general"


@pytest.mark.asyncio
async def test_communication_classifier_fallback() -> None:
    """Verify classifier executes fallback path when model is offline."""
    classifier = CommunicationClassifier()
    
    # Trigger fallback with offline HTTP call error
    res = await classifier.classify("Schedule a meeting please.")
    
    assert res["requires_reply"] is True
    assert res["contains_meeting"] is True
    assert res["contains_task"] is True
    assert res["category"] == "work"


@pytest.mark.asyncio
async def test_communication_engine_pipeline(default_context: BrainContext) -> None:
    """Verify CommunicationEngine execute updates BrainState correctly."""
    mock_classifier = CommunicationClassifier()
    mock_classifier.classify = AsyncMock(return_value={
        "intent": "request",
        "emotion": "neutral",
        "urgency": "high",
        "priority": "high",
        "tone": "professional",
        "category": "work",
        "requires_reply": True,
        "contains_task": True,
        "contains_deadline": True,
        "contains_decision": False,
        "contains_meeting": False,
        "confidence": 0.9,
    })

    engine = CommunicationEngine(classifier=mock_classifier)
    state = BrainState(context=default_context)
    message = AIMessage(
        role=MessageRole.USER,
        sender="user",
        recipient="ai",
        content="Please submit the code today."
    )
    state = state.update(conversation=state.conversation.model_copy(update={"incoming_message": message}))
    
    updated_state = await engine.execute(state)
    
    comm_intel = updated_state.communication_intelligence
    assert comm_intel.intent == "request"
    assert comm_intel.urgency == "high"
    assert comm_intel.priority == "high"
    assert comm_intel.requires_reply is True
    assert comm_intel.contains_task is True
    assert comm_intel.contains_deadline is True
    assert comm_intel.confidence == 0.9
