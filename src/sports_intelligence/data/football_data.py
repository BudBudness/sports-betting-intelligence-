from __future__ import annotations

import csv
import io
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/E0.csv"


@dataclass(frozen=True)
class MatchRow:
    season: str
    date: datetime
    home: str
    away: str
    home_goals: int
    away_goals: int
    result: str
    avg_home_odds: float | None
    avg_draw_odds: float | None
    avg_away_odds: float | None
    source_url: str
    source_sha256: str


def _number(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key, "")
        if value:
            try:
                return float(value)
            except ValueError:
                return None
    return None


def parse_csv(content: bytes, season: str, source_url: str) -> list[MatchRow]:
    digest = sha256(content).hexdigest()
    text = content.decode("utf-8-sig", errors="replace")
    rows: list[MatchRow] = []
    for raw in csv.DictReader(io.StringIO(text)):
        if not raw.get("Date") or not raw.get("HomeTeam") or not raw.get("AwayTeam"):
            continue
        try:
            date = datetime.strptime(raw["Date"], "%d/%m/%Y").replace(tzinfo=timezone.utc)
            home_goals = int(raw["FTHG"])
            away_goals = int(raw["FTAG"])
        except (KeyError, TypeError, ValueError):
            continue
        result = "H" if home_goals > away_goals else "A" if home_goals < away_goals else "D"
        rows.append(MatchRow(
            season=season,
            date=date,
            home=raw["HomeTeam"].strip(),
            away=raw["AwayTeam"].strip(),
            home_goals=home_goals,
            away_goals=away_goals,
            result=result,
            avg_home_odds=_number(raw, "AvgH", "B365H"),
            avg_draw_odds=_number(raw, "AvgD", "B365D"),
            avg_away_odds=_number(raw, "AvgA", "B365A"),
            source_url=source_url,
            source_sha256=digest,
        ))
    return rows


def download_season(season: str, timeout: int = 30) -> tuple[list[MatchRow], str, str]:
    url = BASE_URL.format(season=season)
    request = urllib.request.Request(url, headers={"User-Agent": "sports-betting-intelligence/0.1"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read()
    return parse_csv(content, season, url), url, sha256(content).hexdigest()
