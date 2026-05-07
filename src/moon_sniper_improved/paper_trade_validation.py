"""Validation helpers for Moon Sniper paper trade records.

These checks are intentionally conservative: when a record cannot be
verified from its own fields and current price input, it should be flagged
instead of silently included in performance statistics.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any

PNL_TOLERANCE_USDT = 0.01


@dataclass(frozen=True)
class ValidationIssue:
    trade_id: str
    symbol: str
    code: str
    message: str


def _parse_dt(value: str | None) -> datetime | None:
    if not value:
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


def long_pnl_usdt(position_value: float, entry_price: float, price: float) -> float:
    """Return long-position PnL in USDT, excluding fees/slippage."""
    return position_value * (price / entry_price - 1.0)


def risk_to_stop_usdt(trade: dict[str, Any]) -> float:
    """Return theoretical long risk to stop loss in USDT."""
    return float(trade["position_value"]) * (1.0 - float(trade["stop_loss_price"]) / float(trade["entry_price"]))


def validate_trade(trade: dict[str, Any], current_price: float | None = None) -> list[ValidationIssue]:
    """Validate one Moon Sniper paper trade record.

    Args:
        trade: Paper trade dictionary.
        current_price: Current market price for open-position checks.

    Returns:
        List of validation issues. Empty list means the record passed these checks.
    """
    issues: list[ValidationIssue] = []
    trade_id = str(trade.get("id", "<missing-id>"))
    symbol = str(trade.get("symbol", "<missing-symbol>"))

    status = trade.get("status")
    entry_price = float(trade.get("entry_price", 0) or 0)
    exit_price = trade.get("exit_price")
    exit_reason = trade.get("exit_reason")
    position_value = float(trade.get("position_value", 0) or 0)
    tp1 = float(trade.get("tp1_price", 0) or 0)
    tp2 = float(trade.get("tp2_price", 0) or 0)
    stop = float(trade.get("stop_loss_price", 0) or 0)

    if entry_price <= 0:
        issues.append(ValidationIssue(trade_id, symbol, "bad_entry_price", "entry_price must be positive"))
        return issues

    if status == "closed":
        if exit_price is None:
            issues.append(ValidationIssue(trade_id, symbol, "missing_exit_price", "closed trade has no exit_price"))
            return issues
        exit_price_f = float(exit_price)

        if exit_reason == "tp2" and exit_price_f < tp2:
            issues.append(ValidationIssue(trade_id, symbol, "invalid_tp2", "exit_reason=tp2 but exit_price < tp2_price"))
        if exit_reason == "tp1" and exit_price_f < tp1:
            issues.append(ValidationIssue(trade_id, symbol, "invalid_tp1", "exit_reason=tp1 but exit_price < tp1_price"))
        if exit_reason == "stop_loss" and exit_price_f > stop:
            issues.append(ValidationIssue(trade_id, symbol, "invalid_stop_loss", "exit_reason=stop_loss but exit_price > stop_loss_price"))
        if exit_reason == "time_stop":
            exit_time = _parse_dt(trade.get("exit_time"))
            max_hold_until = _parse_dt(trade.get("max_hold_until"))
            if exit_time and max_hold_until and exit_time < max_hold_until:
                issues.append(ValidationIssue(trade_id, symbol, "invalid_time_stop", "exit_time is before max_hold_until"))

        expected_pnl = long_pnl_usdt(position_value, entry_price, exit_price_f)
        recorded_pnl = float(trade.get("realized_pnl_usdt", 0) or 0)
        if abs(expected_pnl - recorded_pnl) > PNL_TOLERANCE_USDT:
            issues.append(
                ValidationIssue(
                    trade_id,
                    symbol,
                    "pnl_mismatch",
                    f"realized_pnl_usdt mismatch: expected {expected_pnl:.4f}, recorded {recorded_pnl:.4f}",
                )
            )

    elif status == "open" and current_price is not None:
        current = float(current_price)
        if current <= stop:
            issues.append(ValidationIssue(trade_id, symbol, "overdue_stop_loss", "open trade current_price <= stop_loss_price"))
        if current >= tp2:
            issues.append(ValidationIssue(trade_id, symbol, "missed_tp2_exit", "open trade current_price >= tp2_price"))
        elif current >= tp1 and not trade.get("take_profit_1_hit"):
            issues.append(ValidationIssue(trade_id, symbol, "missed_tp1", "open trade current_price >= tp1_price but TP1 not marked"))

    else:
        issues.append(ValidationIssue(trade_id, symbol, "unknown_status", f"unsupported status: {status}"))

    return issues
