import json
import logging
from typing import Optional

from openai import AsyncOpenAI

from backend.config import Settings
from backend.contracts.email import (
    ClassificationResult,
    EmailCategory,
    IncomingEmail,
    UserPreferences,
)

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are an intelligent email classification agent.
Analyze each incoming email and assign exactly one category:

- urgent: Requires immediate user attention — deadlines, critical issues, emergencies, or explicit "action required" requests.
- important: Contains valuable information worth logging — status updates, decisions, project progress, or meaningful correspondence.
- requires_follow_up: Contains open questions, missing context, or ambiguous content that must be clarified before it can be acted on.
- ignore: Newsletters, promotions, automated digests, spam, or any low-value content the user need not see.

Be conservative with "urgent" — only use it when truly time-sensitive.
Use "requires_follow_up" only when a clarifying reply is genuinely necessary.

Respond with valid JSON only — no markdown fences."""


def _build_prompt(email: IncomingEmail, prefs: Optional[UserPreferences]) -> str:
    prefs_block = ""
    if prefs:
        if prefs.urgent_keywords:
            prefs_block += f"\nUser flags these words as urgent: {', '.join(prefs.urgent_keywords)}"
        if prefs.important_senders:
            prefs_block += f"\nAlways treat mail from these senders as important: {', '.join(prefs.important_senders)}"
        if prefs.ignore_keywords:
            prefs_block += f"\nIgnore emails containing: {', '.join(prefs.ignore_keywords)}"
        if prefs.custom_rules:
            prefs_block += f"\nAdditional rules: {prefs.custom_rules}"

    return f"""Classify the following email:{prefs_block}

From: {email.sender_name or email.sender} <{email.sender}>
Subject: {email.subject}
---
{email.body[:3000]}

Respond with JSON:
{{
  "category": "urgent|important|requires_follow_up|ignore",
  "reasoning": "one-sentence explanation",
  "confidence": 0.0-1.0
}}"""


class EmailClassifier:
    def __init__(self, settings: Settings):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model

    async def classify(
        self,
        email: IncomingEmail,
        user_preferences: Optional[UserPreferences] = None,
    ) -> ClassificationResult:
        response = await self.client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": _SYSTEM_PROMPT},
                {"role": "user", "content": _build_prompt(email, user_preferences)},
            ],
            response_format={"type": "json_object"},
            temperature=0.1,
            max_tokens=256,
        )

        raw = json.loads(response.choices[0].message.content)

        try:
            category = EmailCategory(raw["category"])
        except (KeyError, ValueError):
            logger.warning("Unexpected category '%s'; defaulting to ignore.", raw.get("category"))
            category = EmailCategory.IGNORE

        return ClassificationResult(
            email_id=email.id,
            category=category,
            reasoning=raw.get("reasoning", ""),
            confidence=float(raw.get("confidence", 0.8)),
        )
