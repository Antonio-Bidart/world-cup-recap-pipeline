from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

from .ai import generate_summary
from .config import SETTINGS
from .database import connect, fetch_matches, finish_run, init_db, save_recap, start_run, upsert_matches
from .logging_utils import print_event, write_event
from .parser import parse_group_matches
from .report import build_site
from .wiki_client import WikiClient, WikiClientError


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="worldcup-recap")
    subparsers = parser.add_subparsers(dest="command")

    run = subparsers.add_parser("run", help="Fetch matches, persist data, generate recaps and build site.")
    run.add_argument("--db", type=Path, default=SETTINGS.default_db_path)
    run.add_argument("--site", type=Path, default=SETTINGS.default_site_dir)
    run.add_argument("--log", type=Path, default=SETTINGS.default_log_path)

    latest = subparsers.add_parser("latest", help="Show latest completed matches.")
    latest.add_argument("--db", type=Path, default=SETTINGS.default_db_path)

    args = parser.parse_args(argv)
    if args.command == "run":
        return run_pipeline(args)
    if args.command == "latest":
        return show_latest(args)
    parser.print_help()
    return 1


def run_pipeline(args: argparse.Namespace) -> int:
    run_id = str(uuid.uuid4())
    client = WikiClient()
    counts = {"fetched": 0, "inserted": 0, "updated": 0, "skipped": 0, "recaps": 0}
    event_base = {"run_id": run_id, "component": "worldcup_recap"}

    with connect(args.db) as connection:
        init_db(connection)
        start_run(connection, run_id)
        write_event(args.log, {**event_base, "event": "run_started"})

        try:
            matches = []
            for group in SETTINGS.groups:
                wikitext = client.fetch_group_wikitext(group)
                matches.extend(parse_group_matches(group, wikitext))

            counts.update(upsert_matches(connection, matches))
            rows = fetch_matches(connection)
            for row in rows:
                if row["summary"] is None:
                    summary, provider = generate_summary(row)
                    save_recap(connection, row["match_id"], summary, provider)
                    counts["recaps"] += 1

            rows = fetch_matches(connection)
            build_site(rows, args.site)
            finish_run(connection, run_id, "success", counts)
            event = {**event_base, "event": "run_finished", "status": "success", **counts, "site_dir": str(args.site)}
            write_event(args.log, event)
            print_event(event)
            return 0
        except (WikiClientError, ValueError) as exc:
            finish_run(connection, run_id, "failed", counts, str(exc))
            event = {**event_base, "event": "run_finished", "status": "failed", "error": str(exc)}
            write_event(args.log, event)
            print_event(event)
            return 1


def show_latest(args: argparse.Namespace) -> int:
    with connect(args.db) as connection:
        init_db(connection)
        rows = [row for row in fetch_matches(connection) if row["summary"]]

    for row in rows[-8:]:
        print(f"{row['match_date']} | {row['team1']} {row['score']} {row['team2']} | {row['summary']}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

