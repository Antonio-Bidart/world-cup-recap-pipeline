from __future__ import annotations

import csv
import html
import sqlite3
from datetime import datetime
from pathlib import Path

from .analytics import goals_for_row, group_tables, top_scorers
from .models import parse_score
from .text_utils import flag_for_team


def build_site(rows: list[sqlite3.Row], site_dir: Path) -> None:
    site_dir.mkdir(parents=True, exist_ok=True)
    _write_index(rows, site_dir / "index.html")
    _write_matches_csv(rows, site_dir / "matches.csv")


def _write_index(rows: list[sqlite3.Row], path: Path) -> None:
    completed = [row for row in rows if parse_score(row["score"]) is not None]
    upcoming = [row for row in rows if parse_score(row["score"]) is None]
    completed.sort(key=lambda row: (row["match_date"], row["match_time"] or ""), reverse=True)
    upcoming.sort(key=lambda row: (row["match_date"], row["match_time"] or ""))
    tables = group_tables(rows)
    scorers = top_scorers(rows)
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
      background: #eef3f2;
      color: #132022;
    }}
    body {{ margin: 0; }}
    header {{
      background: linear-gradient(135deg, #073b3f 0%, #0f766e 58%, #d6ad35 140%);
      color: white;
      padding: 34px clamp(18px, 5vw, 60px);
    }}
    header h1 {{ margin: 0 0 8px; font-size: clamp(28px, 4vw, 44px); }}
    header p {{ margin: 0; max-width: 920px; color: #dbe8e7; }}
    main {{ padding: 26px clamp(18px, 5vw, 60px) 46px; }}
    section {{ margin: 0 0 32px; }}
    h2 {{ margin: 0 0 14px; font-size: 23px; }}
    .grid {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
      gap: 16px;
    }}
    .card {{
      background: white;
      border: 1px solid #d8e1e5;
      border-radius: 8px;
      padding: 18px;
      box-shadow: 0 10px 26px rgba(16, 24, 40, .07);
    }}
    .match-card {{ display: flex; flex-direction: column; gap: 14px; }}
    .match-meta {{ color: #5b6b73; font-size: 13px; font-weight: 700; text-transform: uppercase; }}
    .scoreline {{
      display: grid;
      grid-template-columns: 1fr auto 1fr;
      align-items: center;
      gap: 12px;
    }}
    .team {{ display: flex; align-items: center; gap: 8px; font-size: 17px; font-weight: 700; }}
    .team:last-child {{ justify-content: flex-end; text-align: right; }}
    .flag {{ font-size: 22px; line-height: 1; }}
    .score {{
      background: #102a2d;
      color: white;
      border-radius: 7px;
      min-width: 72px;
      padding: 8px 10px;
      text-align: center;
      font-size: 24px;
      font-weight: 800;
      font-variant-numeric: tabular-nums;
    }}
    .summary {{ line-height: 1.5; margin: 0; }}
    .goal-list {{ display: flex; flex-wrap: wrap; gap: 7px; margin: 0; }}
    .goal-pill {{
      background: #eef7f4;
      border: 1px solid #c8e5dc;
      border-radius: 999px;
      color: #0d5b50;
      font-size: 13px;
      padding: 6px 9px;
    }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ padding: 10px 11px; border-bottom: 1px solid #e5ecef; text-align: left; }}
    th {{ color: #63737a; font-size: 12px; text-transform: uppercase; }}
    .standings-card {{ padding: 0; overflow: hidden; }}
    .group-title {{
      margin: 0;
      padding: 14px 16px;
      background: #063b3f;
      color: white;
      font-size: 17px;
    }}
    .team-cell {{ display: flex; align-items: center; gap: 8px; font-weight: 700; }}
    .rank {{ color: #7a8a90; width: 24px; display: inline-block; }}
    .points {{ font-weight: 800; color: #063b3f; }}
    .gd-pos {{ color: #047857; font-weight: 700; }}
    .gd-neg {{ color: #b42318; font-weight: 700; }}
    .scorer-board {{
      display: grid;
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
      gap: 10px;
    }}
    .scorer {{
      background: white;
      border: 1px solid #d8e1e5;
      border-radius: 8px;
      padding: 13px 14px;
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
    }}
    .scorer-name {{ font-weight: 800; }}
    .scorer-team {{ color: #617179; font-size: 13px; }}
    .scorer-goals {{ font-size: 24px; font-weight: 900; color: #0f766e; }}
    .links a {{ color: #064e3b; font-weight: 700; margin-right: 14px; }}
  </style>
</head>
<body>
  <header>
    <h1>Mundial Recap Pipeline</h1>
    <p>Reporte automatizado con datos abiertos, recaps generados, historial de partidos, goleadores y tablas por grupo. Generado: {html.escape(generated_at)}.</p>
  </header>
  <main>
    <section class="links">
      <a href="matches.csv">Descargar partidos CSV</a>
    </section>
    <section>
      <h2>Maximos goleadores</h2>
      {_top_scorers_board(scorers)}
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
    goals_html = "".join(
        f'<span class="goal-pill">{html.escape(goal)}</span>'
        for goal in goals
    ) or '<span class="goal-pill">Sin goleadores cargados</span>'
    summary = row["summary"] or "Recap pendiente."
    return f"""<article class="card match-card">
      <div class="match-meta">Grupo {html.escape(row["group_name"])} | {html.escape(row["match_date"])} | {html.escape(row["stadium"] or "")}</div>
      <div class="scoreline">
        <div class="team"><span class="flag">{flag_for_team(row["team1"])}</span>{html.escape(row["team1"])}</div>
        <div class="score">{html.escape(row["score"])}</div>
        <div class="team">{html.escape(row["team2"])}<span class="flag">{flag_for_team(row["team2"])}</span></div>
      </div>
      <p class="summary">{html.escape(summary)}</p>
      <div class="goal-list">{goals_html}</div>
    </article>"""


def _upcoming_card(row: sqlite3.Row) -> str:
    return f"""<article class="card match-card">
      <div class="match-meta">Grupo {html.escape(row["group_name"])} | {html.escape(row["match_date"])} | {html.escape(row["match_time"] or "")}</div>
      <div class="scoreline">
        <div class="team"><span class="flag">{flag_for_team(row["team1"])}</span>{html.escape(row["team1"])}</div>
        <div class="score">vs</div>
        <div class="team">{html.escape(row["team2"])}<span class="flag">{flag_for_team(row["team2"])}</span></div>
      </div>
      <p class="summary">{html.escape(row["stadium"] or "")}</p>
    </article>"""


def _group_table(group: str, table: list[dict[str, int | str]]) -> str:
    rows = "".join(_group_row(index, row) for index, row in enumerate(table, start=1))
    return f"""<article class="card standings-card">
      <h3 class="group-title">Grupo {html.escape(group)}</h3>
      <table>
        <thead><tr><th>Equipo</th><th>PJ</th><th>G</th><th>E</th><th>P</th><th>DG</th><th>Pts</th></tr></thead>
        <tbody>{rows}</tbody>
      </table>
    </article>"""


def _group_row(index: int, row: dict[str, int | str]) -> str:
    team = str(row["team"])
    gd = int(row["gd"])
    gd_class = "gd-pos" if gd > 0 else "gd-neg" if gd < 0 else ""
    return f"""<tr>
      <td><span class="team-cell"><span class="rank">{index}</span><span class="flag">{flag_for_team(team)}</span>{html.escape(team)}</span></td>
      <td>{row['played']}</td>
      <td>{row['won']}</td>
      <td>{row['drawn']}</td>
      <td>{row['lost']}</td>
      <td class="{gd_class}">{gd:+d}</td>
      <td class="points">{row['points']}</td>
    </tr>"""


def _top_scorers_board(scorers: list[dict[str, int | str]]) -> str:
    if not scorers:
        return "<p>No hay goleadores cargados todavia.</p>"
    items = "".join(
        f"""<article class="scorer">
          <div>
            <div class="scorer-name">{html.escape(str(item["player"]))}</div>
            <div class="scorer-team">{flag_for_team(str(item["team"]))} {html.escape(str(item["team"]))}</div>
          </div>
          <div class="scorer-goals">{item["goals"]}</div>
        </article>"""
        for item in scorers[:10]
    )
    return f'<div class="scorer-board">{items}</div>'


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
