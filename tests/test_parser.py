import unittest

from worldcup_recap.parser import parse_group_matches


SAMPLE = """
<section begin=J1 />{{#invoke:football box|main
|date={{Start date|2026|6|16}}
|time=8:00&nbsp;p.m. [[UTC−05:00|UTC−5]]
|team1={{#invoke:flag|fb-rt|ARG}}
|score={{score link|2026 FIFA World Cup Group J#Argentina vs Algeria|3–0}}
|team2={{#invoke:flag|fb|ALG}}
|goals1=
*[[Lionel Messi|Messi]] 17', 60', 76'
|goals2=
|stadium=[[Arrowhead Stadium]], [[Kansas City, Missouri|Kansas City]]
|attendance=69,045
|referee=[[Szymon Marciniak]] ([[Polish Football Association|Poland]])
}}<section end=J1 />
"""


class ParserTest(unittest.TestCase):
    def test_parse_football_box(self):
        matches = parse_group_matches("J", SAMPLE)

        self.assertEqual(len(matches), 1)
        self.assertEqual(matches[0].team1, "Argentina")
        self.assertEqual(matches[0].team2, "Algeria")
        self.assertEqual(matches[0].score, "3-0")
        self.assertEqual(matches[0].date, "2026-06-16")
        self.assertEqual(matches[0].goals1[0].player, "Messi")
        self.assertEqual(matches[0].goals1[0].minute, "17")
        self.assertEqual([goal.minute for goal in matches[0].goals1], ["17", "60", "76"])


if __name__ == "__main__":
    unittest.main()
