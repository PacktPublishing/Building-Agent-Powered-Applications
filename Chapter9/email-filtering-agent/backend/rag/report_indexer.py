import logging
from typing import List

import chromadb

from backend.contracts.report import DailyReport

logger = logging.getLogger(__name__)


class ReportIndexer:
    """Indexes daily email reports into ChromaDB for semantic retrieval.

    Each report produces two types of chunks:
      - One chunk per EmailSummary (fine-grained, captures sender/subject/content).
      - One stats chunk capturing the day's category counts.

    All chunks are upserted by deterministic IDs, so re-indexing is idempotent.
    """

    def __init__(self, collection: chromadb.Collection):
        self._collection = collection

    def index_report(self, report: DailyReport) -> None:
        documents: List[str] = []
        ids: List[str] = []
        metadatas: List[dict] = []

        for summary in report.summaries:
            documents.append(
                f'Email on {report.date} from {summary.sender} '
                f'about "{summary.subject}": {summary.summary}'
            )
            ids.append(f"{report.date}_summary_{summary.email_id}")
            metadatas.append({
                "date": report.date,
                "type": "summary",
                "sender": summary.sender,
                "subject": summary.subject,
            })

        documents.append(
            f"Daily email stats for {report.date}: "
            f"{report.urgent_count} urgent, "
            f"{report.important_count} important, "
            f"{report.follow_up_count} requiring follow-up, "
            f"{report.ignored_count} ignored."
        )
        ids.append(f"{report.date}_stats")
        metadatas.append({"date": report.date, "type": "stats"})

        self._collection.upsert(documents=documents, ids=ids, metadatas=metadatas)
        logger.info("Indexed %d chunk(s) for report %s.", len(documents), report.date)

    def index_all(self, reports: List[DailyReport]) -> None:
        for report in reports:
            self.index_report(report)
