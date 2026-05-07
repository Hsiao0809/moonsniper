# Moon Sniper 原版交易紀錄覆盤

資料來源：`https://hsiao0809.github.io/moon-sniper/`
資料時間：頁面交易更新 `2026-05-07T14:47:40Z`；另以 Binance 即時價格約 `2026-05-07T16:39Z` 重新核算。

## 摘要

- 帳戶：300 USDT
- 總交易：11
- 持倉：8
- 平倉：3
- 頁面勝率：0%
- 頁面已實現損益：+0.00U
- 重算後總 mark-to-market PnL：約 -10.48U
- 估計權益：約 289.52U

## 核心問題

### 1. STX 平倉理由錯誤

三筆 STX 均標示 `tp2` / 停利，但出場價未達 TP1/TP2：

- entry 0.2486 → exit 0.2486，TP1 0.27346，TP2 0.29832
- entry 0.2486 → exit 0.2486，TP1 0.27346，TP2 0.29832
- entry 0.2486 → exit 0.2463，TP1 0.27346，TP2 0.29832

結論：`exit_reason=tp2` 條件錯誤，已污染勝率、停利率與已實現損益。

### 2. SUI 穿越 stop loss 仍未平倉

- entry：1.0251
- stop_loss：0.973845
- 即時價：約 0.9714
- 狀態：open

結論：止損觸發或資料更新流程有問題。

### 3. 未實現損益欄位不一致

JSON 中部分 open trade 的 `unrealized_pnl_usdt` 為 0，但頁面會顯示即時損益；需要統一由同一個計算器重算。

### 4. 相關性風險被低估

多數交易在同一時間批量進場，實際上屬於同一市場狀態下的籃子多單；應用訊號簇風險上限。

## 改良方向

1. 建立嚴格交易狀態機。
2. 每次產生交易紀錄前跑 validation。
3. 分離 raw trade、computed metrics、display stats。
4. 新增 `signal_cluster_id` 與 `market_regime_snapshot`。
5. 每日輸出異常紀錄報告。
