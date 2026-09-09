# Evidence Stage

The project is now entering the evidence stage. The objective is to replace architectural claims with reproducible, timestamped, source-hashed historical observations.

## First evidence track

**Dataset:** Football-Data.co.uk England Premier League E0 historical CSVs.

The source publishes historical results and betting odds, including collected opening/pre-closing prices and, for supported seasons, closing prices. Source documentation states that historical results, odds and match statistics are available for quantitative testing. citeturn0search0turn0search8

**Baseline model:** walk-forward Elo.

**Market baseline:** normalized implied probability from observed average opening odds.

**Metrics:**
- Brier score
- Log loss
- Accuracy
- Positive-EV observation count
- Positive-EV hit rate
- Opening-to-closing price delta where closing data exists

## Evidence rules

1. Predictions are generated before the match outcome is revealed.
2. Team ratings are updated only after each historical match.
3. No future match outcome is used to generate a prior prediction.
4. Every downloaded source is SHA-256 hashed.
5. Source URL, season, row count and hash are retained in the evidence output.
6. Historical evidence is not treated as proof of future profitability.
7. The baseline is explicitly labeled as a baseline and does not represent the final production ensemble.
8. Missing odds/closing observations are excluded from the affected metric and remain visible through counts.

## Reproducible run

```bash
PYTHONPATH=src python scripts/run_historical_evidence.py
```

The runner downloads five Premier League seasons (`2122` through `2526`), reconstructs predictions chronologically, compares them with the normalized market baseline, and writes:

`evidence/historical/football_data_e0.json`

That output must not be hand-edited. A later run may produce a new source hash if the upstream provider revises a file.

## Evidence maturity gate

This stage is **not production evidence yet**. Production evidence requires:

- multiple independent historical sources/providers;
- more than one sport/league/market;
- calibrated model probabilities;
- rolling/expanding validation across separate development and holdout periods;
- baseline comparisons across seasons and market regimes;
- closing-line analysis with a defined metric;
- prediction ledger persistence;
- drift and data-quality monitoring;
- immutable production prediction records;
- independent end-to-end verification.

No performance claim should be published until those gates are satisfied.
