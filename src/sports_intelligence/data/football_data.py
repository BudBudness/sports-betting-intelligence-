from __future__ import annotations

import csv
import io
import time
import urllib.error
import urllib.request
from dataclasses import dataclass
from datetime import datetime, timezone
from hashlib import sha256

BASE_URL = "https://www.football-data.co.uk/mmz4281/{season}/E0.csv"
MIRROR_URL = "https://raw.githubusercontent.com/AnishKhetani/premier-league-data/main/data/processed/results_with_odds.csv"

_MIRROR_CACHE: tuple[bytes, list[dict[str, str]]] | None = None


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
    closing_home_odds: float | None
    closing_draw_odds: float | None
    closing_away_odds: float | None
    source_url: str
    source_sha256: str


def _number(row: dict[str, str], *keys: str) -> float | None:
    for key in keys:
        value = row.get(key, "")
        if value not in (None, ""):
            try:
                value_f = float(value)
                if value_f > 1.0:
                    return value_f
            except (TypeError, ValueError):
                continue
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
            closing_home_odds=_number(raw, "AvgCH", "B365CH"),
            closing_draw_odds=_number(raw, "AvgCD", "B365CD"),
            closing_away_odds=_number(raw, "AvgCA", "B365CA"),
            source_url=source_url,
            source_sha256=digest,
        ))
    return rows


def _mirror_rows(timeout: int) -> tuple[bytes, list[dict[str, str]]]:
    global _MIRROR_CACHE
    if _MIRROR_CACHE is not None:
        return _MIRROR_CACHE
    request = urllib.request.Request(
        MIRROR_URL,
        headers={
            "User-Agent": "sports-betting-intelligence/0.1 (+historical-research)",
            "Accept": "text/csv,text/plain,*/*",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        content = response.read()
    parsed = list(csv.DictReader(io.StringIO(content.decode("utf-8-sig", errors="replace"))))
    if len(parsed) < 10000:
        raise RuntimeError(f"Historical mirror sanity check failed: {len(parsed)} rows")
    _MIRROR_CACHE = (content, parsed)
    return _MIRROR_CACHE


def _parse_mirror_season(season_code: str, timeout: int) -> tuple[list[MatchRow], str, str]:
    content, records = _mirror_rows(timeout)
    digest = sha256(content).hexdigest()
    target_season = f"20{season_code[:2]}-20{season_code[2:]}"
    selected = [
        r for r in records
        if r.get("season_code") == season_code or r.get("season") == target_season
    ]
    rows: list[MatchRow] = []
    for raw in selected:
        try:
            date = datetime.fromisoformat(raw["date"]).replace(tzinfo=timezone.utc)
            home_goals = int(raw["fthg"])
            away_goals = int(raw["ftag"])
        except (KeyError, TypeError, ValueError):
            continue
        result = raw.get("ftr") or ("H" if home_goals > away_goals else "A" if home_goals < away_goals else "D")
        rows.append(MatchRow(
            season=season_code,
            date=date,
            home=raw["home_team"].strip(),
            away=raw["away_team"].strip(),
            home_goals=home_goals,
            away_goals=away_goals,
            result=result,
            avg_home_odds=_number(raw, "market_avg_1x2_home", "bet365_1x2_home"),
            avg_draw_odds=_number(raw, "market_avg_1x2_draw", "bet365_1x2_draw"),
            avg_away_odds=_number(raw, "market_avg_1x2_away", "bet365_1x2_away"),
            closing_home_odds=_number(raw, "market_avg_1x2_home_close", "bet365_1x2_home_close"),
            closing_draw_odds=_number(raw, "market_avg_1x2_draw_close", "bet365_1x2_draw_close"),
            closing_away_odds=_number(raw, "market_avg_1x2_away_close", "bet365_1x2_away_close"),
            source_url=MIRROR_URL,
            source_sha256=digest,
        ))
    if not rows:
        raise RuntimeError(f"Historical mirror contains no rows for season {season_code}")
    return rows, MIRROR_URL, digest


def download_season(season: str, timeout: int = 30, retries: int = 5) -> tuple[list[MatchRow], str, str]:
    url = BASE_URL.format(season=season)
    last_error: Exception | None = None
    for attempt in range(1, retries + 1):
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "sports-betting-intelligence/0.1 (+historical-research)",
                "Accept": "text/csv,text/plain,*/*",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=timeout) as response:
                content = response.read()
            return parse_csv(content, season, url), url, sha256(content).hexdigest()
        except (urllib.error.HTTPError, urllib.error.URLError, TimeoutError) as exc:
            last_error = exc
            if attempt < retries:
                time.sleep(min(8, 2 ** (attempt - 1)))

    try:
        return _parse_mirror_season(season, timeout)
    except Exception as mirror_error:
        raise RuntimeError(
            f"Historical source unavailable after {retries} attempts and mirror fallback failed: {url}"
        ) from mirror_error if last_error is None else last_error
