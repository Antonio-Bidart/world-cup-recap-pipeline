from __future__ import annotations

import json
import time
from urllib.error import HTTPError
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

        payload = self._fetch_json(request, title)
        except json.JSONDecodeError as exc:
            raise WikiClientError(f"Wikipedia returned invalid JSON for {title}") from exc

        pages = payload.get("query", {}).get("pages", [])
        if not pages or pages[0].get("missing"):
            raise WikiClientError(f"Wikipedia page not found: {title}")

        return pages[0]["revisions"][0]["slots"]["main"]["content"]

    def _fetch_json(self, request: Request, title: str) -> dict:
        delays = [0, 3, 8, 15]
        last_error: Exception | None = None
        for delay in delays:
            if delay:
                time.sleep(delay)
            try:
                with urlopen(request, timeout=20) as response:
                    return json.loads(response.read().decode("utf-8"))
            except HTTPError as exc:
                last_error = exc
                if exc.code != 429:
                    raise WikiClientError(f"Could not fetch Wikipedia page {title}: HTTP Error {exc.code}") from exc
            except OSError as exc:
                last_error = exc
                break
            except json.JSONDecodeError as exc:
                raise WikiClientError(f"Wikipedia returned invalid JSON for {title}") from exc

        raise WikiClientError(f"Could not fetch Wikipedia page {title}: {last_error}") from last_error
