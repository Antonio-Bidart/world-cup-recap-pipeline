from __future__ import annotations

import csv
import html
import json
import sqlite3
from datetime import datetime
from pathlib import Path

from .analytics import goals_for_row, group_tables, team_status
from .models import parse_score


def build_site(rows: list[sqlite3.Row], site_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    _write_index(rows, site_dir / "index.html")
    _write_matches_csv(rows, site_dir / "matches.csv")
    _write_status_json(rows, site_dir / "team_status.json")


def _write_index(rows: list[sqlite3.Row], path: Path) -> None:
    completed = [row for row in rows if parse_score(row["score"]) is not None]
    upcoming = [row for row in rows if parse_score(row["score"]) is None]
    completed.sort(key=lambda row: (row["match_date"], row["match_time"] or ""), reverse=True)
    upcoming.sort(key=lambda row: (row["match_date"], row["match_time"] or ""))
    status = team_status(rows)
    tables = group_tables(rows)
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M")

    path.write_text(
        f"""<!doctype html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Mundial Recap Pipeline</title>
  <style>
    :root {{
      font-family: Arial, Helvetica, sans-serif;
      background: #f4f7f8;
      color: #15202b;
    }}
    body {{ margin: 0; }}
    header {{
      background: #063b3f;
      color: white;
      padding: 28px clamp(18px, 5vw, 56px);
      border-bottom: 5px solid #d6ad35;
    }}
    header h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 44px); }}
    header p {{ margin: 0; max-width: 920px; color: #dbe8e7; }}
    main {{ padding: 24px clamp(18px, 5vw, 56px) 44px; }}
    section {{ margin: 0 0 28px; }}
    h2 {{ margin: 0 0 14px; font-size: 22px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
      gap: 14px;
    }}
    .card {{
      background: white;
      border: 1px solid #d8e1e5;
      border-radius: 8px;
      padding: 16px;
      box-shadow: 0 1px 2px rgba(0,0,0,.04);
    }}
    .score {{ font-size: 28px; font-weight: 700; margin: 8px 0; }}
    .meta {{ color: #5b6b73; font-size: 14px; }}
    .summary {{ line-height: 1.45; }}
    table {{ width: 100%; border-collapse: collapse; background: white; border: 1px solid #d8e1e5; }}
    th, td {{ padding: 10px 12px; border-bottom: 1px solid #e5ecef; text-align: left; }}
    th {{ background: #0f766e; color: white; font-size: 13px; }}
    .links a {{ color: #064e3b; font-weight: 700; margin-right: 14px; }}
  </style>
</head>
<body>
  <header>
    <h1>Mundial Recap Pipeline</h1>
    <p>Reporte automatizado con datos abiertos, recaps generados, historial de partidos y seguimiento de proximos compromisos por seleccion. Generado: {html.escape(generated_at)}.</p>
  </header>
  <main>
    <section class="links">
      <a href="matches.csv">Descargar partidos CSV</a>
      <a href="team_status.json">Descargar estado de selecciones JSON</a>
    </section>
    <section>
      <h2>Ultimos partidos con recap</h2>
      <div class="grid">
        {''.join(_match_card(row) for row in completed[:12]) or '<p>No hay partidos finalizados todavia.</p>'}
      </div>
    </section>
    <section>
      <h2>Proximos partidos</h2>
      <div class="grid">
        {''.join(_upcoming_card(row) for row in upcoming[:12]) or '<p>No hay partidos programados.</p>'}
      </div>
    </section>
    <section>
      <h2>Estado por seleccion</h2>
      {_team_status_table(status)}
    </section>
    <section>
      <h2>Tablas por grupo</h2>
      <div class="grid">
        {''.join(_group_table(group, table) for group, table in tables.items())}
      </div>
    </section>
  </main>
</body>
</html>
""",
        encoding="utf-8",
    )


def _match_card(row: sqlite3.Row) -> str:
    goals = goals_for_row(row)
    goals_html = "<br>".join(html.escape(goal) for goal in goals) or "Sin goleadores cargados"
    summary = row["summary"] or "Recap pendiente."
    return f"""<article class="card">
      <div class="meta">Grupo {html.escape(row["group_name"])} · {html.escape(row["match_date"])} · {html.escape(row["stadium"] or "")}</div>
      <div class="score">{html.escape(row["team1"])} {html.escape(row["score"])} {html.escape(row["team2"])}</div>
      <p class="summary">{html.escape(summary)}</p>
      <p class="meta"><strong>Goleadores:</strong><br>{goals_html}</p>
    </article>"""


def _upcoming_card(row: sqlite3.Row) -> str:
    return f"""<article class="card">
      <div class="meta">Grupo {html.escape(row["group_name"])} · {html.escape(row["match_date"])} · {html.escape(row["match_time"] or "")}</div>
      <div class="score">{html.escape(row["team1"])} vs {html.escape(row["team2"])}</div>
      <p class="meta">{html.escape(row["stadium"] or "")}</p>
    </article>"""


def _team_status_table(status: dict[str, dict[str, object]]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(team)}</td><td>{data['played']}</td><td>{html.escape(str(data['next_match']))}</td></tr>"
        for team, data in sorted(status.items())
    )
    return f"<table><thead><tr><th>Seleccion</th><th>Partidos jugados</th><th>Proximo partido / estado</th></tr></thead><tbody>{rows}</tbody></table>"


def _group_table(group: str, table: list[dict[str, int | str]]) -> str:
    rows = "".join(
        f"<tr><td>{html.escape(str(row['team']))}</td><td>{row['played']}</td><td>{row['points']}</td><td>{row['gd']}</td><td>{row['gf']}</td></tr>"
        for row in table
    )
    return f"""<article class="card">
      <h3>Grupo {html.escape(group)}</h3>
      <table><thead><tr><th>Equipo</th><th>PJ</th><th>Pts</th><th>DG</th><th>GF</th></tr></thead><tbody>{rows}</tbody></table>
    </article>"""


def _write_matches_csv(rows: list[sqlite3.Row], path: Path) -> None:
    with path.open("w", newline="", encoding="utf-8") as file:
        writer = csv.writer(file)
        writer.writerow(["group", "date", "time", "team1", "team2", "score", "stadium", "goals", "summary"])
        for row in rows:
            writer.writerow(
                [
                    row["group_name"],
                    row["match_date"],
                    row["match_time"],
                    row["team1"],
                    row["team2"],
                    row["score"],
                    row["stadium"],
                    "; ".join(goals_for_row(row)),
                    row["summary"] or "",
                ]
            )


def _write_status_json(rows: list[sqlite3.Row], path: Path) -> None:
    path.write_text(json.dumps(team_status(rows), indent=2, ensure_ascii=False), encoding="utf-8")

