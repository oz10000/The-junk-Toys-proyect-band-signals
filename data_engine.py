# data_engine.py (fragmento con get_sample_data)
import ccxt
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os
import time
import config

class DataEngine:
    # ... (resto de métodos igual) ...

    def get_sample_data(self, symbol, timeframe='5m', days=7):
        """
        Genera datos sintéticos realistas para demostración cuando no hay conexión.
        """
        np.random.seed(42)
        periods = int(days * 24 * 60 / 5)
        base_price = {
            'BTC/USDT': 60000, 'ETH/USDT': 3000, 'BNB/USDT': 500,
            'SOL/USDT': 150, 'XRP/USDT': 0.5, 'DOGE/USDT': 0.08,
            'ADA/USDT': 0.3, 'AVAX/USDT': 30, 'DOT/USDT': 5,
            'LINK/USDT': 15, 'MATIC/USDT': 0.5
        }.get(symbol, 100)
        trend = np.cumsum(np.random.randn(periods) * 0.001) + 1
        close = base_price * trend
        high = close * (1 + np.random.rand(periods) * 0.01)
        low = close * (1 - np.random.rand(periods) * 0.01)
        open_price = close * (1 + np.random.randn(periods) * 0.002)
        volume = np.random.rand(periods) * 1000000
        dates = pd.date_range(end=datetime.now(), periods=periods, freq='5min')
        df = pd.DataFrame({
            'open': open_price,
            'high': high,
            'low': low,
            'close': close,
            'volume': volume
        }, index=dates)
        return df
