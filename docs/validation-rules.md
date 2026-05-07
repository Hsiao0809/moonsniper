# Paper Trade Validation Rules

## 目的

確保紙交易紀錄可被事後驗證，避免錯誤的 TP/SL 標籤污染策略統計。

## 必要規則

### 出場理由一致性

- `exit_reason = tp2` 時，`exit_price >= tp2_price`。
- `exit_reason = tp1` 時，`exit_price >= tp1_price`。
- `exit_reason = stop_loss` 時，`exit_price <= stop_loss_price`。
- `exit_reason = time_stop` 時，`exit_time >= max_hold_until`。

### 損益重算

- long position PnL：`position_value * (exit_price / entry_price - 1)`。
- open position unrealized PnL：`position_value * (current_price / entry_price - 1)`。
- 若紀錄 PnL 與重算 PnL 差異 > 0.01U，標記 invalid。

### open trade 監控

- 若 `current_price <= stop_loss_price` 且 `status = open`，標記 `overdue_stop_loss`。
- 若 `current_price >= tp1_price` 且 `take_profit_1_hit = false`，標記 `missed_tp1`。
- 若 `current_price >= tp2_price` 且 `status = open`，標記 `missed_tp2_exit`。

### 風控規則

- 計算單筆風險：`position_value * (1 - stop_loss_price / entry_price)`。
- 同一 `signal_cluster_id` 的總風險不得超過設定上限。
- 若沒有 `signal_cluster_id`，同一分鐘內建立的同方向交易先視為同一簇。
