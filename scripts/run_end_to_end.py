from __future__ import annotations

import csv
import hashlib
import json
import math
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from sports_intelligence.confidence import score_confidence
from sports_intelligence.data.football_data import MatchRow, download_season
from sports_intelligence.market import edge, expected_value, fair_odds, implied_probability
from sports_intelligence.models.elo import EloState, outcome_probabilities
from sports_intelligence.production_evidence.append_only import AppendOnlyEvidenceLedger
from sports_intelligence.reporting.assessment import assess_value

SEASONS = ("2122", "2223", "2324", "2425", "2526")
TRAIN = {"2122", "2223"}
VALIDATION = {"2324"}
TEST = {"2425"}
SHADOW = {"2526"}
OUT = Path("evidence/e2e")


def multiclass_brier(rows: list[tuple[tuple[float, float, float], str]]) -> float:
    index = {"H": 0, "D": 1, "A": 2}
    return sum(sum((p - (1.0 if j == index[result] else 0.0)) ** 2 for j, p in enumerate(probs)) for probs, result in rows) / len(rows)


def multiclass_logloss(rows: list[tuple[tuple[float, float, float], str]]) -> float:
    index = {"H": 0, "D": 1, "A": 2}
    return sum(-math.log(max(1e-15, probs[index[result]])) for probs, result in rows) / len(rows)


def accuracy(rows: list[tuple[tuple[float, float, float], str]]) -> float:
    index = {"H": 0, "D": 1, "A": 2}
    return sum(int(max(range(3), key=lambda i: probs[i]) == index[result]) for probs, result in rows) / len(rows)


def calibration_error(rows: list[tuple[tuple[float, float, float], str]], bins: int = 10) -> float:
    index = {"H": 0, "D": 1, "A": 2}
    buckets: list[list[tuple[float, int]]] = [[] for _ in range(bins)]
    for probs, result in rows:
        predicted = max(probs)
        actual = int(index[result] == max(range(3), key=lambda i: probs[i]))
        bucket = min(bins - 1, int(predicted * bins))
        buckets[bucket].append((predicted, actual))
    total = len(rows)
    return sum(abs(sum(p for p, _ in b) / len(b) - sum(y for _, y in b) / len(b)) * len(b) / total for b in buckets if b)


def temperature_transform(probs: tuple[float, float, float], temperature: float) -> tuple[float, float, float]:
    logits = [math.log(max(1e-12, p)) / temperature for p in probs]
    maximum = max(logits)
    values = [math.exp(x - maximum) for x in logits]
    total = sum(values)
    return tuple(x / total for x in values)  # type: ignore[return-value]


def fit_temperature(rows: list[tuple[tuple[float, float, float], str]]) -> float:
    if not rows:
        return 1.0
    best_temperature = 1.0
    best_loss = float("inf")
    for step in range(51):
        temperature = 0.5 + step * 0.05
        transformed = [(temperature_transform(p, temperature), y) for p, y in rows]
        loss = multiclass_logloss(transformed)
        if loss < best_loss:
            best_loss = loss
            best_temperature = temperature
    return best_temperature


def normalize_market(row: MatchRow) -> tuple[float, float, float] | None:
    odds = (row.avg_home_odds, row.avg_draw_odds, row.avg_away_odds)
    if not all(x is not None and x > 1.0 for x in odds):
        return None
    raw = tuple(1.0 / float(x) for x in odds)
    total = sum(raw)
    return tuple(x / total for x in raw)  # type: ignore[return-value]


def validate(rows: list[MatchRow]) -> dict[str, object]:
    ids = [(r.season, r.date.isoformat(), r.home, r.away) for r in rows]
    duplicate_count = len(ids) - len(set(ids))
    invalid_scores = sum(int(r.home_goals < 0 or r.away_goals < 0) for r in rows)
    invalid_odds = sum(int(any(x is not None and x <= 1.0 for x in (r.avg_home_odds, r.avg_draw_odds, r.avg_away_odds, r.closing_home_odds, r.closing_draw_odds, r.closing_away_odds))) for r in rows)
    missing_market = sum(int(normalize_market(r) is None) for r in rows)
    status = "INVALID" if duplicate_count or invalid_scores else "VALID WITH WARNINGS" if missing_market else "VALID"
    return {
        "status": status,
        "rows": len(rows),
        "duplicates": duplicate_count,
        "invalid_scores": invalid_scores,
        "invalid_odds": invalid_odds,
        "missing_complete_market": missing_market,
    }


def _prediction_id(row: MatchRow) -> str:
    raw = f"{row.season}|{row.date.isoformat()}|{row.home}|{row.away}"
    return hashlib.sha256(raw.encode()).hexdigest()[:20]


def run() -> dict[str, object]:
    all_rows: list[MatchRow] = []
    sources: list[dict[str, object]] = []
    for season in SEASONS:
        rows, url, digest = download_season(season)
        all_rows.extend(rows)
        sources.append({"season": season, "url": url, "sha256": digest, "rows": len(rows)})

    rows = sorted(all_rows, key=lambda r: (r.date, r.home, r.away))
    quality = validate(rows)
    if quality["status"] == "INVALID":
        raise RuntimeError(f"Historical dataset is invalid: {quality}")

    state = EloState(ratings={})
    validation_raw: list[tuple[tuple[float, float, float], str]] = []
    test_raw: list[tuple[MatchRow, tuple[float, float, float], tuple[float, float, float]]] = []
    shadow_count = 0

    for row in rows:
        model = outcome_probabilities(state, row.home, row.away)
        market = normalize_market(row)
        if market is not None:
            if row.season in VALIDATION:
                validation_raw.append((model, row.result))
            elif row.season in TEST:
                test_raw.append((row, model, market))
            elif row.season in SHADOW:
                shadow_count += 1
        state.update(row.home, row.away, row.result == "H", row.result == "D")

    if not validation_raw or not test_raw:
        raise RuntimeError("E2E temporal split lacks validation or test observations")

    temperature = fit_temperature(validation_raw)
    calibrated_test = [(row, temperature_transform(raw, temperature), market) for row, raw, market in test_raw]

    model_rows = [(p, row.result) for row, p, _ in calibrated_test]
    market_rows = [(m, row.result) for row, _, m in calibrated_test]
    metrics = {
        "test_sample_size": len(model_rows),
        "model": {
            "brier": multiclass_brier(model_rows),
            "log_loss": multiclass_logloss(model_rows),
            "accuracy": accuracy(model_rows),
            "calibration_error": calibration_error(model_rows),
        },
        "market_baseline": {
            "brier": multiclass_brier(market_rows),
            "log_loss": multiclass_logloss(market_rows),
            "accuracy": accuracy(market_rows),
            "calibration_error": calibration_error(market_rows),
        },
        "validation": {
            "sample_size": len(validation_raw),
            "raw_log_loss": multiclass_logloss(validation_raw),
            "calibrated_log_loss": multiclass_logloss([(temperature_transform(p, temperature), y) for p, y in validation_raw]),
            "temperature": temperature,
        },
    }

    ledger_path = OUT / "prediction_ledger.jsonl"
    if ledger_path.exists():
        ledger_path.unlink()
    ledger = AppendOnlyEvidenceLedger(ledger_path)
    prediction_rows: list[dict[str, object]] = []
    assessment_counts: Counter[str] = Counter()
    candidate_returns: list[float] = []
    clv_values: list[float] = []

    for row, probs, market in calibrated_test:
        odds = (row.avg_home_odds, row.avg_draw_odds, row.avg_away_odds)
        closing = (row.closing_home_odds, row.closing_draw_odds, row.closing_away_odds)
        selections = ("HOME", "DRAW", "AWAY")
        candidates = []
        for i, selection in enumerate(selections):
            observed = odds[i]
            if observed is None:
                continue
            p = probs[i]
            imp = implied_probability(observed)
            candidates.append({
                "selection": selection,
                "probability": p,
                "fair_price": fair_odds(p),
                "market_price": observed,
                "market_implied_probability": imp,
                "edge": edge(p, imp),
                "ev": expected_value(p, observed),
                "index": i,
            })
        best = max(candidates, key=lambda c: c["ev"]) if candidates else None
        if best is None:
            assessment = "INSUFFICIENT DATA"
            confidence = score_confidence(data_quality=str(quality["status"]), model_agreement=None, sample_size=0, edge=None)
        else:
            assessment = assess_value(float(best["probability"]), float(best["market_price"]))
            agreement = 1.0 - abs(float(best["probability"]) - float(best["market_implied_probability"]))
            confidence = score_confidence(data_quality=str(quality["status"]), model_agreement=agreement, sample_size=len(model_rows), edge=float(best["edge"]))
            if assessment == "VALUE IDENTIFIED":
                candidate_returns.append(float(best["market_price"]) - 1.0 if row.result == ("H" if best["selection"] == "HOME" else "D" if best["selection"] == "DRAW" else "A") else -1.0)
        assessment_counts[assessment] += 1

        close_price = closing[best["index"]] if best is not None else None
        clv = None
        if best is not None and close_price is not None and close_price > 1.0:
            clv = float(best["market_price"]) / close_price - 1.0
            clv_values.append(clv)

        record = {
            "prediction_id": _prediction_id(row),
            "event_id": f"{row.season}:{row.date.date()}:{row.home}:{row.away}",
            "prediction_timestamp": row.date.isoformat(),
            "data_version": row.source_sha256,
            "feature_version": "elo-pre-match-v1",
            "model_version": "elo-v1",
            "calibration_version": f"temperature-v1:{temperature:.2f}",
            "market_snapshot_id": hashlib.sha256(f"{row.source_sha256}|{row.season}|{row.date.isoformat()}|{row.home}|{row.away}".encode()).hexdigest()[:24],
            "probabilities": {"home": probs[0], "draw": probs[1], "away": probs[2]},
            "fair_prices": {"home": fair_odds(probs[0]), "draw": fair_odds(probs[1]), "away": fair_odds(probs[2])},
            "market_prices": {"home": row.avg_home_odds, "draw": row.avg_draw_odds, "away": row.avg_away_odds},
            "closing_prices": {"home": row.closing_home_odds, "draw": row.closing_draw_odds, "away": row.closing_away_odds},
            "selected_candidate": best,
            "confidence": {"score": confidence.score, "level": confidence.level, "rationale": confidence.rationale},
            "assessment": assessment,
            "result": row.result,
            "closing_line_value": clv,
            "backtest_status": "OUT_OF_SAMPLE_TEST",
            "execution_boundary": "ANALYSIS_ONLY",
        }
        ledger.append(record)
        prediction_rows.append(record)

    report = {
        "status": "E2E_COMPLETE",
        "execution_boundary": "ANALYSIS_ONLY",
        "execution_utc": datetime.now(timezone.utc).isoformat(),
        "pipeline": [
            "ingestion", "provenance", "validation", "temporal_features", "pre_match_prediction",
            "probability_calibration", "market_normalization", "fair_price", "edge", "expected_value",
            "confidence", "out_of_sample_backtest", "closing_line_comparison", "immutable_ledger", "reporting",
        ],
        "source_provenance": sources,
        "data_quality": quality,
        "temporal_split": {"train": sorted(TRAIN), "validation": sorted(VALIDATION), "test": sorted(TEST), "shadow": sorted(SHADOW), "shadow_observations": shadow_count},
        "metrics": metrics,
        "value_evidence": {
            "value_identified_count": assessment_counts["VALUE IDENTIFIED"],
            "marginal_count": assessment_counts["MARGINAL VALUE"],
            "no_clear_value_count": assessment_counts["NO CLEAR VALUE"],
            "hypothetical_unit_return_sum": sum(candidate_returns),
            "hypothetical_unit_return_count": len(candidate_returns),
            "hypothetical_unit_roi": sum(candidate_returns) / len(candidate_returns) if candidate_returns else None,
            "mean_clv": sum(clv_values) / len(clv_values) if clv_values else None,
            "clv_observations": len(clv_values),
        },
        "decision_gate": {
            "model_brier_beats_market": metrics["model"]["brier"] < metrics["market_baseline"]["brier"],
            "model_log_loss_beats_market": metrics["model"]["log_loss"] < metrics["market_baseline"]["log_loss"],
            "historical_value_evidence_present": bool(candidate_returns),
            "status": "PASS" if metrics["model"]["brier"] < metrics["market_baseline"]["brier"] and metrics["model"]["log_loss"] < metrics["market_baseline"]["log_loss"] else "MODEL REVIEW REQUIRED",
        },
        "limitations": [
            "Elo is the baseline production model in this first complete E2E run; it is not a claim of optimal predictive performance.",
            "The historical provider exposes collected opening/average/closing odds rather than a complete tick-by-tick market stream.",
            "The shadow season is isolated from primary test metrics.",
            "Hypothetical returns are research evidence only; no wager execution or bankroll management occurs.",
        ],
        "ledger": {"path": str(ledger_path), "records": len(prediction_rows), "hash_chain_valid": ledger.verify()},
    }
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "report.json").write_text(json.dumps(report, indent=2, default=str) + "\n", encoding="utf-8")
    (OUT / "summary.json").write_text(json.dumps({"status": report["status"], "metrics": metrics, "decision_gate": report["decision_gate"], "value_evidence": report["value_evidence"]}, indent=2, default=str) + "\n", encoding="utf-8")

    with (OUT / "predictions.csv").open("w", newline="", encoding="utf-8") as handle:
        fields = ["prediction_id", "event_id", "selection", "probability", "market_price", "fair_price", "edge", "ev", "confidence", "assessment", "result", "closing_price", "clv"]
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for record in prediction_rows:
            selected = record["selected_candidate"] or {}
            idx = selected.get("index") if isinstance(selected, dict) else None
            closes = record["closing_prices"]
            close_map = {0: closes["home"], 1: closes["draw"], 2: closes["away"]}
            writer.writerow({
                "prediction_id": record["prediction_id"],
                "event_id": record["event_id"],
                "selection": selected.get("selection") if isinstance(selected, dict) else None,
                "probability": selected.get("probability") if isinstance(selected, dict) else None,
                "market_price": selected.get("market_price") if isinstance(selected, dict) else None,
                "fair_price": selected.get("fair_price") if isinstance(selected, dict) else None,
                "edge": selected.get("edge") if isinstance(selected, dict) else None,
                "ev": selected.get("ev") if isinstance(selected, dict) else None,
                "confidence": record["confidence"]["score"],
                "assessment": record["assessment"],
                "result": record["result"],
                "closing_price": close_map.get(idx),
                "clv": record["closing_line_value"],
            })
    return report


if __name__ == "__main__":
    result = run()
    print(json.dumps({"status": result["status"], "decision_gate": result["decision_gate"], "metrics": result["metrics"]}, indent=2, default=str))
