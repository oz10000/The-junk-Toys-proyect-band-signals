# data_engine.py
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import config

class DataEngine:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.cache_dir = 'data/ohlcv'
        os.makedirs(self.cache_dir, exist_ok=True)
        self._build_universe()

    def _build_universe(self):
        """Construye la intersección Binance Spot USDT ∩ Bybit Linear USDT."""
        try:
            bybit = ccxt.bybit({'enableRateLimit': True})
            binance_markets = self.exchange.load_markets()
            bybit_markets = bybit.load_markets()
            binance_spot = {m for m in binance_markets if m.endswith('/USDT') and binance_markets[m]['spot']}
            bybit_linear = {m for m in bybit_markets if m.endswith('/USDT') and bybit_markets[m]['linear']}
            common = sorted(list(binance_spot & bybit_linear))
            config.UNIVERSE = common
            config.MAX_LEVERAGE_BY_ASSET = {sym: 10 for sym in common}
        except Exception as e:
            print(f"Error construyendo universo: {e}")
            # Fallback
            config.UNIVERSE = [
                'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
                'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT',
                'MATIC/USDT', 'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'BCH/USDT',
                'NEAR/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT', 'FTM/USDT'
            ]
            config.MAX_LEVERAGE_BY_ASSET = {sym: 10 for sym in config.UNIVERSE}

    def fetch_ohlcv(self, symbol, timeframe='5m', limit=1000, since=None):
        try:
            return self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
        except Exception as e:
            print(f"Error fetching {symbol}: {e}")
            return []

    def download_historical(self, symbol, timeframe='5m', days=365):
        filename = f"{self.cache_dir}/{symbol.replace('/', '_')}_{timeframe}.parquet"
        if os.path.exists(filename):
            df = pd.read_parquet(filename)
            if not df.empty:
                last_ts = df.index[-1]
                if (datetime.now() - last_ts).total_seconds() > 3600 * 24 * 2:
                    new_data = self._fetch_since(symbol, timeframe, last_ts + timedelta(minutes=1))
                    if not new_data.empty:
                        df = pd.concat([df, new_data]).drop_duplicates()
                        df.to_parquet(filename)
                return df
        df = self._fetch_since(symbol, timeframe, datetime.now() - timedelta(days=days))
        if not df.empty:
            df.to_parquet(filename)
        return df

    def _fetch_since(self, symbol, timeframe, since_dt):
        all_ohlcv = []
        since = self.exchange.parse8601(since_dt.isoformat())
        while True:
            batch = self.fetch_ohlcv(symbol, timeframe, limit=1000, since=since)
            if not batch:
                break
            all_ohlcv.extend(batch)
            since = batch[-1][0] + 1
            if len(batch) < 1000:
                break
            time.sleep(0.1)
        if not all_ohlcv:
            return pd.DataFrame()
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df
