from __future__ import annotations

import json
from urllib.parse import urlencode
from urllib.request import Request, urlopen

from .config import SETTINGS, Settings


class WikiClientError(RuntimeError):
    """Raised when Wikipedia cannot be reached or parsed."""


class WikiClient:
    def __init__(self, settings: Settings = SETTINGS) -> None:
        self.settings = settings

    def fetch_group_wikitext(self, group: str) -> str:
        title = self.settings.group_title_template.format(group=group)
        params = {
            "action": "query",
            "prop": "revisions",
            "titles": title,
            "rvslots": "main",
            "rvprop": "content",
            "format": "json",
            "formatversion": "2",
        }
        url = f"{self.settings.wikipedia_api_url}?{urlencode(params)}"
        request = Request(
            url,
            headers={
                "Accept": "application/json",
                "User-Agent": "world-cup-recap-pipeline/0.1 (portfolio automation)",
            },
        )

        try:
            with urlopen(request, timeout=20) as response:
                payload = json.loads(response.read().decode("utf-8"))
        except OSError as exc:
            raise WikiClientError(f"Could not fetch Wikipedia page {title}: {exc}") from exc
        except json.JSONDecodeError as exc:
            raise WikiClientError(f"Wikipedia returned invalid JSON for {title}") from exc

        pages = payload.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            raise WikiClientError(f"Wikipedia page not found: {title}")

        return pages[0]["revisions"][0]["slots"]["main"]["content"]

