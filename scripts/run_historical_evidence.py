from __future__ import annotations

import json
from pathlib import Path

from sports_intelligence.data.football_data import download_season
from sports_intelligence.evaluation.walk_forward_evidence import run_walk_forward

SEASONS = ("2122", "2223", "2324", "2425", "2526")
OUT = Path("evidence/historical/football_data_e0.json")


def main() -> None:
    all_rows = []
    sources = []
    for season in SEASONS:
        rows, url, digest = download_season(season)
        all_rows.extend(rows)
        sources.append({"season": season, "url": url, "sha256": digest, "rows": len(rows)})
    summary = run_walk_forward(all_rows)
    payload = {
        "status": "OBSERVED_RUN",
        "method": "walk_forward_elo_vs_normalized_market",
        "execution_utc": __import__("datetime").datetime.now(__import__("datetime").timezone.utc).isoformat(),
        "source": "Football-Data.co.uk England Premier League E0",
        "sources": sources,
        "metrics": summary.__dict__,
        "limitations": [
            "This is a baseline model, not the final ensemble.",
            "The historical source provides collected odds rather than a complete tick-level market history.",
            "Results are evidence of historical behavior only and are not a guarantee of future performance.",
        ],
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(payload["metrics"], indent=2))


if __name__ == "__main__":
    main()
