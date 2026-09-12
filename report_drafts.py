"""Deterministic report-aligned draft forecast importer.

Drafts are intentionally stored separately from validated forecasts.  The
parser is conservative: only explicitly labelled forecast-watch statements
with a probability range are imported.
"""

import argparse
import hashlib
import html
import re
import sqlite3
import urllib.request
from datetime import datetime, timezone
from html.parser import HTMLParser
from pathlib import Path

GENERATOR_VERSION = "report-template-v1"
DEFAULT_SOURCE_URL = "https://charlieclarke787.github.io/"


class _TextParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.parts = []

    def handle_data(self, data):
        self.parts.append(data)

    def text(self):
        return "\n".join(self.parts)


def _report_text(content):
    parser = _TextParser()
    parser.feed(content)
    return re.sub(r"\s+", " ", html.unescape(parser.text())).strip()


def _probability_range(value):
    match = re.search(
        r"(?P<low>\d+(?:\.\d+)?)\s*(?:%|percent)?\s*(?:-|to|–|—)\s*"
        r"(?P<high>\d+(?:\.\d+)?)\s*(?:%|percent)",
        value,
        re.IGNORECASE,
    )
    if not match:
        match = re.search(r"\b(?P<low>0?\.\d+)\s*(?:-|to)\s*(?P<high>0?\.\d+)\b", value)
        if not match:
            return None
        low, high = float(match.group("low")), float(match.group("high"))
    else:
        low, high = float(match.group("low")) / 100, float(match.group("high")) / 100
    if not (0 <= low <= high <= 1):
        raise ValueError("probability range must be between 0 and 1")
    return low, high


def parse_report(content, source_url=DEFAULT_SOURCE_URL):
    """Return explicitly labelled forecast-watch questions and ranges."""
    text = _report_text(content)
    title_match = re.search(r"<title[^>]*>(.*?)</title>", content, re.I | re.S)
    title = re.sub(r"\s+", " ", html.unescape(title_match.group(1))).strip() if title_match else source_url
    date_match = re.search(
        r"(?:published|report date|date)\s*[:\-]\s*([A-Za-z0-9, /\-]+)",
        text,
        re.I,
    )
    report_date = date_match.group(1).strip() if date_match else None
    items = []
    statements = re.findall(
        r"(?:forecast[\s-]*watch|watch[\s-]*forecast)\s*[:\-]\s*(.*?)(?=(?:forecast[\s-]*watch|watch[\s-]*forecast)\s*[:\-]|$)",
        text,
        flags=re.I,
    )
    for statement in statements:
        probability = _probability_range(statement)
        if probability is None:
            continue
        range_match = re.search(
            r"\d+(?:\.\d+)?\s*(?:%|percent)?\s*(?:-|to|–|—)\s*\d+(?:\.\d+)?\s*(?:%|percent)"
            r"|\b0?\.\d+\s*(?:-|to)\s*0?\.\d+\b",
            statement,
            re.I,
        )
        question = statement[:range_match.start()].strip() if range_match else statement.strip()
        if question and question not in [item["question"] for item in items]:
            items.append(
                {
                    "question": question.rstrip(".?") + "?",
                    "low": probability[0],
                    "high": probability[1],
                    "report_title": title,
                    "report_date": report_date,
                    "source_url": source_url,
                }
            )
    return items


def generate_draft(item):
    """Create the same midpoint draft for the same parsed input every time."""
    low, high = float(item["low"]), float(item["high"])
    if not (0 <= low <= high <= 1):
        raise ValueError("probability bounds must satisfy 0 <= low <= high <= 1")
    probability = round((low + high) / 2, 6)
    return {
        "question": item["question"],
        "probability": probability,
        "rationale": (
            "Deterministic report-aligned draft: midpoint of the published "
            f"probability range ({low:.0%}-{high:.0%}). Requires human review."
        ),
    }


def _read_source(source):
    if source.startswith(("http://", "https://")):
        request = urllib.request.Request(source, headers={"User-Agent": "ArtemisForecasting/1.0"})
        with urllib.request.urlopen(request, timeout=20) as response:
            return response.read().decode("utf-8"), source
    path = Path(source)
    if not path.is_file():
        raise FileNotFoundError(f"report source does not exist: {source}")
    return path.read_text(encoding="utf-8"), path.resolve().as_uri()


def import_report(source, db_path="forecasts.db", assumptions="midpoint of published range"):
    content, source_url = _read_source(source)
    if not content.strip():
        raise ValueError("report is empty")
    items = parse_report(content, source_url)
    if not items:
        raise ValueError("report contains no clearly identified forecast-watch ranges")
    content_hash = hashlib.sha256(content.encode("utf-8")).hexdigest()
    retrieved_at = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(db_path)
    conn.execute(
        """CREATE TABLE IF NOT EXISTS report_snapshots (
            id INTEGER PRIMARY KEY, source_url TEXT NOT NULL, report_title TEXT,
            report_date TEXT, content_hash TEXT NOT NULL UNIQUE, generator_version TEXT NOT NULL,
            retrieved_at TEXT NOT NULL, assumptions TEXT NOT NULL)"""
    )
    conn.execute(
        """CREATE TABLE IF NOT EXISTS draft_forecasts (
            id INTEGER PRIMARY KEY, snapshot_id INTEGER NOT NULL, question TEXT NOT NULL,
            probability REAL NOT NULL CHECK(probability >= 0 AND probability <= 1),
            rationale TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'unapproved',
            reviewed_by TEXT, reviewed_at TEXT, review_notes TEXT,
            UNIQUE(snapshot_id, question), FOREIGN KEY(snapshot_id) REFERENCES report_snapshots(id))"""
    )
    snapshot = conn.execute(
        "SELECT id FROM report_snapshots WHERE content_hash = ?", (content_hash,)
    ).fetchone()
    if snapshot:
        conn.close()
        return {"snapshot_id": snapshot[0], "added": 0, "skipped": len(items)}
    first = items[0]
    cursor = conn.execute(
        """INSERT INTO report_snapshots
        (source_url, report_title, report_date, content_hash, generator_version, retrieved_at, assumptions)
        VALUES (?, ?, ?, ?, ?, ?, ?)""",
        (source_url, first["report_title"], first["report_date"], content_hash,
         GENERATOR_VERSION, retrieved_at, assumptions),
    )
    snapshot_id = cursor.lastrowid
    added = 0
    for item in items:
        draft = generate_draft(item)
        conn.execute(
            """INSERT INTO draft_forecasts
            (snapshot_id, question, probability, rationale) VALUES (?, ?, ?, ?)""",
            (snapshot_id, draft["question"], draft["probability"], draft["rationale"]),
        )
        added += 1
    conn.commit()
    conn.close()
    return {"snapshot_id": snapshot_id, "added": added, "skipped": 0}


def main():
    parser = argparse.ArgumentParser(description="Import deterministic draft forecasts from a report.")
    parser.add_argument("source", nargs="?", default=DEFAULT_SOURCE_URL, help="report URL or local HTML path")
    parser.add_argument("--db", default="forecasts.db")
    parser.add_argument("--assumptions", default="midpoint of published range")
    args = parser.parse_args()
    result = import_report(args.source, args.db, args.assumptions)
    print("Report draft import complete: {added} added, {skipped} skipped.".format(**result))


if __name__ == "__main__":
    main()
