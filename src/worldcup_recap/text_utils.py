from __future__ import annotations

import html
import re


TEAM_CODES = {
    "ARG": "Argentina",
    "ALG": "Algeria",
    "AUS": "Australia",
    "AUT": "Austria",
    "BEL": "Belgium",
    "BIH": "Bosnia and Herzegovina",
    "BRA": "Brazil",
    "CAN": "Canada",
    "CIV": "Cote d'Ivoire",
    "CMR": "Cameroon",
    "COL": "Colombia",
    "CPV": "Cabo Verde",
    "CRC": "Costa Rica",
    "CRO": "Croatia",
    "CZE": "Czechia",
    "COD": "Congo DR",
    "CUW": "Curacao",
    "ECU": "Ecuador",
    "EGY": "Egypt",
    "ENG": "England",
    "FRA": "France",
    "GER": "Germany",
    "GHA": "Ghana",
    "HAI": "Haiti",
    "IRN": "IR Iran",
    "IRQ": "Iraq",
    "JPN": "Japan",
    "JOR": "Jordan",
    "KOR": "Korea Republic",
    "KSA": "Saudi Arabia",
    "MAR": "Morocco",
    "MEX": "Mexico",
    "NED": "Netherlands",
    "NOR": "Norway",
    "NZL": "New Zealand",
    "PAN": "Panama",
    "PAR": "Paraguay",
    "POR": "Portugal",
    "QAT": "Qatar",
    "RSA": "South Africa",
    "SCO": "Scotland",
    "SEN": "Senegal",
    "ESP": "Spain",
    "SUI": "Switzerland",
    "SWE": "Sweden",
    "TUN": "Tunisia",
    "TUR": "Turkey",
    "USA": "United States",
    "URU": "Uruguay",
    "UZB": "Uzbekistan",
}

TEAM_FLAGS = {
    "Algeria": "🇩🇿",
    "Argentina": "🇦🇷",
    "Australia": "🇦🇺",
    "Austria": "🇦🇹",
    "Belgium": "🇧🇪",
    "Bosnia and Herzegovina": "🇧🇦",
    "Brazil": "🇧🇷",
    "Cabo Verde": "🇨🇻",
    "Cameroon": "🇨🇲",
    "Canada": "🇨🇦",
    "Colombia": "🇨🇴",
    "Congo DR": "🇨🇩",
    "Costa Rica": "🇨🇷",
    "Cote d'Ivoire": "🇨🇮",
    "Croatia": "🇭🇷",
    "Curacao": "🇨🇼",
    "Czechia": "🇨🇿",
    "Ecuador": "🇪🇨",
    "Egypt": "🇪🇬",
    "England": "🏴",
    "France": "🇫🇷",
    "Germany": "🇩🇪",
    "Ghana": "🇬🇭",
    "Haiti": "🇭🇹",
    "IR Iran": "🇮🇷",
    "Iraq": "🇮🇶",
    "Japan": "🇯🇵",
    "Jordan": "🇯🇴",
    "Korea Republic": "🇰🇷",
    "Mexico": "🇲🇽",
    "Morocco": "🇲🇦",
    "Netherlands": "🇳🇱",
    "New Zealand": "🇳🇿",
    "Norway": "🇳🇴",
    "Panama": "🇵🇦",
    "Paraguay": "🇵🇾",
    "Portugal": "🇵🇹",
    "Qatar": "🇶🇦",
    "Saudi Arabia": "🇸🇦",
    "Scotland": "🏴",
    "Senegal": "🇸🇳",
    "South Africa": "🇿🇦",
    "Spain": "🇪🇸",
    "Sweden": "🇸🇪",
    "Switzerland": "🇨🇭",
    "Tunisia": "🇹🇳",
    "Turkey": "🇹🇷",
    "United States": "🇺🇸",
    "Uruguay": "🇺🇾",
    "Uzbekistan": "🇺🇿",
}


def clean_wikitext(value: str) -> str:
    value = html.unescape(value or "")
    value = re.sub(r"<ref[^>]*>.*?</ref>", "", value, flags=re.DOTALL)
    value = re.sub(r"<ref[^/]*/>", "", value)
    value = re.sub(r"<!--.*?-->", "", value, flags=re.DOTALL)
    value = re.sub(r"\{\{efn[^}]*\}\}", "", value)
    value = re.sub(r"\{\{nbsp\}\}", " ", value)
    value = re.sub(r"&nbsp;", " ", value)
    value = _replace_flag_templates(value)
    value = _replace_score_link(value)
    value = re.sub(r"\[\[([^|\]]+)\|([^|\]]+)\]\]", r"\2", value)
    value = re.sub(r"\[\[([^\]]+)\]\]", r"\1", value)
    value = re.sub(r"\{\{Start date\|(\d{4})\|(\d{1,2})\|(\d{1,2})\}\}", r"\1-\2-\3", value)
    value = re.sub(r"\{\{[^{}]*\}\}", "", value)
    value = re.sub(r"'''?", "", value)
    value = re.sub(r"<[^>]+>", "", value)
    value = value.replace("–", "-").replace("—", "-")
    value = re.sub(r"\s+", " ", value).strip()
    return value


def slugify(value: str) -> str:
    value = clean_wikitext(value).lower()
    value = re.sub(r"[^a-z0-9]+", "-", value)
    return value.strip("-")


def flag_for_team(team: str) -> str:
    return TEAM_FLAGS.get(team, "🏳")


def _replace_flag_templates(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        code = match.group(1)
        return TEAM_CODES.get(code, code)

    return re.sub(r"\{\{#invoke:flag\|fb(?:-rt)?\|([A-Z]{3})\}\}", repl, value)


def _replace_score_link(value: str) -> str:
    return re.sub(r"\{\{score link\|[^|]+\|([^}]+)\}\}", r"\1", value)
