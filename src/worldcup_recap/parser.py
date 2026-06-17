from __future__ import annotations

import re

from .models import Goal, Match
from .text_utils import clean_wikitext, slugify


FIELD_RE = re.compile(r"^\|([^=]+)=(.*)$")


def parse_group_matches(group: str, wikitext: str) -> list[Match]:
    matches: list[Match] = []
    for block in _football_box_blocks(wikitext):
        fields = _parse_fields(block)
        team1 = clean_wikitext(fields.get("team1", ""))
        team2 = clean_wikitext(fields.get("team2", ""))
        date = clean_wikitext(fields.get("date", ""))
        score = clean_wikitext(fields.get("score", ""))
        if not team1 or not team2 or not date:
            continue

        match_id = f"{group}-{date}-{slugify(team1)}-{slugify(team2)}"
        matches.append(
            Match(
                match_id=match_id,
                group=group,
                date=_normalize_date(date),
                time=clean_wikitext(fields.get("time", "")),
                team1=team1,
                team2=team2,
                score=score,
                goals1=tuple(parse_goals(team1, fields.get("goals1", ""))),
                goals2=tuple(parse_goals(team2, fields.get("goals2", ""))),
                stadium=clean_wikitext(fields.get("stadium", "")),
                attendance=clean_wikitext(fields.get("attendance", "")),
                referee=clean_wikitext(fields.get("referee", "")),
            )
        )
    return matches


def parse_goals(team: str, raw: str) -> list[Goal]:
    goals: list[Goal] = []
    for line in raw.splitlines():
        line = line.strip()
        if not line.startswith("*"):
            continue
        text = clean_wikitext(line.lstrip("*").strip())
        if not text:
            continue

        minute_matches = list(re.finditer(r"(\d+(?:\+\d+)?)'", text))
        minute = minute_matches[0].group(1) if minute_matches else ""
        before_minute = text[: minute_matches[0].start()].strip() if minute_matches else text
        note = ""
        if " o.g." in text:
            note = "own goal"
        elif " pen." in text:
            note = "penalty"

        player = before_minute.replace(" o.g.", "").replace(" pen.", "").strip(" ,")
        if minute_matches:
            for match in minute_matches:
                goals.append(Goal(team=team, player=player, minute=match.group(1), note=note))
        else:
            goals.append(Goal(team=team, player=player, minute=minute, note=note))
    return goals


def _football_box_blocks(wikitext: str) -> list[str]:
    blocks: list[str] = []
    marker = "{{#invoke:football box|main"
    start = 0
    while True:
        idx = wikitext.find(marker, start)
        if idx == -1:
            break
        depth = 0
        end = idx
        while end < len(wikitext) - 1:
            pair = wikitext[end : end + 2]
            if pair == "{{":
                depth += 1
                end += 2
                continue
            if pair == "}}":
                depth -= 1
                end += 2
                if depth == 0:
                    blocks.append(wikitext[idx:end])
                    break
                continue
            end += 1
        start = end
    return blocks


def _parse_fields(block: str) -> dict[str, str]:
    fields: dict[str, list[str]] = {}
    current_key: str | None = None

    for line in block.splitlines():
        match = FIELD_RE.match(line)
        if match:
            current_key = match.group(1).strip()
            fields[current_key] = [match.group(2).strip()]
        elif current_key:
            fields[current_key].append(line.rstrip())

    return {key: "\n".join(value).strip() for key, value in fields.items()}


def _normalize_date(value: str) -> str:
    match = re.search(r"(\d{4})-(\d{1,2})-(\d{1,2})", value)
    if not match:
        return value
    year, month, day = match.groups()
    return f"{int(year):04d}-{int(month):02d}-{int(day):02d}"
