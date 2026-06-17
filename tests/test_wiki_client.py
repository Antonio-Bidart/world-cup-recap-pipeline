import unittest
from unittest.mock import patch

from worldcup_recap.wiki_client import WikiClient


class WikiClientTest(unittest.TestCase):
    def test_fetch_all_group_wikitexts_maps_titles_to_groups(self):
        payload = {
            "query": {
                "pages": [
                    {
                        "title": "2026 FIFA World Cup Group A",
                        "revisions": [{"slots": {"main": {"content": "group-a-text"}}}],
                    },
                    {
                        "title": "2026 FIFA World Cup Group B",
                        "revisions": [{"slots": {"main": {"content": "group-b-text"}}}],
                    },
                ]
            }
        }

        client = WikiClient()
        with patch.object(client, "_fetch_json", return_value=payload):
            result = client.fetch_all_group_wikitexts(("A", "B"))

        self.assertEqual(result, {"A": "group-a-text", "B": "group-b-text"})


if __name__ == "__main__":
    unittest.main()

