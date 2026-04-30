import logging
from contextlib import asynccontextmanager
from datetime import datetime
from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from openai import AsyncOpenAI
from pydantic import BaseModel

from backend.agents.classifier import EmailClassifier
from backend.agents.followup import FollowUpService
from backend.agents.qa_agent import QAAgent
from backend.agents.summarizer import EmailSummarizer
from backend.config import settings
from backend.contracts.conversation import FollowUpReplyRequest
from backend.contracts.email import EmailCategory, ProcessEmailRequest, ProcessEmailResponse
from backend.contracts.report import DailyReport, QueryRequest, QueryResponse
from backend.memory.short_term_memory import ShortTermMemory
from backend.rag import create_rag
from backend.services.push_notification import PushNotificationService
from backend.storage.azure_report_storage import AzureReportStorage
from backend.storage.local_report_storage import LocalReportStorage
from backend.storage.report_storage import ReportStorage

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
logger = logging.getLogger(__name__)

# ── Shared singletons ─────────────────────────────────────────────────────────

memory = ShortTermMemory(
    client=AsyncOpenAI(api_key=settings.openai_api_key),
    model=settings.openai_model,
)
storage: ReportStorage = (
    AzureReportStorage(
        connection_string=settings.azure_storage_connection_string,
        container_name=settings.azure_storage_container,
    )
    if settings.azure_storage_connection_string
    else LocalReportStorage(settings.reports_dir)
)
push_service = PushNotificationService(fcm_server_key=settings.fcm_server_key)
indexer, retriever = create_rag(settings)

classifier = EmailClassifier(settings)
summarizer = EmailSummarizer(settings)
followup_service = FollowUpService(settings, memory)
qa_agent = QAAgent(settings, memory, retriever)


# ── Application lifecycle ─────────────────────────────────────────────────────

@asynccontextmanager
async def lifespan(app: FastAPI):
    pruned = storage.cleanup_old_reports(retention_days=settings.report_retention_days)
    if pruned:
        logger.info("Pruned %d old report(s).", pruned)

    existing = storage.get_reports_range(days=settings.report_retention_days)
    indexer.index_all(existing)
    logger.info("Indexed %d existing report(s) into vector store.", len(existing))

    logger.info("Email Filtering Agent backend is ready.")
    yield
    logger.info("Email Filtering Agent backend shutting down.")


app = FastAPI(
    title="Email Filtering Agent API",
    description="Backend for the personal email filtering agent (book example).",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ── Request / response helpers ────────────────────────────────────────────────

class DeviceRegisterRequest(BaseModel):
    push_token: str


class DeviceRegisterResponse(BaseModel):
    registered: bool
    device_count: int


# ── Email processing ──────────────────────────────────────────────────────────

@app.post("/api/emails/process", response_model=ProcessEmailResponse, tags=["Emails"])
async def process_email(request: ProcessEmailRequest) -> ProcessEmailResponse:
    """Classify an incoming email and take the appropriate action.

    Actions taken depend on the classification result:
    - **urgent** → push notification sent to the user's device(s).
    - **important** → LLM summary generated and appended to the daily report.
    - **requires_follow_up** → follow-up message drafted and returned in the response.
    - **ignore** → counters updated; no further action.
    """
    email = request.email
    logger.info("Processing email %s: '%s' from %s", email.id, email.subject, email.sender)

    result = await classifier.classify(email, request.user_preferences)
    actions: list[str] = [
        f"classified as '{result.category.value}' (confidence {result.confidence:.0%})"
    ]
    follow_up_message: Optional[str] = None
    summary: Optional[str] = None

    if result.category == EmailCategory.URGENT:
        await push_service.send_urgent_notification(
            subject=email.subject, sender=email.sender, email_id=email.id
        )
        storage.increment_counter("urgent")
        actions.append("push notification sent")

    elif result.category == EmailCategory.IMPORTANT:
        summary = await summarizer.summarize(email)
        from backend.contracts.report import EmailSummary  # local import to avoid circularity
        report = storage.add_summary(
            EmailSummary(
                email_id=email.id,
                sender=email.sender_name or email.sender,
                subject=email.subject,
                summary=summary,
                received_at=email.received_at,
            )
        )
        indexer.index_report(report)
        actions.append("summary added to daily report and indexed")

    elif result.category == EmailCategory.REQUIRES_FOLLOW_UP:
        state, follow_up_message = await followup_service.initiate_followup(email)
        storage.increment_counter("requires_follow_up")
        actions.append(f"follow-up initiated (thread_id={state.thread_id})")

    else:  # IGNORE
        storage.increment_counter("ignore")
        actions.append("email ignored — no action taken")

    return ProcessEmailResponse(
        email_id=email.id,
        category=result.category,
        actions_taken=actions,
        follow_up_message=follow_up_message,
        summary=summary,
    )


# ── Follow-up replies ─────────────────────────────────────────────────────────

@app.post("/api/followup/reply", tags=["Follow-ups"])
async def process_followup_reply(request: FollowUpReplyRequest):
    """Process an external reply to a follow-up message.

    Returns whether the conversation is resolved and, if more information is
    still needed, the next follow-up message to send.
    """
    try:
        state, next_followup, resolved_category = await followup_service.process_reply(
            thread_id=request.thread_id,
            reply_body=request.body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=404, detail=str(exc))

    if resolved_category:
        return {
            "status": "resolved",
            "resolved_category": resolved_category.value,
            "next_followup_message": None,
        }

    return {
        "status": "pending",
        "resolved_category": None,
        "next_followup_message": next_followup,
    }


@app.get("/api/followups/{email_id}", tags=["Follow-ups"])
async def get_followup_status(email_id: str):
    """Return the current follow-up status for a given email."""
    for state in memory.get_all_followup_states().values():
        if state.email_id == email_id:
            return {
                "email_id": email_id,
                "thread_id": state.thread_id,
                "status": state.status,
                "attempts": state.attempts,
                "max_attempts": state.max_attempts,
            }
    raise HTTPException(status_code=404, detail="No follow-up found for this email.")


# ── Reports ───────────────────────────────────────────────────────────────────

@app.get("/api/reports/daily", response_model=DailyReport, tags=["Reports"])
async def get_today_report() -> DailyReport:
    """Return today's (UTC) email report."""
    return storage.get_or_create_report()


@app.get("/api/reports/daily/{date}", response_model=DailyReport, tags=["Reports"])
async def get_report_by_date(date: str) -> DailyReport:
    """Return the daily report for a specific date (YYYY-MM-DD)."""
    try:
        datetime.strptime(date, "%Y-%m-%d")
    except ValueError:
        raise HTTPException(status_code=400, detail="Date must be in YYYY-MM-DD format.")
    return storage.get_or_create_report(date)


@app.post("/api/reports/finalize", response_model=DailyReport, tags=["Reports"])
async def finalize_report(date: Optional[str] = None) -> DailyReport:
    """Finalize today's report and push a summary notification to all devices."""
    report = storage.finalize_report(date)
    indexer.index_report(report)
    await push_service.send_daily_report_notification(
        date=report.date, summary_count=len(report.summaries)
    )
    return report


# ── Q&A ───────────────────────────────────────────────────────────────────────

@app.post("/api/query", response_model=QueryResponse, tags=["Q&A"])
async def query_emails(request: QueryRequest) -> QueryResponse:
    """Answer a natural-language question about past email activity."""
    return await qa_agent.answer(
        question=request.question,
        session_id=request.session_id,
    )


# ── Device registration ───────────────────────────────────────────────────────

@app.post("/api/devices/register", response_model=DeviceRegisterResponse, tags=["Devices"])
async def register_device(request: DeviceRegisterRequest) -> DeviceRegisterResponse:
    """Register a mobile device push token to receive notifications."""
    registered = push_service.register_device(request.push_token)
    return DeviceRegisterResponse(
        registered=registered,
        device_count=push_service.get_registered_count(),
    )


@app.delete("/api/devices/{push_token}", tags=["Devices"])
async def unregister_device(push_token: str):
    """Remove a device from the push notification registry."""
    removed = push_service.unregister_device(push_token)
    return {"removed": removed}


# ── Health ────────────────────────────────────────────────────────────────────

@app.get("/api/health", tags=["System"])
async def health_check():
    return {
        "status": "healthy",
        "registered_devices": push_service.get_registered_count(),
    }
