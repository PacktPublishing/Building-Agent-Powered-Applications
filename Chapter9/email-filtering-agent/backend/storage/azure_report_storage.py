import json
from datetime import datetime, timedelta, timezone
from typing import List, Optional

from azure.core.exceptions import ResourceNotFoundError
from azure.storage.blob import BlobServiceClient

from backend.contracts.report import DailyReport
from backend.storage.report_storage import ReportStorage


class AzureReportStorage(ReportStorage):
    """Azure Blob Storage backend for daily email reports.

    Each day's report is stored as a JSON blob named YYYY-MM-DD.json inside
    the configured container.  Old blobs beyond the retention window are pruned
    via cleanup_old_reports().
    """

    def __init__(self, connection_string: str, container_name: str):
        self._container = (
            BlobServiceClient.from_connection_string(connection_string)
            .get_container_client(container_name)
        )
        if not self._container.exists():
            self._container.create_container()

    def _blob_name(self, date: str) -> str:
        return f"{date}.json"

    def get_or_create_report(self, date: Optional[str] = None) -> DailyReport:
        date = date or self._today()
        try:
            data = self._container.get_blob_client(self._blob_name(date)).download_blob().readall()
            return DailyReport(**json.loads(data))
        except ResourceNotFoundError:
            return DailyReport(date=date)

    def save_report(self, report: DailyReport) -> None:
        blob = self._container.get_blob_client(self._blob_name(report.date))
        blob.upload_blob(
            json.dumps(report.model_dump(mode="json"), indent=2, default=str),
            overwrite=True,
            content_settings={"content_type": "application/json"},
        )

    def get_reports_range(self, days: int = 30) -> List[DailyReport]:
        """Return up to *days* most-recent reports (newest first)."""
        reports: List[DailyReport] = []
        today = datetime.now(timezone.utc)
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            try:
                data = (
                    self._container.get_blob_client(self._blob_name(date))
                    .download_blob()
                    .readall()
                )
                reports.append(DailyReport(**json.loads(data)))
            except ResourceNotFoundError:
                pass
        return reports

    def cleanup_old_reports(self, retention_days: int = 180) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = 0
        for blob in self._container.list_blobs():
            if not blob.name.endswith(".json"):
                continue
            stem = blob.name[:-5]  # strip .json
            try:
                blob_date = datetime.strptime(stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if blob_date < cutoff:
                    self._container.delete_blob(blob.name)
                    deleted += 1
            except ValueError:
                pass
        return deleted
