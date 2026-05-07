# Moon Sniper Improved

Moon Sniper 改良版專案：把原本的暴漲潛力幣種偵測 + 紙交易追蹤，升級成「可驗證、可覆盤、可風控」的交易研究系統。

> 狀態：專案初始化。此專案目前只做研究與紙交易，不宣稱有實盤 edge。

## 改良目標

1. 修正紙交易引擎資料品質問題：TP/SL/時間停損必須與價格條件一致。
2. 建立可審計交易紀錄：entry、exit、reason、PnL、MFE、MAE、signal snapshot 全部可重算。
3. 加入風控層：單筆風險、同訊號簇總風險、最大同時持倉、冷卻時間。
4. 評分可驗證：追蹤 score 與後續 MFE/MAE、TP1、SL 的關係。
5. 建立每日覆盤輸出：績效、異常紀錄、風險暴露、下一步實驗。

## 從原版覆盤得到的第一批問題

- STX 平倉標示 `tp2`，但 exit price 低於 TP1/TP2，出場理由不可信。
- SUI 即時價格低於 stop loss，但交易仍標示 open，止損觸發疑似失效。
- `paper_trades.json` 的 `unrealized_pnl_usdt` 與前端即時計算不一致。
- 多筆交易同一時間批量進場，實際上是同一市場 regime 的高度相關曝險。

## 專案結構

```text
moon-sniper-improved/
├── README.md
├── docs/
│   ├── improvement-plan.md
│   ├── trading-record-review.md
│   └── validation-rules.md
├── schemas/
│   └── paper_trade.schema.json
└── src/
    └── moon_sniper_improved/
        ├── __init__.py
        └── paper_trade_validation.py
```

## 風控預設

- 此專案預設只做紙交易。
- 若未來轉實盤，預設單一 live trade idea 最大計畫虧損不得超過 10U。
- 同一批次/同一訊號簇總風險需另外計算，不可把高度相關多單視為分散。

## 下一步

1. 將原版 `paper_trades.json` 匯入測試資料。
2. 實作 validation CLI，輸出 invalid records。
3. 修正 TP/SL/time-stop 狀態機。
4. 新增每日覆盤報告產生器。
