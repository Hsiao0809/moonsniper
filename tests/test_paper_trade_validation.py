from moon_sniper_improved.paper_trade_validation import validate_trade, risk_to_stop_usdt


def stx_false_tp2_record():
    return {
        "id": "PT-STX-BAD",
        "symbol": "STXUSDT",
        "status": "closed",
        "entry_price": 0.2486,
        "exit_price": 0.2463,
        "exit_reason": "tp2",
        "position_value": 75,
        "realized_pnl_usdt": 0,
        "stop_loss_price": 0.23617,
        "tp1_price": 0.27346,
        "tp2_price": 0.29832,
    }


def test_detects_false_tp2_and_pnl_mismatch():
    issues = validate_trade(stx_false_tp2_record())
    codes = {issue.code for issue in issues}
    assert "invalid_tp2" in codes
    assert "pnl_mismatch" in codes


def test_detects_open_trade_below_stop():
    trade = {
        "id": "PT-SUI-OPEN",
        "symbol": "SUIUSDT",
        "status": "open",
        "entry_price": 1.0251,
        "position_value": 75,
        "stop_loss_price": 0.973845,
        "tp1_price": 1.12761,
        "tp2_price": 1.23012,
    }
    issues = validate_trade(trade, current_price=0.9714)
    assert {issue.code for issue in issues} == {"overdue_stop_loss"}


def test_risk_to_stop_usdt():
    trade = {
        "entry_price": 1.0251,
        "position_value": 75,
        "stop_loss_price": 0.973845,
    }
    assert round(risk_to_stop_usdt(trade), 2) == 3.75
