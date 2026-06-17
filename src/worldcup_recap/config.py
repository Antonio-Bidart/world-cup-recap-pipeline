from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class Settings:
    wikipedia_api_url: str = "https://en.wikipedia.org/w/api.php"
    group_title_template: str = "2026 FIFA World Cup Group {group}"
    groups: tuple[str, ...] = tuple("ABCDEFGHIJKL")
    default_db_path: Path = Path("data/worldcup.sqlite")
    default_site_dir: Path = Path("site")
    default_log_path: Path = Path("logs/runs.ndjson")
    github_models_endpoint: str = "https://models.github.ai/inference/chat/completions"
    github_models_model: str = "openai/gpt-4o-mini"


SETTINGS = Settings()

