# Sports Betting Intelligence

Production-grade, analysis-only sports betting intelligence platform.

## Purpose

Convert sports data and time-stamped market observations into reproducible probabilistic forecasts, calibrated probabilities, fair prices, value analysis, confidence assessments, historical backtests, model evaluation, and production evidence.

## Hard Boundary

This system does **not** place, submit, modify, or simulate real wagers. It does not operate betting accounts or move funds. Hypothetical EV and research scenarios are analytical outputs only.

## Architecture

Folders/modules define capabilities. Deterministic services execute logic. Pipelines orchestrate. Models produce mathematics. Rules enforce quality gates. Optional AI may interpret outputs but is never required for core operation.

## Core flow

`Ingestion → Validation → Features → Prediction → Calibration → Market → Value → Confidence → Risk → Evaluation → Reporting → Audit`

## Evidence standard

Historical validation reconstructs the information set available at each prediction timestamp. Production evidence is maintained through an immutable prediction ledger, outcome reconciliation, calibration monitoring, market comparison, closing-line analysis, and drift detection.

## Evidence-stage implementation

The repository now includes a reproducible historical evidence track using Football-Data.co.uk Premier League E0 data, a walk-forward Elo baseline, normalized market baseline comparison, source SHA-256 provenance, closing-price capture, and a GitHub Actions evidence workflow. See `docs/EVIDENCE_STAGE.md`.

The evidence runner covers seasons `2122` through `2526` and writes a machine-readable evidence artifact. Numerical results are not committed until the source data has actually been downloaded and the run completed successfully.

## Repository status

`v0.1.0` — evidence-stage implementation baseline.

No fabricated historical data, performance claims, odds, or profitability results are included.
