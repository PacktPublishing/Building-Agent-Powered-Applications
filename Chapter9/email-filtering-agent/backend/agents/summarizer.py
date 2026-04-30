import logging

from openai import AsyncOpenAI

from backend.config import Settings
from backend.contracts.email import IncomingEmail

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an email summarization assistant producing entries for a daily digest.

Rules:
- Write exactly 2–3 sentences.
- Include only facts explicitly stated in the email — never infer or hallucinate.
- Mention the sender, the key update or decision, and any action items.
- Write in third person, past or present tense."""


class EmailSummarizer:
    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def summarize(self, email: IncomingEmail) -> str:
        prompt = (
            f"Summarize this email for the daily report:\n\n"
            f"From: {email.sender_name or email.sender} <{email.sender}>\n"
            f"Subject: {email.subject}\n"
            f"---\n"
            f"{email.body[:4000]}"
        )

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
            temperature=0.2,
            max_tokens=200,
        )

        return response.choices[0].message.content.strip()
