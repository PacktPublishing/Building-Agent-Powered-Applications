import uuid
from typing import Dict, List, Optional

from openai import AsyncOpenAI

from backend.contracts.conversation import (
    ConversationMessage,
    ConversationSession,
    FollowUpState,
    MessageRole,
)

_SUMMARIZE_SYSTEM_PROMPT = """\
You are compressing older turns of a conversation into a compact memory block.
Your output will be injected as context for an AI assistant continuing the conversation.

Rules:
- Preserve every fact, decision, question asked, and answer given — nothing important may be lost.
- Keep named entities (people, email senders, subjects, dates, categories) verbatim.
- Note any unresolved questions or pending actions explicitly.
- Write in past tense, third-person neutral ("The user asked...", "The assistant confirmed...").
- Be as concise as possible without omitting anything load-bearing.
- Output plain prose — no bullet lists, no headers.\
"""


class ShortTermMemory:
    """Short-term memory for multi-turn conversations.

    Applies a three-tier context strategy when building the message list for
    the LLM:
      - Last *recent_verbatim* (default 5) messages: kept in full.
      - Up to the previous *max_messages - recent_verbatim* (default 15) messages:
        compressed into a single summary message via an LLM call.
      - Anything older than *max_messages* (default 20): discarded.

    System messages are always placed first and are never summarised.
    """

    def __init__(
        self,
        max_messages: int = 20,
        recent_verbatim: int = 5,
        client: Optional[AsyncOpenAI] = None,
        model: str = "gpt-4o",
    ):
        self._sessions: Dict[str, ConversationSession] = {}
        self._followup_states: Dict[str, FollowUpState] = {}
        self._summary_cache: Dict[str, str] = {}  # session_id -> cached summary
        self.max_messages = max_messages
        self.recent_verbatim = recent_verbatim
        self._client = client
        self._model = model

    # ── Session management ────────────────────────────────────────────────────

    def create_session(
        self, context_type: str, email_id: Optional[str] = None
    ) -> ConversationSession:
        session = ConversationSession(context_type=context_type, email_id=email_id)
        self._sessions[session.session_id] = session
        return session

    def get_session(self, session_id: str) -> Optional[ConversationSession]:
        return self._sessions.get(session_id)

    def add_message(self, session_id: str, role: MessageRole, content: str) -> bool:
        session = self._sessions.get(session_id)
        if not session:
            return False

        session.messages.append(ConversationMessage(role=role, content=content))
        self._summary_cache.pop(session_id, None)  # invalidate cached summary

        # Hard cap: keep system messages + last max_messages non-system messages
        if len(session.messages) > self.max_messages:
            system_msgs = [m for m in session.messages if m.role == MessageRole.SYSTEM]
            other_msgs = [m for m in session.messages if m.role != MessageRole.SYSTEM]
            keep = self.max_messages - len(system_msgs)
            session.messages = system_msgs + other_msgs[-keep:]

        return True

    async def get_messages_for_llm(self, session_id: str) -> List[dict]:
        """Return messages formatted for the OpenAI chat completions API.

        Applies the three-tier strategy: verbatim recent, summarised middle,
        discarded oldest.
        """
        session = self._sessions.get(session_id)
        if not session:
            return []

        system_msgs = [m for m in session.messages if m.role == MessageRole.SYSTEM]
        non_system = [m for m in session.messages if m.role != MessageRole.SYSTEM]

        result = [{"role": m.role.value, "content": m.content} for m in system_msgs]

        if len(non_system) <= self.recent_verbatim:
            result.extend({"role": m.role.value, "content": m.content} for m in non_system)
            return result

        verbatim = non_system[-self.recent_verbatim:]
        to_summarize = non_system[-self.max_messages: -self.recent_verbatim]

        if to_summarize:
            summary = await self._get_or_build_summary(session_id, to_summarize)
            result.append({"role": "system", "content": f"[Earlier conversation summary]: {summary}"})

        result.extend({"role": m.role.value, "content": m.content} for m in verbatim)
        return result

    async def _get_or_build_summary(
        self, session_id: str, messages: List[ConversationMessage]
    ) -> str:
        if session_id in self._summary_cache:
            return self._summary_cache[session_id]

        if not self._client:
            # Fallback: plain text condensation when no LLM client is available
            summary = " | ".join(
                f"{m.role.value}: {m.content[:120]}" for m in messages
            )
            self._summary_cache[session_id] = summary
            return summary

        formatted = "\n".join(f"{m.role.value}: {m.content}" for m in messages)
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": _SUMMARIZE_SYSTEM_PROMPT},
                {"role": "user", "content": formatted},
            ],
            max_tokens=300,
            temperature=0.2,
        )
        summary = response.choices[0].message.content.strip()
        self._summary_cache[session_id] = summary
        return summary

    # ── Follow-up state management ────────────────────────────────────────────

    def create_followup_state(
        self,
        email_id: str,
        thread_id: Optional[str],
        original_email: dict,
        max_attempts: int,
    ) -> FollowUpState:
        session = self.create_session(context_type="followup", email_id=email_id)
        state = FollowUpState(
            email_id=email_id,
            thread_id=thread_id or str(uuid.uuid4()),
            original_email=original_email,
            max_attempts=max_attempts,
            session_id=session.session_id,
        )
        self._followup_states[state.thread_id] = state
        return state

    def get_followup_state(self, thread_id: str) -> Optional[FollowUpState]:
        return self._followup_states.get(thread_id)

    def update_followup_state(self, thread_id: str, **kwargs) -> bool:
        state = self._followup_states.get(thread_id)
        if not state:
            return False
        for key, value in kwargs.items():
            setattr(state, key, value)
        return True

    def get_all_followup_states(self) -> Dict[str, FollowUpState]:
        return dict(self._followup_states)
