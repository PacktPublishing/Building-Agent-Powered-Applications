import logging
from typing import List, Tuple

import chromadb

logger = logging.getLogger(__name__)


class ReportRetriever:
    """Retrieves the most semantically relevant report chunks for a query.

    Searches across all indexed data — the retention window is enforced by
    storage (cleanup_old_reports) rather than repeated here.

    Returns formatted context text and the dates of the matched chunks so
    callers can surface them as source references.
    """

    def __init__(self, collection: chromadb.Collection, top_k: int = 5):
        self._collection = collection
        self._top_k = top_k

    def retrieve(self, query: str) -> Tuple[str, List[str]]:
        """Return (context_text, source_dates) for the top-k relevant chunks."""
        count = self._collection.count()
        if count == 0:
            return "No email data has been indexed yet.", []

        n = min(self._top_k, count)
        results = self._collection.query(
            query_texts=[query],
            n_results=n,
            include=["documents", "metadatas"],
        )

        docs: List[str] = results["documents"][0] if results["documents"] else []
        metas: List[dict] = results["metadatas"][0] if results["metadatas"] else []

        if not docs:
            return "No relevant email data found.", []

        context = "\n".join(f"- {doc}" for doc in docs)
        source_dates = sorted({m["date"] for m in metas if "date" in m}, reverse=True)
        return context, source_dates
