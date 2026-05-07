# Moon Sniper Improved Implementation Plan

> For Hermes: Use this plan as the implementation checklist for the improved Moon Sniper project.

## Goal

Build a reliable paper-trading and review layer for Moon Sniper, focused on data integrity, risk controls, and auditable performance metrics.

## Architecture

- Keep raw market/signal/trade snapshots immutable.
- Compute PnL and stats from raw records, not hand-edited display fields.
- Validate every trade record before publishing dashboard data.
- Separate scanner, paper-trade engine, validator, report generator, and dashboard.

## Milestones

### M1 — Data Quality Foundation

- Add JSON schema for paper trades.
- Add Python validator for TP/SL/time-stop and PnL consistency.
- Add invalid-record report.

### M2 — Risk Engine

- Add per-trade risk calculation.
- Add signal-cluster grouping.
- Add max concurrent positions and cluster risk cap.

### M3 — Review Metrics

- Add MFE/MAE tracking.
- Add TP1/SL/time-stop hit rates.
- Add score-bucket performance analysis.

### M4 — Dashboard Upgrade

- Show valid vs invalid records.
- Show realized, unrealized, exposure, margin used, theoretical SL risk.
- Show open trades that should have triggered SL/TP.

## Acceptance Criteria

- STX-style false `tp2` records are detected as invalid.
- SUI-style open trade below SL is detected as `overdue_stop_loss`.
- All PnL shown on dashboard can be recomputed from raw price fields.
- Strategy performance cannot be reported unless invalid-record count is zero or explicitly disclosed.
