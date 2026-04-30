import logging
from typing import List, Optional

import httpx

logger = logging.getLogger(__name__)

# Expo's push API is used here because the mobile app is built with Expo.
# For production FCM/APNs direct integration, replace _send_to_all with
# provider-specific calls using self.fcm_server_key.
_EXPO_PUSH_URL = "https://exp.host/--/api/v2/push/send"


class PushNotificationService:
    """Sends push notifications to registered mobile devices via Expo Push API."""

    def __init__(self, fcm_server_key: Optional[str] = None):
        self.fcm_server_key = fcm_server_key
        self._tokens: List[str] = []

    # ── Device registry ───────────────────────────────────────────────────────

    def register_device(self, push_token: str) -> bool:
        if push_token not in self._tokens:
            self._tokens.append(push_token)
            logger.info("Registered device token: %s…", push_token[:20])
            return True
        return False

    def unregister_device(self, push_token: str) -> bool:
        if push_token in self._tokens:
            self._tokens.remove(push_token)
            return True
        return False

    def get_registered_count(self) -> int:
        return len(self._tokens)

    # ── Notification senders ──────────────────────────────────────────────────

    async def send_urgent_notification(
        self, subject: str, sender: str, email_id: str
    ) -> bool:
        if not self._tokens:
            logger.warning("No registered devices – urgent notification not sent.")
            return False
        return await self._send_to_all(
            title=f"Urgent: {subject[:50]}",
            body=f"From: {sender}",
            data={"type": "urgent_email", "email_id": email_id},
        )

    async def send_daily_report_notification(self, date: str, summary_count: int) -> bool:
        if not self._tokens:
            return False
        return await self._send_to_all(
            title="Daily Email Report Ready",
            body=f"Your report for {date} has {summary_count} summaries.",
            data={"type": "daily_report", "date": date},
        )

    # ── Internal ──────────────────────────────────────────────────────────────

    async def _send_to_all(self, title: str, body: str, data: dict) -> bool:
        messages = [
            {"to": token, "title": title, "body": body, "data": data}
            for token in self._tokens
        ]
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(
                    _EXPO_PUSH_URL,
                    json=messages,
                    headers={"Content-Type": "application/json"},
                )
                resp.raise_for_status()
            logger.info("Push notification sent to %d device(s).", len(messages))
            return True
        except Exception as exc:
            logger.error("Push notification failed: %s", exc)
            return False
