from __future__ import annotations

import json
import os
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

from .analytics import goals_for_row
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
    goals = goals_for_row(row)
    goals_text = " Goleadores: " + "; ".join(goals) + "." if goals else ""
    if score is None:
        return f"{row['team1']} y {row['team2']} tienen partido programado por el grupo {row['group_name']}."

    s1, s2 = score
    if s1 == s2:
        result = f"{row['team1']} y {row['team2']} empataron {row['score']}"
        reading = "El reparto de puntos mantiene abierta la lectura del grupo."
    else:
        winner = row["team1"] if s1 > s2 else row["team2"]
        loser = row["team2"] if s1 > s2 else row["team1"]
        margin = abs(s1 - s2)
        tone = "con autoridad" if margin >= 3 else "por margen corto" if margin == 1 else "con diferencia clara"
        result = f"{winner} vencio a {loser} {row['score']} {tone}"
        reading = "El resultado modifica la tendencia competitiva del grupo."

    return f"{result} en el grupo {row['group_name']}. {reading}{goals_text}"

