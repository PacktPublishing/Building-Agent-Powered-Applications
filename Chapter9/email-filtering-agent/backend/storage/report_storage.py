from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import List, Optional

from backend.contracts.report import DailyReport, EmailSummary


class ReportStorage(ABC):
    """Abstract base for report storage backends."""

    def _today(self) -> str:
        return datetime.now(timezone.utc).strftime("%Y-%m-%d")

    @abstractmethod
    def get_or_create_report(self, date: Optional[str] = None) -> DailyReport: ...

    @abstractmethod
    def save_report(self, report: DailyReport) -> None: ...

    @abstractmethod
    def get_reports_range(self, days: int = 30) -> List[DailyReport]: ...

    @abstractmethod
    def cleanup_old_reports(self, retention_days: int = 180) -> int: ...

    # ── Template methods (shared business logic) ──────────────────────────────

    def add_summary(self, summary: EmailSummary, date: Optional[str] = None) -> DailyReport:
        report = self.get_or_create_report(date)
        report.summaries.append(summary)
        report.important_count += 1
        self.save_report(report)
        return report

    def increment_counter(self, category: str, date: Optional[str] = None) -> None:
        report = self.get_or_create_report(date)
        if category == "urgent":
            report.urgent_count += 1
        elif category == "ignore":
            report.ignored_count += 1
        elif category == "requires_follow_up":
            report.follow_up_count += 1
        self.save_report(report)

    def finalize_report(self, date: Optional[str] = None) -> DailyReport:
        report = self.get_or_create_report(date)
        report.finalized = True
        report.finalized_at = datetime.now(timezone.utc)
        self.save_report(report)
        return report
