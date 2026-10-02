"""Intake agent. Loads Other comments and hands them to Review in batches. No model calls."""

from dataclasses import dataclass, field

from backend.workflows.ingest import IngestError, RawReturn, parse_csv

BATCH_SIZE = 8


@dataclass
class CommentBatch:
    number: int
    rows: list[RawReturn]


@dataclass
class IntakeResult:
    rows: list[RawReturn] = field(default_factory=list)
    batches: list[CommentBatch] = field(default_factory=list)
    dropped: list[dict] = field(default_factory=list)
    batch_size: int = BATCH_SIZE

    @property
    def loaded(self) -> int:
        return len(self.rows)


def load_and_batch(payload: bytes | str) -> IntakeResult:
    """Read the CSV, drop rows that are not usable, then split the rest into batches."""
    report = parse_csv(payload)
    batches = [
        CommentBatch(number=index + 1, rows=report.rows[start : start + BATCH_SIZE])
        for index, start in enumerate(range(0, len(report.rows), BATCH_SIZE))
    ]
    return IntakeResult(rows=report.rows, batches=batches, dropped=report.dropped)


__all__ = ["BATCH_SIZE", "CommentBatch", "IngestError", "IntakeResult", "load_and_batch"]
