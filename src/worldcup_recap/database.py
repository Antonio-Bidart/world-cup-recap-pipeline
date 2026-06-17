from __future__ import annotations

import json
import sqlite3
from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

from .models import Match


SCHEMA = """
CREATE TABLE IF NOT EXISTS matches (
    match_id TEXT PRIMARY KEY,
    group_name TEXT NOT NULL,
    match_date TEXT NOT NULL,
    match_time TEXT,
    team1 TEXT NOT NULL,
    team2 TEXT NOT NULL,
    score TEXT NOT NULL,
    stadium TEXT,
    attendance TEXT,
    referee TEXT,
    goals_json TEXT NOT NULL,
    payload_hash TEXT NOT NULL,
    inserted_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);

CREATE TABLE IF NOT EXISTS recaps (
    match_id TEXT PRIMARY KEY,
    provider TEXT NOT NULL,
    summary TEXT NOT NULL,
    generated_at TEXT NOT NULL,
    FOREIGN KEY(match_id) REFERENCES matches(match_id)
);

CREATE TABLE IF NOT EXISTS runs (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    run_id TEXT NOT NULL UNIQUE,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    status TEXT NOT NULL,
    matches_fetched INTEGER NOT NULL DEFAULT 0,
    matches_inserted INTEGER NOT NULL DEFAULT 0,
    matches_updated INTEGER NOT NULL DEFAULT 0,
    matches_skipped INTEGER NOT NULL DEFAULT 0,
    recaps_generated INTEGER NOT NULL DEFAULT 0,
    error_message TEXT
);
"""


def connect(db_path: Path) -> sqlite3.Connection:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    connection = sqlite3.connect(db_path)
    connection.row_factory = sqlite3.Row
    return connection


def init_db(connection: sqlite3.Connection) -> None:
    connection.executescript(SCHEMA)
    connection.commit()


def start_run(connection: sqlite3.Connection, run_id: str) -> None:
    connection.execute(
        "INSERT INTO runs (run_id, started_at, status) VALUES (?, ?, ?)",
        (run_id, datetime.now(timezone.utc).isoformat(), "running"),
    )
    connection.commit()


def finish_run(
    connection: sqlite3.Connection,
    run_id: str,
    status: str,
    counts: dict[str, int],
    error_message: str | None = None,
) -> None:
    connection.execute(
        """
        UPDATE runs
        SET finished_at = ?,
            status = ?,
            matches_fetched = ?,
            matches_inserted = ?,
            matches_updated = ?,
            matches_skipped = ?,
            recaps_generated = ?,
            error_message = ?
        WHERE run_id = ?
        """,
        (
            datetime.now(timezone.utc).isoformat(),
            status,
            counts.get("fetched", 0),
            counts.get("inserted", 0),
            counts.get("updated", 0),
            counts.get("skipped", 0),
            counts.get("recaps", 0),
            error_message,
            run_id,
        ),
    )
    connection.commit()


def upsert_matches(connection: sqlite3.Connection, matches: Iterable[Match]) -> dict[str, int]:
    counts = {"fetched": 0, "inserted": 0, "updated": 0, "skipped": 0}
    now = datetime.now(timezone.utc).isoformat()

    with connection:
        for match in matches:
            counts["fetched"] += 1
            current = connection.execute(
                "SELECT payload_hash FROM matches WHERE match_id = ?",
                (match.match_id,),
            ).fetchone()
            if current is None:
                _insert_match(connection, match, now)
                counts["inserted"] += 1
            elif current["payload_hash"] != match.payload_hash:
                _update_match(connection, match, now)
                counts["updated"] += 1
            else:
                counts["skipped"] += 1
    return counts


def save_recap(connection: sqlite3.Connection, match_id: str, summary: str, provider: str) -> None:
    connection.execute(
        """
        INSERT INTO recaps (match_id, provider, summary, generated_at)
        VALUES (?, ?, ?, ?)
        ON CONFLICT(match_id) DO UPDATE SET
            provider = excluded.provider,
            summary = excluded.summary,
            generated_at = excluded.generated_at
        """,
        (match_id, provider, summary, datetime.now(timezone.utc).isoformat()),
    )
    connection.commit()


def fetch_matches(connection: sqlite3.Connection) -> list[sqlite3.Row]:
    return list(
        connection.execute(
            """
            SELECT m.*, r.summary, r.provider
            FROM matches m
            LEFT JOIN recaps r ON r.match_id = m.match_id
            ORDER BY m.match_date ASC, m.match_time ASC, m.team1 ASC
            """
        )
    )


def _goals_payload(match: Match) -> str:
    return json.dumps(
        {
            "goals1": [asdict(goal) for goal in match.goals1],
            "goals2": [asdict(goal) for goal in match.goals2],
        },
        sort_keys=True,
        ensure_ascii=True,
    )


def _insert_match(connection: sqlite3.Connection, match: Match, now: str) -> None:
    connection.execute(
        """
        INSERT INTO matches (
            match_id, group_name, match_date, match_time, team1, team2, score,
            stadium, attendance, referee, goals_json, payload_hash, inserted_at, updated_at
        )
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            match.match_id,
            match.group,
            match.date,
            match.time,
            match.team1,
            match.team2,
            match.score,
            match.stadium,
            match.attendance,
            match.referee,
            _goals_payload(match),
            match.payload_hash,
            now,
            now,
        ),
    )


def _update_match(connection: sqlite3.Connection, match: Match, now: str) -> None:
    connection.execute(
        """
        UPDATE matches
        SET group_name = ?,
            match_date = ?,
            match_time = ?,
            team1 = ?,
            team2 = ?,
            score = ?,
            stadium = ?,
            attendance = ?,
            referee = ?,
            goals_json = ?,
            payload_hash = ?,
            updated_at = ?
        WHERE match_id = ?
        """,
        (
            match.group,
            match.date,
            match.time,
            match.team1,
            match.team2,
            match.score,
            match.stadium,
            match.attendance,
            match.referee,
            _goals_payload(match),
            match.payload_hash,
            now,
            match.match_id,
        ),
    )

