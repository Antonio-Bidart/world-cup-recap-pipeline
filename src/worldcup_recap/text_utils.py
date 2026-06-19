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

TEAM_FLAG_CODES = {
    "Algeria": "dz",
    "Argentina": "ar",
    "Australia": "au",
    "Austria": "at",
    "Belgium": "be",
    "Bosnia and Herzegovina": "ba",
    "Brazil": "br",
    "Cabo Verde": "cv",
    "Cameroon": "cm",
    "Canada": "ca",
    "Colombia": "co",
    "Congo DR": "cd",
    "Costa Rica": "cr",
    "Cote d'Ivoire": "ci",
    "Croatia": "hr",
    "Curacao": "cw",
    "Czechia": "cz",
    "Ecuador": "ec",
    "Egypt": "eg",
    "England": "gb-eng",
    "France": "fr",
    "Germany": "de",
    "Ghana": "gh",
    "Haiti": "ht",
    "IR Iran": "ir",
    "Iraq": "iq",
    "Japan": "jp",
    "Jordan": "jo",
    "Korea Republic": "kr",
    "Mexico": "mx",
    "Morocco": "ma",
    "Netherlands": "nl",
    "New Zealand": "nz",
    "Norway": "no",
    "Panama": "pa",
    "Paraguay": "py",
    "Portugal": "pt",
    "Qatar": "qa",
    "Saudi Arabia": "sa",
    "Scotland": "gb-sct",
    "Senegal": "sn",
    "South Africa": "za",
    "Spain": "es",
    "Sweden": "se",
    "Switzerland": "ch",
    "Tunisia": "tn",
    "Turkey": "tr",
    "United States": "us",
    "Uruguay": "uy",
    "Uzbekistan": "uz",
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
    code = TEAM_FLAG_CODES.get(team)
    if not code:
        return '<span class="flag-fallback">--</span>'
    escaped_team = html.escape(team, quote=True)
    return (
        f'<img class="flag-img" '
        f'src="https://flagcdn.com/w40/{code}.png" '
        f'srcset="https://flagcdn.com/w80/{code}.png 2x" '
        f'width="28" height="20" loading="lazy" alt="{escaped_team} flag">'
    )


def _replace_flag_templates(value: str) -> str:
    def repl(match: re.Match[str]) -> str:
        code = match.group(1)
        return TEAM_CODES.get(code, code)

    return re.sub(r"\{\{#invoke:flag\|fb(?:-rt)?\|([A-Z]{3})\}\}", repl, value)


def _replace_score_link(value: str) -> str:
    return re.sub(r"\{\{score link\|[^|]+\|([^}]+)\}\}", r"\1", value)
