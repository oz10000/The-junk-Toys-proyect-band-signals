# risk_engine.py
from config import MAX_LEVERAGE_BY_ASSET

def get_optimal_leverage(symbol, atr_pct, confidence, target_win_rate=0.85):
    max_lev = MAX_LEVERAGE_BY_ASSET.get(symbol, 10)
    if atr_pct <= 0:
        return 1
    kelly = 0.25 / (atr_pct * (1 - target_win_rate))
    leverage = kelly * (0.5 + 0.5 * confidence)
    leverage = max(1, min(max_lev, int(round(leverage))))
    return leverage
