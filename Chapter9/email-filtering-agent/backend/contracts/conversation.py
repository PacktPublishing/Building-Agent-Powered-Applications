import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ConversationMessage(BaseModel):
    role: MessageRole
    content: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ConversationSession(BaseModel):
    session_id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    messages: List[ConversationMessage] = []
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))
    context_type: str  # "followup" or "user_query"
    email_id: Optional[str] = None


class FollowUpState(BaseModel):
    email_id: str
    thread_id: str
    original_email: dict
    attempts: int = 0
    max_attempts: int = 3
    session_id: str
    status: str = "active"  # active, resolved, abandoned
    created_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class FollowUpReplyRequest(BaseModel):
    thread_id: str
    sender: str
    body: str
