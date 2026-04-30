import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


class EmailCategory(str, Enum):
    URGENT = "urgent"
    IMPORTANT = "important"
    REQUIRES_FOLLOW_UP = "requires_follow_up"
    IGNORE = "ignore"


class UserPreferences(BaseModel):
    urgent_keywords: List[str] = ["urgent", "critical", "asap", "deadline", "emergency"]
    important_senders: List[str] = []
    ignore_keywords: List[str] = ["newsletter", "unsubscribe", "promotion", "no-reply"]
    custom_rules: Optional[str] = None


class IncomingEmail(BaseModel):
    id: str = Field(default_factory=lambda: str(uuid.uuid4()))
    sender: str
    sender_name: Optional[str] = None
    subject: str
    body: str
    thread_id: Optional[str] = None
    received_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class ClassificationResult(BaseModel):
    email_id: str
    category: EmailCategory
    reasoning: str
    confidence: float


class ProcessEmailRequest(BaseModel):
    email: IncomingEmail
    user_preferences: Optional[UserPreferences] = None


class ProcessEmailResponse(BaseModel):
    email_id: str
    category: EmailCategory
    actions_taken: List[str]
    follow_up_message: Optional[str] = None
    summary: Optional[str] = None
