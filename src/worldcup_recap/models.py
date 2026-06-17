from __future__ import annotations

import hashlib
import json
from dataclasses import asdict, dataclass, field
from datetime import datetime

from .text_utils import slugify


@dataclass(frozen=True)
class Goal:
    team: str
    player: str
    minute: str
    note: str = ""


@dataclass(frozen=True)
class Match:
    match_id: str
    group: str
    date: str
    time: str
    team1: str
    team2: str
    score: str
    goals1: tuple[Goal, ...] = field(default_factory=tuple)
    goals2: tuple[Goal, ...] = field(default_factory=tuple)
    stadium: str = ""
    attendance: str = ""
    referee: str = ""

    @property
    def is_completed(self) -> bool:
        return parse_score(self.score) is not None

    @property
    def title(self) -> str:
        return f"{self.team1} vs {self.team2}"

    @property
    def slug(self) -> str:
        return f"{self.date}-{slugify(self.team1)}-vs-{slugify(self.team2)}"

    @property
    def payload_hash(self) -> str:
        encoded = json.dumps(asdict(self), sort_keys=True, ensure_ascii=True).encode("utf-8")
        return hashlib.sha256(encoded).hexdigest()


def parse_score(score: str) -> tuple[int, int] | None:
    cleaned = score.replace("–", "-").replace("—", "-").strip()
    parts = cleaned.split("-")
    if len(parts) != 2:
        return None
    try:
        return int(parts[0].strip()), int(parts[1].strip())
    except ValueError:
        return None


def parse_date(value: str) -> datetime | None:
    try:
        return datetime.strptime(value, "%Y-%m-%d")
    except ValueError:
        return None

