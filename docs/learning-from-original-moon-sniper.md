# Learning from Original Moon Sniper

Source: https://hsiao0809.github.io/moon-sniper/
Snapshot inspected: 2026-05-08 Asia/Taipei session. Page data showed `signals.json`, `paper_trades.json`, Binance spot ticker API, Binance futures API, and OKX public API usage.

> This note is for product/system learning only. It is not evidence of trading edge and must not be used as a live trading recommendation.

## What the original does well

### 1. Fast product loop

The page turns a scanner into a usable dashboard:

- top-level KPIs: candidate count, account balance, open trades, win rate, realized PnL, unrealized PnL, total trades
- tabs: potential coins, live scan, paper trading, BTC microstructure
- direct TradingView links per symbol
- live price refresh every 30 seconds

Learning: the improved project should not only be a backend validator. It needs a clear cockpit for decision review.

### 2. Simple but legible signal model

The signal table exposes the components instead of hiding behind one score:

- scan price
- current price
- return since scan
- 24h change
- 24h quote volume
- total score
- volume score
- volume ratio
- consolidation
- overbought penalty
- momentum
- breakout
- tags

Learning: keep score decomposition visible. A score without components is hard to debug.

### 3. Data-driven tags

Tags translate numeric features into human-readable reasons:

- `📊 量爆增`
- `⚡ 上漲中`
- `🔥 強勢`
- `📈 突破壓力`
- `📗 買盤強勁`
- `🛡️ 有支撐`
- `🔄 可能反轉`

Learning: tags are useful, but each tag must map to a deterministic rule and be saved with the trade snapshot.

### 4. Live scan beyond a static JSON file

The live scan mode uses public APIs to perform on-demand scans:

- crypto: Binance spot `/api/v3/ticker/24hr`, `/api/v3/klines`, `/api/v3/depth`
- TradFi-like markets: OKX public instruments, tickers, candles, order books
- categories: crypto, US stocks, ETF, commodities

Learning: separate scheduled scanner output from interactive live scans. The former supports audited records; the latter supports exploration.

### 5. BTC microstructure module

The microstructure tab checks BTC layers:

- order book bid/ask ratio
- 20/50-day SMA regime
- 1h volume ratio
- estimated CVD intent
- estimated gamma state
- futures open interest and OI change

Learning: altcoin scanner needs a BTC/regime filter. Many altcoin long signals are regime-dependent.

## Technical structure observed

### Frontend data flow

1. `refreshData()` fetches `signals.json` and `paper_trades.json`.
2. `render()` updates time, KPIs, signal table, and trade list.
3. `fetchLivePrices()` calls Binance ticker price API for all signal symbols and open-trade symbols.
4. `renderTrades()` separates open and closed paper trades.
5. `liveScan()` performs on-demand scanning.
6. `microstructureScan()` performs BTC regime analysis.

### Data files

`signals.json` contains:

- `scanned_at`
- `total_scanned`
- `signals[]`
  - `symbol`, `base`, `price`, `price_change_24h`, `volume_24h_usdt`
  - `high_24h`, `low_24h`
  - `scores.total`, `scores.volume`, `scores.volume_ratio`, `scores.momentum`, `scores.breakout`, `scores.orderbook`, `scores.smart_money`, `scores.short`, `scores.consolidation`
  - `orderbook.bid_vol_usdt`, `ask_vol_usdt`, `bid_ask_ratio`, `support_score`, `resistance_score`
  - `tags[]`
  - `patterns`, `smart_money`

`paper_trades.json` contains:

- `stats`
  - account balance, total trades, open/closed count, win/loss count, win rate, realized/unrealized PnL
- `trades[]`
  - `id`, `symbol`, `base`, `direction`, `status`
  - `entry_price`, `entry_time`, `exit_price`, `exit_time`, `exit_reason`
  - `margin`, `leverage`, `position_value`
  - `stop_loss_price`, `tp1_price`, `tp2_price`, `max_hold_until`
  - `score`, `tags`
  - `max_unrealized_pnl_pct/usdt`, `min_unrealized_pnl_pct/usdt`
  - TP hit flags

## Scoring model observed from frontend

For live crypto scan:

- candidate filter:
  - symbol ends with `USDT`
  - exclude stablecoins
  - quote volume >= 50,000
  - 24h change >= 3% and < 20%
  - last price > 0.000001
- sort candidates by quote volume and analyze top 50
- fetch 1h klines and depth
- compute scores:
  - volume normalization
  - 24h momentum bands
  - bid/ask order book score
  - volume spike as a smart-money proxy
  - short-term breakout using recent average close vs previous average close

Important limitation: this is a heuristic scoring model, not an edge model. It must be evaluated by forward paper trading.

## Weaknesses discovered earlier and confirmed by structure

### 1. Display and truth are mixed

The frontend recomputes some live values while `paper_trades.json` stores stale or zero values. This can make dashboard stats and rendered trade cards diverge.

Improvement rule: raw records, computed metrics, and display fields must be separate.

### 2. Exit reason needs validation

Closed STX trades were marked `tp2`, but exit prices did not reach TP1/TP2. This means performance stats can be polluted.

Improvement rule: any `exit_reason` must pass a deterministic price/time condition before it enters stats.

### 3. Regime awareness is present but not yet integrated into trade gating

The BTC microstructure module is separate from the altcoin paper-trading decisions.

Improvement rule: store BTC/regime snapshot at trade entry and evaluate whether signals perform differently by regime.

### 4. Related-position risk is not explicit enough

Several trades entered at the same timestamp. They should be treated as one signal cluster rather than independent bets.

Improvement rule: add `signal_cluster_id`, cluster risk cap, and max concurrent same-regime exposure.

## Features to import into moonsniper improved

### P0 — must build first

1. Keep original dashboard concepts: KPI cards, tabs, signal table, trade cards.
2. Add validation status everywhere: valid / invalid / stale / needs review.
3. Split data layers:
   - `raw_signals.json`
   - `raw_trades.json`
   - `computed_metrics.json`
   - `dashboard_state.json`
4. Every trade must include `signal_snapshot` and `regime_snapshot`.
5. Add deterministic validation before reporting stats.

### P1 — next iteration

1. Live scan module using Binance/OKX public APIs.
2. Score decomposition and sortable columns.
3. BTC microstructure/regime panel.
4. Per-symbol TradingView links.
5. Daily auto-generated review report.

### P2 — later

1. Score-bucket validation: compare high-score vs low-score MFE/MAE.
2. Regime-conditioned performance: bull BTC / neutral / bearish.
3. Feature importance over paper-trade outcomes.
4. Watchlist and cooldown system.
5. GitHub Pages dashboard deployment pipeline.

## Proposed improved architecture

```text
scanner/                 # fetch market data and create raw signal snapshots
paper_engine/            # deterministic trade state machine
validators/              # TP/SL/time/PnL/data freshness validation
risk/                    # per-trade and cluster risk limits
reports/                 # daily markdown/json review outputs
dashboard/               # GitHub Pages static UI
schemas/                 # JSON schemas for all durable records
data/raw/                # immutable snapshots
data/derived/            # computed metrics, reproducible from raw
```

## Database fields to add

### signal snapshot

- `signal_id`
- `scan_time`
- `symbol`
- `market`
- `scan_price`
- `live_price_at_render`
- `volume_24h_usdt`
- `price_change_24h_pct`
- `scores_json`
- `tags_json`
- `source_api`
- `source_data_version`

### trade snapshot

- `trade_id`
- `signal_id`
- `signal_cluster_id`
- `entry_time`
- `entry_price`
- `entry_reason`
- `stop_loss_price`
- `tp1_price`
- `tp2_price`
- `max_hold_until`
- `risk_usdt`
- `position_value`
- `margin`
- `leverage`
- `status`
- `exit_time`
- `exit_price`
- `exit_reason`
- `validation_status`
- `validation_issues_json`

### regime snapshot

- `btc_price`
- `btc_24h_change_pct`
- `btc_sma20`
- `btc_sma50`
- `btc_regime`
- `btc_bid_ask_ratio`
- `btc_1h_volume_ratio`
- `btc_open_interest`
- `btc_oi_change_pct`
- `regime_source_time`

## Testable hypotheses

1. Signals tagged `📈 突破壓力` have higher 24h MFE than signals without breakout tags.
2. Signals with high volume score but weak order-book support have worse MAE.
3. Altcoin long signals perform better when BTC regime is bullish or neutral, and worse when BTC regime is bearish.
4. Very high 24h change close to the upper filter limit has worse forward return due to late-entry risk.
5. Cluster risk cap improves equity curve even if it reduces total trade count.

## Do not copy blindly

Useful to copy:

- product layout
- score component visibility
- live scan UX
- BTC regime panel idea
- paper-trading dashboard concept

Must redesign:

- validation logic
- PnL truth source
- TP/SL state machine
- risk clustering
- separation of raw vs computed data
- edge validation methodology

## Next implementation action

Add a dashboard data contract and build `dashboard_state.json` generation from validated records, then update the GitHub Pages page to show:

- valid trades count
- invalid trades count
- stale data warning
- theoretical stop-loss risk
- open-trade cluster exposure
- score-bucket forward performance once enough samples exist
