import sqlite3
import unittest

from worldcup_recap.analytics import group_tables
from worldcup_recap.database import init_db, upsert_matches, fetch_matches
from worldcup_recap.models import Match


class AnalyticsTest(unittest.TestCase):
    def test_group_table_points(self):
        connection = sqlite3.connect(":memory:")
        connection.row_factory = sqlite3.Row
        init_db(connection)
        upsert_matches(
            connection,
            [
                Match(match_id="a", group="A", date="2026-06-11", time="", team1="Mexico", team2="South Africa", score="2-1"),
                Match(match_id="b", group="A", date="2026-06-12", time="", team1="Czechia", team2="Korea Republic", score="0-0"),
            ],
        )

        tables = group_tables(fetch_matches(connection))

        self.assertEqual(tables["A"][0]["team"], "Mexico")
        self.assertEqual(tables["A"][0]["points"], 3)


if __name__ == "__main__":
    unittest.main()

