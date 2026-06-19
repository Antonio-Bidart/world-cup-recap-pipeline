from __future__ import annotations

import json
import sqlite3
from collections import Counter, defaultdict
from datetime import date

from .models import parse_score


def team_status(rows: list[sqlite3.Row], today: date | None = None) -> dict[str, dict[str, object]]:
    today = today or date.today()
    teams = sorted({row["team1"] for row in rows} | {row["team2"] for row in rows})
    status: dict[str, dict[str, object]] = {}

    for team in teams:
        future = [
            row
            for row in rows
            if team in (row["team1"], row["team2"])
            and parse_score(row["score"]) is None
            and row["match_date"] >= today.isoformat()
        ]
        future.sort(key=lambda row: (row["match_date"], row["match_time"] or ""))
        played = [row for row in rows if team in (row["team1"], row["team2"]) and parse_score(row["score"])]
        next_match = future[0] if future else None
        status[team] = {
            "played": len(played),
            "next_match": _next_match_label(team, next_match) if next_match else "Sin partido programado: eliminado o pendiente de fixture",
        }
    return status


def group_tables(rows: list[sqlite3.Row]) -> dict[str, list[dict[str, int | str]]]:
    tables: dict[str, dict[str, dict[str, int | str]]] = defaultdict(dict)
    for row in rows:
        group = row["group_name"]
        for team in (row["team1"], row["team2"]):
            tables[group].setdefault(
                team,
                {"team": team, "played": 0, "won": 0, "drawn": 0, "lost": 0, "gf": 0, "ga": 0, "gd": 0, "points": 0},
            )

        score = parse_score(row["score"])
        if score is None:
            continue
        s1, s2 = score
        t1 = tables[group][row["team1"]]
        t2 = tables[group][row["team2"]]
        t1["played"] += 1
        t2["played"] += 1
        t1["gf"] += s1
        t1["ga"] += s2
        t2["gf"] += s2
        t2["ga"] += s1
        t1["gd"] = t1["gf"] - t1["ga"]
        t2["gd"] = t2["gf"] - t2["ga"]
        if s1 > s2:
            t1["won"] += 1
            t2["lost"] += 1
            t1["points"] += 3
        elif s1 < s2:
            t2["won"] += 1
            t1["lost"] += 1
            t2["points"] += 3
        else:
            t1["drawn"] += 1
            t2["drawn"] += 1
            t1["points"] += 1
            t2["points"] += 1

    return {
        group: sorted(
            table.values(),
            key=lambda item: (-int(item["points"]), -int(item["gd"]), -int(item["gf"]), str(item["team"])),
        )
        for group, table in sorted(tables.items())
    }


def goals_for_row(row: sqlite3.Row) -> list[str]:
    payload = json.loads(row["goals_json"])
    goals = []
    for key in ("goals1", "goals2"):
        for goal in payload.get(key, []):
            note = f" ({goal['note']})" if goal.get("note") else ""
            minute = f"{goal['minute']}'" if goal.get("minute") else ""
            goals.append(f"{goal['player']} ({goal['team']}) {minute}{note}".strip())
    return goals


def goal_events_for_row(row: sqlite3.Row) -> list[dict[str, str]]:
    payload = json.loads(row["goals_json"])
    goals = []
    for key in ("goals1", "goals2"):
        goals.extend(payload.get(key, []))
    return goals


def top_scorers(rows: list[sqlite3.Row], limit: int = 10) -> list[dict[str, int | str]]:
    counts: Counter[tuple[str, str]] = Counter()
    for row in rows:
        if parse_score(row["score"]) is None:
            continue
        for goal in goal_events_for_row(row):
            if goal.get("note") == "own goal":
                continue
            player = str(goal.get("player", "")).strip()
            team = str(goal.get("team", "")).strip()
            if player:
                counts[(player, team)] += 1

    return [
        {"player": player, "team": team, "goals": goals}
        for (player, team), goals in counts.most_common(limit)
    ]


def _next_match_label(team: str, row: sqlite3.Row) -> str:
    opponent = row["team2"] if row["team1"] == team else row["team1"]
    return f"{row['match_date']} {row['match_time']} vs {opponent} ({row['group_name']})"
