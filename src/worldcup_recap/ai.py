from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .analytics import goal_events_for_row, goals_for_row
from .config import SETTINGS
from .models import parse_score


def generate_summary(row) -> tuple[str, str]:
    if os.getenv("ENABLE_GITHUB_MODELS", "").lower() == "true":
        token = os.getenv("GH_MODELS_TOKEN") or os.getenv("GITHUB_TOKEN")
        if token:
            try:
                return _github_models_summary(row, token), "github-models"
            except (HTTPError, URLError, TimeoutError, KeyError, json.JSONDecodeError):
                pass
    return _local_summary(row), "local-recap-engine"


def _github_models_summary(row, token: str) -> str:
    goals = "; ".join(goals_for_row(row)) or "No goals listed yet"
    prompt = (
        "Escribi un resumen deportivo breve en espanol, factual y sin inventar datos. "
        "Usa maximo 55 palabras. Datos: "
        f"Partido {row['team1']} vs {row['team2']}, grupo {row['group_name']}, "
        f"resultado {row['score']}, estadio {row['stadium']}, goleadores: {goals}."
    )
    payload = {
        "model": SETTINGS.github_models_model,
        "messages": [
            {"role": "system", "content": "Sos un analista deportivo conciso. No inventes datos."},
            {"role": "user", "content": prompt},
        ],
        "temperature": 0.2,
        "max_tokens": 140,
    }
    request = Request(
        SETTINGS.github_models_endpoint,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    with urlopen(request, timeout=30) as response:
        data = json.loads(response.read().decode("utf-8"))
    return data["choices"][0]["message"]["content"].strip()


def _local_summary(row) -> str:
    score = parse_score(row["score"])
    if score is None:
        return f"{row['team1']} y {row['team2']} tienen partido programado por el grupo {row['group_name']}."

    s1, s2 = score
    venue = f" en {row['stadium']}" if row["stadium"] else ""
    scorer_text = _scorer_phrase(goal_events_for_row(row))
    if s1 == s2:
        opener = f"{row['team1']} y {row['team2']} igualaron {row['score']}{venue}"
        reading = "El empate reparte puntos y deja el grupo abierto para la siguiente fecha."
    else:
        winner = row["team1"] if s1 > s2 else row["team2"]
        loser = row["team2"] if s1 > s2 else row["team1"]
        margin = abs(s1 - s2)
        opener = f"{winner} supero a {loser} {row['score']}{venue}"
        if margin >= 3:
            reading = f"{winner} construyo una ventaja amplia y mejoro fuerte su diferencia de gol."
        elif margin == 2:
            reading = f"{winner} resolvio el partido con una diferencia clara y suma margen en la tabla."
        else:
            reading = f"{winner} se quedo con un triunfo corto, valioso para ordenar el grupo."

    scorers = f" En el registro de goles aparece {scorer_text}." if scorer_text else ""
    return f"{opener}. {reading}{scorers}"


def _scorer_phrase(goals: list[dict[str, str]]) -> str:
    if not goals:
        return ""
    counts: dict[tuple[str, str], int] = {}
    own_goals = 0
    for goal in goals:
        if goal.get("note") == "own goal":
            own_goals += 1
            continue
        key = (str(goal.get("player", "")), str(goal.get("team", "")))
        counts[key] = counts.get(key, 0) + 1

    parts = []
    for (player, team), count in sorted(counts.items(), key=lambda item: (-item[1], item[0][0])):
        suffix = f" x{count}" if count > 1 else ""
        parts.append(f"{player} ({team}){suffix}")
    if own_goals:
        parts.append(f"{own_goals} gol en contra")
    return ", ".join(parts[:4])
