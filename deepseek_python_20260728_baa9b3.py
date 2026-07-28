# config.py
import pytz

TIMEFRAME = '5m'
LOOKBACK_DAYS = 365
INITIAL_CAPITAL = 10000.0
COMMISSION = 0.0004
SLIPPAGE = 0.0005

TIMEZONE = pytz.timezone('America/Argentina/Buenos_Aires')

HOUR_FILTER_START = 10
HOUR_FILTER_END = 17

# El universo se llena automáticamente en data_engine
UNIVERSE = []
MAX_LEVERAGE_BY_ASSET = {}

DEFAULT_PARAMS = {
    'min_score': 0.30,
    'adx_threshold': 22,
    'ker_threshold': 0.42,
    'tp_mult': 2.5,
    'sl_mult': 1.0,
    'trailing_distance': 0.008,
    'trailing_activation': 0.012,
    'trailing_callback': 0.003,
    'break_even_trigger': 0.008,
    'break_even_buffer': 0.002,
    'max_hold_minutes': 120,
    'rotation_confidence_gap': 0.15,
}