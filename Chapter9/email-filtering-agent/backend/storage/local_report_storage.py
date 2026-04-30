import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import List, Optional

from backend.contracts.report import DailyReport
from backend.storage.report_storage import ReportStorage


class LocalReportStorage(ReportStorage):
    """File-based persistent storage for daily email reports.

    Each day's report is stored as a JSON file named YYYY-MM-DD.json inside
    the configured reports directory.  Old reports beyond the retention window
    are pruned on startup via cleanup_old_reports().
    """

    def __init__(self, reports_dir: str):
        self.reports_dir = Path(reports_dir)
        self.reports_dir.mkdir(parents=True, exist_ok=True)

    def _report_path(self, date: str) -> Path:
        return self.reports_dir / f"{date}.json"

    def get_or_create_report(self, date: Optional[str] = None) -> DailyReport:
        date = date or self._today()
        path = self._report_path(date)
        if path.exists():
            with open(path) as f:
                return DailyReport(**json.load(f))
        return DailyReport(date=date)

    def save_report(self, report: DailyReport) -> None:
        path = self._report_path(report.date)
        with open(path, "w") as f:
            json.dump(report.model_dump(mode="json"), f, indent=2, default=str)

    def get_reports_range(self, days: int = 30) -> List[DailyReport]:
        """Return up to *days* most-recent reports (newest first)."""
        reports: List[DailyReport] = []
        today = datetime.now(timezone.utc)
        for i in range(days):
            date = (today - timedelta(days=i)).strftime("%Y-%m-%d")
            path = self._report_path(date)
            if path.exists():
                with open(path) as f:
                    reports.append(DailyReport(**json.load(f)))
        return reports

    def cleanup_old_reports(self, retention_days: int = 180) -> int:
        cutoff = datetime.now(timezone.utc) - timedelta(days=retention_days)
        deleted = 0
        for path in self.reports_dir.glob("*.json"):
            try:
                file_date = datetime.strptime(path.stem, "%Y-%m-%d").replace(tzinfo=timezone.utc)
                if file_date < cutoff:
                    path.unlink()
                    deleted += 1
            except ValueError:
                pass
        return deleted
