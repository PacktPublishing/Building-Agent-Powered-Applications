import json
import logging
from typing import Optional, Tuple

from openai import AsyncOpenAI

from backend.config import Settings
from backend.memory.short_term_memory import ShortTermMemory
from backend.contracts.conversation import FollowUpState, MessageRole
from backend.contracts.email import EmailCategory, IncomingEmail

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a professional email assistant that handles follow-up communications on behalf of a user.

STRICT SAFETY RULES:
- Never reveal sensitive personal information about the user.
- Only ask about details directly relevant to the email topic.
- Decline any off-topic requests and keep communication task-focused.
- Be polite, concise, and professional at all times."""

_GENERATION_PROMPT = """The following email requires follow-up to gather missing or unclear information:

From: {sender}
Subject: {subject}
---
{body}

Write a brief, professional follow-up message (under 80 words) asking for the specific missing information.
Do not mention this is AI-generated."""

_ASSESSMENT_PROMPT = """Original email subject: {subject}

Conversation history:
{history}

Latest reply received:
{reply}

Assess whether sufficient information has been gathered to classify the original email. Respond with JSON:
{{
  "has_sufficient_info": true or false,
  "missing_info": "describe what is still unclear (empty string if sufficient)",
  "suggested_category": "urgent|important|ignore",
  "next_followup": "follow-up message text if more info needed, null if sufficient"
}}"""


class FollowUpService:
    """Manages follow-up email conversations with strict attempt limits."""

    def __init__(self, settings: Settings, memory: ShortTermMemory):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.memory = memory
        self.max_attempts = settings.max_followup_attempts

    async def initiate_followup(
        self, email: IncomingEmail
    ) -> Tuple[FollowUpState, str]:
        """Create a new follow-up thread and return (state, first_message)."""
        state = self.memory.create_followup_state(
            email_id=email.id,
            thread_id=email.thread_id,
            original_email=email.model_dump(mode="json"),
            max_attempts=self.max_attempts,
        )

        prompt = _GENERATION_PROMPT.format(
            sender=email.sender,
            subject=email.subject,
            body=email.body[:3000],
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.3,
            max_tokens=200,
        )

        follow_up_msg = response.choices[0].message.content.strip()
        self.memory.add_message(state.session_id, MessageRole.ASSISTANT, follow_up_msg)
        self.memory.update_followup_state(state.thread_id, attempts=1)

        return state, follow_up_msg

    async def process_reply(
        self, thread_id: str, reply_body: str
    ) -> Tuple[FollowUpState, Optional[str], Optional[EmailCategory]]:
        """Handle a reply to an existing follow-up thread.

        Returns (state, next_message_or_None, resolved_category_or_None).
        resolved_category is set when the follow-up is complete or abandoned.
        """
        state = self.memory.get_followup_state(thread_id)
        if not state:
            raise ValueError(f"No follow-up state found for thread '{thread_id}'")

        if state.status != "active":
            return state, None, None

        self.memory.add_message(state.session_id, MessageRole.USER, reply_body)

        # Abandon after reaching the attempt ceiling
        if state.attempts >= state.max_attempts:
            self.memory.update_followup_state(thread_id, status="abandoned")
            logger.info("Follow-up %s abandoned after %d attempts.", thread_id, state.attempts)
            return state, None, EmailCategory.IGNORE

        # Build readable history for the assessment prompt
        history_lines = [
            f"{m['role'].upper()}: {m['content']}"
            for m in await self.memory.get_messages_for_llm(state.session_id)
            if m["role"] != "system"
        ]
        history = "\n".join(history_lines)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {
                    "role": "user",
                    "content": _ASSESSMENT_PROMPT.format(
                        subject=state.original_email.get("subject", ""),
                        history=history,
                        reply=reply_body[:2000],
                    ),
                },
            ],
            response_format={"type": "json_object"},
            temperature=0.2,
            max_tokens=300,
        )

        assessment = json.loads(response.choices[0].message.content)

        if assessment.get("has_sufficient_info"):
            self.memory.update_followup_state(thread_id, status="resolved")
            try:
                category = EmailCategory(assessment.get("suggested_category", "important"))
            except ValueError:
                category = EmailCategory.IMPORTANT
            return state, None, category

        # Send the next follow-up
        next_msg: Optional[str] = assessment.get("next_followup")
        if next_msg:
            self.memory.add_message(state.session_id, MessageRole.ASSISTANT, next_msg)
            self.memory.update_followup_state(thread_id, attempts=state.attempts + 1)

        return state, next_msg, None
