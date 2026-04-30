import logging
from typing import Optional

from openai import AsyncOpenAI

from backend.config import Settings
from backend.contracts.conversation import MessageRole
from backend.contracts.report import QueryResponse
from backend.memory.short_term_memory import ShortTermMemory
from backend.rag.report_retriever import ReportRetriever

logger = logging.getLogger(__name__)

_SYSTEM_PROMPT = """You are a helpful email assistant that answers user questions about their email activity.

Rules:
- Answer based solely on the email data provided with each question.
- If the information is not in the provided data, say so clearly — do not guess.
- Be concise and specific; cite the report date when referencing a specific email.
- Maintain context across multi-turn conversations."""


class QAAgent:
    """Multi-turn Q&A agent using RAG over indexed daily report data."""

    def __init__(self, settings: Settings, memory: ShortTermMemory, retriever: ReportRetriever):
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)
        self.model = settings.openai_model
        self.memory = memory
        self.retriever = retriever

    async def answer(
        self,
        question: str,
        session_id: Optional[str] = None,
    ) -> QueryResponse:
        session = self.memory.get_session(session_id) if session_id else None

        if session is None:
            session = self.memory.create_session(context_type="user_query")
            self.memory.add_message(session.session_id, MessageRole.SYSTEM, _SYSTEM_PROMPT)

        # Retrieve only the most relevant chunks for this specific question
        context, source_dates = self.retriever.retrieve(question)

        # Inject retrieved context alongside the question so each turn is grounded
        user_content = f"Relevant email data:\n{context}\n\nQuestion: {question}"
        self.memory.add_message(session.session_id, MessageRole.USER, user_content)

        response = await self.client.chat.completions.create(
            model=self.model,
            messages=await self.memory.get_messages_for_llm(session.session_id),
            temperature=0.3,
            max_tokens=500,
        )

        answer_text = response.choices[0].message.content.strip()
        self.memory.add_message(session.session_id, MessageRole.ASSISTANT, answer_text)

        return QueryResponse(
            answer=answer_text,
            session_id=session.session_id,
            sources=source_dates,
        )
