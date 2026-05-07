#!/usr/bin/env python3
"""Build MoonSniper dashboard_state.json.

This script converts source market/trade records into MoonSniper's own
validated dashboard state. The GitHub Pages dashboard should read the generated
`data/dashboard_state.json`, not external dashboard state directly.

Current seed source is the original public Moon Sniper JSON. That source is
recorded in provenance so it can later be replaced by MoonSniper's own scanner
without changing the dashboard contract.
"""

from __future__ import annotations

import json
import time
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "dashboard_state.json"
SOURCE_BASE = "https://hsiao0809.github.io/moon-sniper"
BINANCE_TICKER = "https://api.binance.com/api/v3/ticker/price"


def get_json(url: str, timeout: int = 30) -> Any:
    req = urllib.request.Request(url, headers={"User-Agent": "MoonSniperBuilder/0.1"})
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.load(resp)


def fetch_prices(symbols: list[str]) -> dict[str, float]:
    prices: dict[str, float] = {}
    for i in range(0, len(symbols), 80):
        chunk = symbols[i : i + 80]
        query = urllib.parse.urlencode({"symbols": json.dumps(chunk, separators=(",", ":"))})
        try:
            rows = get_json(f"{BINANCE_TICKER}?{query}")
        except Exception:
            continue
        for row in rows:
            try:
                prices[row["symbol"]] = float(row["price"])
            except Exception:
                pass
    return prices


def risk_to_stop(trade: dict[str, Any]) -> float:
    position_value = float(trade.get("position_value") or 0)
    entry = float(trade.get("entry_price") or 0)
    stop = float(trade.get("stop_loss_price") or 0)
    if entry <= 0:
        return 0.0
    return position_value * (1 - stop / entry)


def pnl_for_trade(trade: dict[str, Any], prices: dict[str, float]) -> float:
    position_value = float(trade.get("position_value") or 0)
    entry = float(trade.get("entry_price") or 0)
    if entry <= 0:
        return 0.0
    if trade.get("status") == "closed" and trade.get("exit_price") is not None:
        return position_value * (float(trade["exit_price"]) / entry - 1)
    live = prices.get(trade.get("symbol", ""))
    if trade.get("status") == "open" and live:
        return position_value * (live / entry - 1)
    return float(trade.get("unrealized_pnl_usdt") or trade.get("realized_pnl_usdt") or 0)


def validate_trade(trade: dict[str, Any], prices: dict[str, float]) -> list[str]:
    issues: list[str] = []
    status = trade.get("status")
    entry = float(trade.get("entry_price") or 0)
    exit_price = trade.get("exit_price")
    tp1 = float(trade.get("tp1_price") or 0)
    tp2 = float(trade.get("tp2_price") or 0)
    stop = float(trade.get("stop_loss_price") or 0)

    if entry <= 0:
        return ["bad_entry_price"]

    if status == "closed":
        if exit_price is None:
            issues.append("missing_exit_price")
        else:
            exit_f = float(exit_price)
            if trade.get("exit_reason") == "tp2" and exit_f < tp2:
                issues.append("invalid_tp2_exit_below_tp2")
            if trade.get("exit_reason") == "tp1" and exit_f < tp1:
                issues.append("invalid_tp1_exit_below_tp1")
            if trade.get("exit_reason") == "stop_loss" and exit_f > stop:
                issues.append("invalid_stop_loss_exit_above_sl")
            recomputed = pnl_for_trade(trade, prices)
            recorded = float(trade.get("realized_pnl_usdt") or 0)
            if abs(recomputed - recorded) > 0.01:
                issues.append("pnl_mismatch")
    elif status == "open":
        live = prices.get(trade.get("symbol", ""))
        if live:
            if live <= stop:
                issues.append("overdue_stop_loss")
            if live >= tp2:
                issues.append("missed_tp2_exit")
            elif live >= tp1 and not trade.get("take_profit_1_hit"):
                issues.append("missed_tp1")
    else:
        issues.append("unknown_status")
    return issues


def build() -> dict[str, Any]:
    signals_data = get_json(f"{SOURCE_BASE}/signals.json?seed={int(time.time())}")
    trades_data = get_json(f"{SOURCE_BASE}/paper_trades.json?seed={int(time.time())}")
    signals = signals_data.get("signals", [])
    trades = trades_data.get("trades", [])
    symbols = sorted({s.get("symbol") for s in signals if s.get("symbol")} | {t.get("symbol") for t in trades if t.get("status") == "open" and t.get("symbol")})
    prices = fetch_prices(symbols)

    enriched_trades = []
    all_issues = []
    for trade in trades:
        t = dict(trade)
        t["current_price"] = prices.get(t.get("symbol", ""))
        t["computed_pnl_usdt"] = round(pnl_for_trade(t, prices), 6)
        t["risk_to_stop_usdt"] = round(risk_to_stop(t), 6)
        t["validation_issues"] = validate_trade(t, prices)
        t["validation_status"] = "invalid" if t["validation_issues"] else "valid"
        for issue in t["validation_issues"]:
            all_issues.append({"trade_id": t.get("id"), "symbol": t.get("symbol"), "code": issue})
        enriched_trades.append(t)

    open_trades = [t for t in enriched_trades if t.get("status") == "open"]
    closed_trades = [t for t in enriched_trades if t.get("status") == "closed"]
    open_pnl = sum(float(t["computed_pnl_usdt"]) for t in open_trades)
    closed_pnl = sum(float(t["computed_pnl_usdt"]) for t in closed_trades)
    account_balance = float(trades_data.get("stats", {}).get("account_balance") or 300)

    state = {
        "schema_version": "dashboard_state.v1",
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "provenance": {
            "mode": "seeded_from_original_public_json",
            "signals_source": f"{SOURCE_BASE}/signals.json",
            "trades_source": f"{SOURCE_BASE}/paper_trades.json",
            "price_source": BINANCE_TICKER,
            "note": "Dashboard reads this MoonSniper-owned generated file. Replace sources with MoonSniper scanner when ready.",
        },
        "signals": signals,
        "trades": enriched_trades,
        "prices": prices,
        "metrics": {
            "signal_count": len(signals),
            "total_trades": len(enriched_trades),
            "open_count": len(open_trades),
            "closed_count": len(closed_trades),
            "account_balance_usdt": account_balance,
            "open_pnl_usdt": round(open_pnl, 6),
            "closed_pnl_usdt": round(closed_pnl, 6),
            "estimated_equity_usdt": round(account_balance + open_pnl + closed_pnl, 6),
            "invalid_count": len(all_issues),
            "theoretical_sl_risk_usdt": round(sum(float(t["risk_to_stop_usdt"]) for t in open_trades), 6),
            "gross_open_exposure_usdt": round(sum(float(t.get("position_value") or 0) for t in open_trades), 6),
            "margin_used_usdt": round(sum(float(t.get("margin") or 0) for t in open_trades), 6),
        },
        "issues": all_issues,
    }
    return state


def main() -> None:
    state = build()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"wrote {OUT}")
    print(json.dumps(state["metrics"], ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
