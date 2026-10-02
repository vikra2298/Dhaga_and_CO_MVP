"""Deterministic CSV ingest. No model calls."""

import csv
import io
from dataclasses import dataclass, field

REQUIRED = ("return_id", "sku", "category", "vendor", "size", "return_reason", "other_text")
TEXT_CAP = 1000
ROW_CAP = 500


class IngestError(Exception):
    def __init__(self, message: str):
        super().__init__(message)
        self.message = message


@dataclass
class RawReturn:
    return_id: str
    sku: str
    category: str
    vendor: str
    size: str
    return_reason: str
    other_text: str


@dataclass
class IngestReport:
    rows: list[RawReturn] = field(default_factory=list)
    dropped: list[dict] = field(default_factory=list)

    def add_drop(self, reason: str, count: int = 1) -> None:
        for item in self.dropped:
            if item["reason"] == reason:
                item["count"] += count
                return
        self.dropped.append({"reason": reason, "count": count})


def _norm_header(name: str) -> str:
    return name.strip().lower().replace(" ", "_")


def parse_csv(payload: bytes | str) -> IngestReport:
    if isinstance(payload, bytes):
        text = payload.decode("utf-8-sig", errors="replace")
    else:
        text = payload
    reader = csv.DictReader(io.StringIO(text))
    if not reader.fieldnames:
        raise IngestError("The file has no header row.")
    headers = {_norm_header(name): name for name in reader.fieldnames if name}
    missing = [column for column in REQUIRED if column not in headers]
    if missing:
        raise IngestError("Missing columns: " + ", ".join(missing))

    report = IngestReport()
    seen: set[str] = set()
    for raw in reader:
        row = {column: (raw.get(headers[column]) or "").strip() for column in REQUIRED}
        comment = row["other_text"]
        reason = row["return_reason"].casefold()
        if not comment:
            report.add_drop("Empty comment")
            continue
        if reason and reason not in {"other", "others"}:
            report.add_drop("Reason is not Other")
            continue
        if not row["return_id"] or not row["sku"]:
            report.add_drop("Missing return id or SKU")
            continue
        if row["return_id"] in seen:
            report.add_drop("Duplicate return id in this file")
            continue
        seen.add(row["return_id"])
        if len(comment) > TEXT_CAP:
            comment = comment[:TEXT_CAP]
            report.add_drop("Trimmed to 1000 characters")
        report.rows.append(
            RawReturn(
                return_id=row["return_id"],
                sku=row["sku"],
                category=row["category"],
                vendor=row["vendor"],
                size=row["size"],
                return_reason=row["return_reason"] or "Other",
                other_text=comment,
            )
        )

    if len(report.rows) > ROW_CAP:
        extra = len(report.rows) - ROW_CAP
        report.rows = report.rows[:ROW_CAP]
        report.add_drop("Over 500 rows in one run", extra)
    return report
