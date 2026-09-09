from datetime import datetime, timezone

from sports_intelligence.data.football_data import parse_csv
from sports_intelligence.evaluation.walk_forward_evidence import run_walk_forward


def test_parse_and_walk_forward_evidence():
    csv = b"Date,HomeTeam,AwayTeam,FTHG,FTAG,FTR,AvgH,AvgD,AvgA,AvgCH,AvgCD,AvgCA\n01/08/2025,A,B,2,0,H,2.0,3.4,4.0,1.9,3.5,4.2\n08/08/2025,B,A,1,1,D,2.6,3.2,2.7,2.5,3.1,2.8\n"
    rows = parse_csv(csv, "2526", "fixture://test")
    summary = run_walk_forward(rows)
    assert summary.sample_size == 2
    assert summary.model_brier >= 0
    assert summary.market_brier >= 0
    assert summary.closing_line_observations == 2
    assert summary.mean_closing_odds_delta is not None
