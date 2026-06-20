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


REAL_WORLD_SAMPLE = """
<section begin=B3 />{{#invoke:football box|main
|date={{Start date|2026|6|18}}
|time=7:00&nbsp;p.m. UTC-7
|team1={{#invoke:flag|fb-rt|CAN}}
|score={{score link|2026 FIFA World Cup Group B#Canada vs Qatar|6-0}}
|team2={{#invoke:flag|fb|QAT}}
|goals1=
*Larin 16
*J. David 29, 45+3, 90+2
*Saliba 64
|goals2=
|stadium=[[BC Place]], [[Vancouver]]
|attendance=54,500
|referee=Test Ref
}}<section end=B3 />
"""


class RealWorldFormatTest(unittest.TestCase):
    """Wikipedia no siempre pone el apostrofe del minuto (ej.: '29, 45+3, 90+2' en
    vez de '29', 45+3', 90+2''), distinto entre paginas de grupo segun quien edito.
    Si el parser no tolera eso, todos los goles de esa linea quedan pegados adentro
    del nombre del jugador (ver conversacion sobre Jonathan David sin aparecer en
    el ranking de goleadores pese a tener un hat-trick)."""

    def test_multi_goal_line_without_apostrophe(self):
        matches = parse_group_matches("B", REAL_WORLD_SAMPLE)
        self.assertEqual(len(matches), 1)
        david_goals = [g for g in matches[0].goals1 if g.player == "J. David"]
        self.assertEqual(len(david_goals), 3, "Jonathan David deberia tener 3 goles separados, no 1 pegado")
        self.assertEqual([g.minute for g in david_goals], ["29", "45+3", "90+2"])

    def test_single_goal_line_without_apostrophe(self):
        matches = parse_group_matches("B", REAL_WORLD_SAMPLE)
        larin_goals = [g for g in matches[0].goals1 if g.player == "Larin"]
        self.assertEqual(len(larin_goals), 1)
        self.assertEqual(larin_goals[0].minute, "16")

if __name__ == "__main__":
    unittest.main()
