"""SQLite store. Counts stay in code."""

import sqlite3
from pathlib import Path

from backend.agents.intake import BATCH_SIZE
from backend.schemas.taxonomy import AUTO_APPROVE_AT, LABEL_TITLES, suggested_action

# Catalogue areas. Actionable ones can change a size chart, image, vendor note, or copy.
AREAS = (
    ("Fit and size", ("fit_too_small", "fit_too_large", "fit_too_tight", "fit_too_loose", "size_chart_mismatch"), True),
    ("Quality", ("quality_fabric", "quality_stitching_or_damage"), True),
    ("Colour", ("colour_image_mismatch",), True),
    ("Copy and look", ("description_or_look_mismatch",), True),
    ("Not enough to act", ("insufficient_evidence",), False),
    ("Not a product issue", ("not_a_product_issue",), False),
)

ROOT = Path(__file__).resolve().parents[1]
DB_PATH = ROOT / "data" / "dhaga.sqlite"

SCHEMA = """
CREATE TABLE IF NOT EXISTS events (
  id TEXT PRIMARY KEY,
  return_id TEXT UNIQUE,
  sku TEXT NOT NULL,
  category TEXT,
  vendor TEXT,
  size TEXT,
  return_reason TEXT,
  other_text TEXT NOT NULL,
  status TEXT NOT NULL,
  label TEXT,
  confidence REAL,
  evidence_span TEXT,
  short_reason TEXT,
  final_label TEXT,
  auto_approved INTEGER NOT NULL DEFAULT 0
);
CREATE TABLE IF NOT EXISTS pipeline (
  id INTEGER PRIMARY KEY CHECK (id = 1),
  loaded INTEGER NOT NULL,
  batches INTEGER NOT NULL,
  batch_size INTEGER NOT NULL,
  auto_approved INTEGER NOT NULL,
  sent_to_neha INTEGER NOT NULL,
  source TEXT NOT NULL
);
"""


def connect() -> sqlite3.Connection:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.executescript(SCHEMA)
    return db


def _public(row: sqlite3.Row) -> dict:
    item = dict(row)
    label = item.get("final_label") or item.get("label")
    item["display_label"] = LABEL_TITLES.get(label or "", label)
    item["suggested_action"] = suggested_action(label)
    if item.get("confidence") is None:
        item["confidence_pct"] = None
    else:
        item["confidence_pct"] = round(float(item["confidence"]) * 100)
    return item


def seed_if_empty() -> None:
    db = connect()
    count = db.execute("SELECT COUNT(*) AS n FROM events").fetchone()["n"]
    if count:
        db.close()
        return
    rows = _sample_rows()
    db.executemany(
        """
        INSERT INTO events (
          id, return_id, sku, category, vendor, size, return_reason, other_text,
          status, label, confidence, evidence_span, short_reason, final_label, auto_approved
        ) VALUES (
          :id, :return_id, :sku, :category, :vendor, :size, :return_reason, :other_text,
          :status, :label, :confidence, :evidence_span, :short_reason, :final_label, :auto_approved
        )
        """,
        rows,
    )
    db.commit()
    db.close()


def _agents(loaded: int, batches: int | None, auto_approved: int, sent_to_neha: int, source: str) -> dict:
    threshold = int(AUTO_APPROVE_AT * 100)
    return {
        "intake": {
            "name": "Intake",
            "loaded": loaded,
            "batches": batches,
            "batch_size": BATCH_SIZE,
            "detail": (
                f"Loaded {loaded} Other comments and split them into {batches} batches of {BATCH_SIZE}."
                if batches
                else f"{loaded} comments are on the dashboard. Upload a CSV to batch them."
            ),
        },
        "review": {
            "name": "Review",
            "auto_approved": auto_approved,
            "sent_to_neha": sent_to_neha,
            "threshold": threshold,
            "detail": (
                f"Filed {auto_approved} at {threshold}% or above. "
                f"Sent {sent_to_neha} to Neha because they are under {threshold}% or have no score."
            ),
        },
        "source": source,
    }


def _pct(part: int, whole: int) -> int:
    if whole <= 0:
        return 0
    return round(100 * part / whole)


def _label_of(row: sqlite3.Row) -> str | None:
    return row["final_label"] or row["label"]


def insights(rows: list[sqlite3.Row]) -> dict:
    """What this file now shows. Shares are this file, not the case-study mix."""
    accepted = [row for row in rows if row["status"] == "accepted"]
    review = [row for row in rows if row["status"] == "review"]
    counted = len(accepted)
    total = len(rows)
    no_score = sum(1 for row in review if row["confidence"] is None)
    low = len(review) - no_score

    areas = []
    for title, labels, actionable in AREAS:
        matched = [row for row in accepted if _label_of(row) in labels]
        lead_label = None
        if matched:
            tally: dict[str, int] = {}
            for row in matched:
                label = _label_of(row) or ""
                tally[label] = tally.get(label, 0) + 1
            lead_label = max(tally, key=tally.get)
        areas.append(
            {
                "title": title,
                "count": len(matched),
                "share_pct": _pct(len(matched), counted),
                "actionable": actionable,
                "note": suggested_action(lead_label) if lead_label else "",
            }
        )
    areas.sort(key=lambda item: item["count"], reverse=True)

    actionable = [item for item in areas if item["actionable"] and item["count"]]
    focus = None
    if actionable:
        lead = actionable[0]
        lead_labels = next(labels for title, labels, _flag in AREAS if title == lead["title"])
        cells: dict[tuple, int] = {}
        for row in accepted:
            label = _label_of(row)
            if label not in lead_labels:
                continue
            key = (row["sku"], row["vendor"], row["size"], label)
            cells[key] = cells.get(key, 0) + 1
        sku, vendor, size, label = max(cells, key=cells.get)
        focus = {
            "title": lead["title"],
            "count": lead["count"],
            "share_pct": lead["share_pct"],
            "sku": sku,
            "vendor": vendor,
            "size": size,
            "label": LABEL_TITLES.get(label, label),
            "cluster": cells[(sku, vendor, size, label)],
            "action": suggested_action(label),
        }

    products: list[dict] = []
    by_sku: dict[str, list[sqlite3.Row]] = {}
    for row in accepted:
        by_sku.setdefault(row["sku"], []).append(row)
    for sku, items in by_sku.items():
        tally: dict[str, int] = {}
        for row in items:
            label = _label_of(row) or ""
            tally[label] = tally.get(label, 0) + 1
        top = max(tally, key=tally.get)
        products.append(
            {
                "sku": sku,
                "vendor": items[0]["vendor"],
                "count": len(items),
                "share_pct": _pct(len(items), counted),
                "top_title": LABEL_TITLES.get(top, top),
            }
        )
    products.sort(key=lambda item: item["count"], reverse=True)

    sku_board: list[dict] = []
    board: dict[str, dict] = {}
    for row in rows:
        if row["status"] == "dismissed":
            continue
        item = board.setdefault(
            row["sku"],
            {"sku": row["sku"], "vendor": row["vendor"], "auto_approved": 0, "open": 0, "counted": 0},
        )
        if row["status"] == "review":
            item["open"] += 1
        elif row["status"] == "accepted":
            item["counted"] += 1
            if row["auto_approved"]:
                item["auto_approved"] += 1
    sku_board = sorted(board.values(), key=lambda item: (item["open"], item["counted"]), reverse=True)

    attention = []
    for row in review:
        if row["confidence"] is None:
            why = "No score. Never auto-approved."
        else:
            why = f"{round(float(row['confidence']) * 100)}% — under 75%, so Neha decides."
        attention.append(
            {
                "sku": row["sku"],
                "size": row["size"],
                "vendor": row["vendor"],
                "text": row["other_text"],
                "why": why,
            }
        )

    leave = sum(item["count"] for item in areas if not item["actionable"])
    if total == 0:
        headline = "Upload a file to see what the agents changed."
    elif counted == 0:
        headline = f"Intake has {total} comments. None are counted yet. {len(review)} are still with Neha."
    else:
        headline = (
            f"These comments were only “Other.” "
            f"Review has filed {counted} of {total} ({_pct(counted, total)}%). "
            f"{len(review)} of {total} ({_pct(len(review), total)}%) are still with Neha."
        )

    return {
        "headline": headline,
        "counted": counted,
        "counted_pct": _pct(counted, total),
        "still_with_neha": len(review),
        "still_pct": _pct(len(review), total),
        "low_confidence": low,
        "no_score": no_score,
        "leave_alone": leave,
        "leave_pct": _pct(leave, counted),
        "areas": areas,
        "products": products,
        "sku_board": sku_board,
        "attention": attention,
        "focus": focus,
        "limit": (
            "Shares are this file only. The brief’s 31% return rate and 44% Other mix are not recomputed here. "
            "No rupee saving is shown until Dhaga gives a cost per product return."
        ),
    }


def save_pipeline(loaded: int, batches: int, auto_approved: int, sent_to_neha: int) -> None:
    db = connect()
    db.execute(
        """
        INSERT INTO pipeline (id, loaded, batches, batch_size, auto_approved, sent_to_neha, source)
        VALUES (1, ?, ?, ?, ?, ?, 'upload')
        ON CONFLICT(id) DO UPDATE SET
          loaded = excluded.loaded,
          batches = excluded.batches,
          batch_size = excluded.batch_size,
          auto_approved = excluded.auto_approved,
          sent_to_neha = excluded.sent_to_neha,
          source = excluded.source
        """,
        (loaded, batches, BATCH_SIZE, auto_approved, sent_to_neha),
    )
    db.commit()
    db.close()


def dashboard() -> dict:
    db = connect()
    rows = db.execute("SELECT * FROM events").fetchall()
    pipeline = db.execute("SELECT * FROM pipeline WHERE id = 1").fetchone()
    db.close()
    accepted = [row for row in rows if row["status"] == "accepted"]
    review = [row for row in rows if row["status"] == "review"]
    dismissed = [row for row in rows if row["status"] == "dismissed"]
    counts: dict[str, int] = {}
    for row in accepted:
        label = row["final_label"] or row["label"]
        counts[label] = counts.get(label, 0) + 1
    ranked = sorted(counts.items(), key=lambda item: item[1], reverse=True)
    auto = sum(1 for row in rows if row["auto_approved"])
    if pipeline:
        agents = _agents(
            pipeline["loaded"],
            pipeline["batches"],
            pipeline["auto_approved"],
            pipeline["sent_to_neha"],
            pipeline["source"],
        )
    else:
        agents = _agents(len(rows), None, auto, len(review), "sample")
    return {
        "total": len(rows),
        "accepted": len(accepted),
        "in_review": len(review),
        "dismissed": len(dismissed),
        "labels": [
            {"label": label, "title": LABEL_TITLES.get(label, label), "count": count}
            for label, count in ranked
        ],
        "skus": sorted({row["sku"] for row in accepted}),
        "sample_banner": "Sample file, not the case-study mix. The brief says 44% of returns are Other. It does not say how that bucket splits.",
        "agents": agents,
        "insights": insights(rows),
    }


def sku_detail(sku: str) -> dict:
    db = connect()
    rows = db.execute(
        "SELECT * FROM events WHERE sku = ? AND status = 'accepted' ORDER BY id",
        (sku,),
    ).fetchall()
    db.close()
    if not rows:
        return {"sku": sku, "vendor": None, "top_label": None, "top_title": None, "action": None, "sizes": [], "quotes": []}
    public = [_public(row) for row in rows]
    counts: dict[str, int] = {}
    sizes: dict[str, int] = {}
    for row in public:
        label = row["final_label"] or row["label"]
        counts[label] = counts.get(label, 0) + 1
        sizes[row["size"]] = sizes.get(row["size"], 0) + 1
    top = max(counts, key=counts.get)
    return {
        "sku": sku,
        "vendor": public[0]["vendor"],
        "top_label": top,
        "top_title": LABEL_TITLES.get(top, top),
        "action": suggested_action(top),
        "sizes": [{"size": size, "count": count} for size, count in sizes.items()],
        "quotes": [
            {
                "text": row["other_text"],
                "label": row["display_label"],
                "confidence_pct": row["confidence_pct"],
                "auto_approved": bool(row["auto_approved"]),
            }
            for row in public[:6]
        ],
    }


def review_queue() -> list[dict]:
    db = connect()
    rows = db.execute("SELECT * FROM events WHERE status = 'review' ORDER BY id").fetchall()
    db.close()
    return [_public(row) for row in rows]


def decide(event_id: str, action: str, label: str | None = None) -> dict | None:
    db = connect()
    row = db.execute("SELECT * FROM events WHERE id = ?", (event_id,)).fetchone()
    if row is None or row["status"] != "review":
        db.close()
        return None
    if action == "dismiss":
        db.execute("UPDATE events SET status = 'dismissed' WHERE id = ?", (event_id,))
    elif action == "approve":
        final = row["label"]
        if not final:
            db.close()
            raise ValueError("Choose a label and save it. This row has no score.")
        db.execute(
            "UPDATE events SET status = 'accepted', final_label = ?, auto_approved = 0 WHERE id = ?",
            (final, event_id),
        )
    elif action == "edit":
        if label not in LABEL_TITLES:
            db.close()
            raise ValueError("That label is not in the taxonomy.")
        db.execute(
            """
            UPDATE events
            SET status = 'accepted', label = ?, final_label = ?, auto_approved = 0
            WHERE id = ?
            """,
            (label, label, event_id),
        )
    else:
        db.close()
        raise ValueError("Unknown action.")
    db.commit()
    db.close()
    return {"ok": True}


def replace_with_run(records: list[dict]) -> None:
    """A new upload replaces the working set so the dashboard matches this file."""
    db = connect()
    db.execute("DELETE FROM events")
    if records:
        db.executemany(
            """
            INSERT INTO events (
              id, return_id, sku, category, vendor, size, return_reason, other_text,
              status, label, confidence, evidence_span, short_reason, final_label, auto_approved
            ) VALUES (
              :id, :return_id, :sku, :category, :vendor, :size, :return_reason, :other_text,
              :status, :label, :confidence, :evidence_span, :short_reason, :final_label, :auto_approved
            )
            """,
            records,
        )
    db.commit()
    db.close()


def _row(
    index: int,
    sku: str,
    vendor: str,
    size: str,
    text: str,
    status: str,
    label: str | None,
    confidence: float | None,
    reason: str,
    auto: bool,
) -> dict:
    final = label if status == "accepted" else None
    return {
        "id": f"s{index:03d}",
        "return_id": f"R{index:03d}",
        "sku": sku,
        "category": "Womenswear",
        "vendor": vendor,
        "size": size,
        "return_reason": "Other",
        "other_text": text,
        "status": status,
        "label": label,
        "confidence": confidence,
        "evidence_span": text if label else None,
        "short_reason": reason,
        "final_label": final,
        "auto_approved": 1 if auto else 0,
    }


def _sample_rows() -> list[dict]:
    """Synthetic Hinglish rows. Clear comments are already auto-approved at 75% or above."""
    accepted = [
        ("KURTI123", "Jaipur Vendor 14", "M", "shrit but chota h", "fit_too_small", 0.91, "Size is small."),
        ("KURTI123", "Jaipur Vendor 14", "M", "size expected se chota", "fit_too_small", 0.93, "Smaller than expected."),
        ("KURTI123", "Jaipur Vendor 14", "M", "M bahut chota h", "fit_too_small", 0.94, "Size M is very small."),
        ("KURTI123", "Jaipur Vendor 14", "L", "kurti achi h but L bhi chota", "fit_too_small", 0.86, "Even L is small."),
        ("KURTI123", "Jaipur Vendor 14", "L", "shoulder bahut tight", "fit_too_tight", 0.92, "Shoulder is tight."),
        ("KURTI123", "Jaipur Vendor 14", "XL", "bahut loose h", "fit_too_loose", 0.90, "Too loose."),
        ("KURTI123", "Jaipur Vendor 14", "L", "size bada hai", "fit_too_large", 0.89, "Size is large."),
        ("SHIRT440", "Jaipur Vendor 3", "XL", "bahut bada h", "fit_too_large", 0.88, "Much too big."),
        ("KURTI991", "Tiruppur Vendor 6", "M", "chart galat hai", "size_chart_mismatch", 0.87, "Size chart is wrong."),
        ("KURTI123", "Jaipur Vendor 14", "M", "not true to size", "size_chart_mismatch", 0.84, "Not true to size."),
        ("KURTI991", "Tiruppur Vendor 6", "M", "colour photo jaisa nhi hai", "colour_image_mismatch", 0.93, "Colour does not match the photo."),
        ("KURTI991", "Tiruppur Vendor 6", "M", "photo me navy tha ye black h", "colour_image_mismatch", 0.91, "Photo was navy, item is black."),
        ("KURTI991", "Tiruppur Vendor 6", "L", "kapda transparent hai", "quality_fabric", 0.90, "Fabric is transparent."),
        ("SHIRT440", "Jaipur Vendor 3", "M", "cloth patla h", "quality_fabric", 0.86, "Cloth is thin."),
        ("SHIRT440", "Jaipur Vendor 3", "L", "office shirt nhi lg rha", "description_or_look_mismatch", 0.81, "Does not look like the office shirt described."),
        ("DUPATTA22", "Jaipur Vendor 14", "Free", "stitch nikal gyi", "quality_stitching_or_damage", 0.92, "Stitching came out."),
        ("SHIRT440", "Jaipur Vendor 3", "M", "delivery late hui", "not_a_product_issue", 0.95, "Late delivery, not the product."),
        ("DUPATTA22", "Jaipur Vendor 14", "Free", "courier ne wrong item diya", "not_a_product_issue", 0.96, "Wrong item from the courier."),
        ("KURTI991", "Tiruppur Vendor 6", "M", "macha nai lga", "insufficient_evidence", 0.80, "Reads like didn’t like it. No fit, colour, or fabric reason."),
        ("KURTI123", "Jaipur Vendor 14", "L", "product acha nahi laga", "insufficient_evidence", 0.88, "Reads like didn’t like it. No fit, colour, or fabric reason."),
        ("SHIRT440", "Jaipur Vendor 3", "M", "I didn't like the product", "insufficient_evidence", 0.90, "Clear dislike. No product reason."),
    ]
    review = [
        ("SHIRT440", "Jaipur Vendor 3", "M", "shrit thoda alg h size", "fit_too_tight", 0.58, "Low confidence. The size direction is not clear."),
        ("KURTI991", "Tiruppur Vendor 6", "S", "ok return", None, None, "Validation failed. The model quote was not in the customer’s text, so no score was stored."),
    ]
    rows = []
    number = 1
    for sku, vendor, size, text, label, confidence, reason in accepted:
        rows.append(_row(number, sku, vendor, size, text, "accepted", label, confidence, reason, True))
        number += 1
    for sku, vendor, size, text, label, confidence, reason in review:
        rows.append(_row(number, sku, vendor, size, text, "review", label, confidence, reason, False))
        number += 1
    return rows
