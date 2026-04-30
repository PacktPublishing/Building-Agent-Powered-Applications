from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel


class EmailSummary(BaseModel):
    email_id: str
    sender: str
    subject: str
    summary: str
    received_at: datetime


class DailyReport(BaseModel):
    date: str  # YYYY-MM-DD
    summaries: List[EmailSummary] = []
    urgent_count: int = 0
    important_count: int = 0
    ignored_count: int = 0
    follow_up_count: int = 0
    finalized: bool = False
    finalized_at: Optional[datetime] = None


class QueryRequest(BaseModel):
    question: str
    session_id: Optional[str] = None


class QueryResponse(BaseModel):
    answer: str
    session_id: str
    sources: List[str] = []
