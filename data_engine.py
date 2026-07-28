# data_engine.py
import ccxt
import pandas as pd
from datetime import datetime, timedelta
import os
import time
import config
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class DataEngine:
    def __init__(self):
        self.exchange = ccxt.binance({
            'enableRateLimit': True,
            'options': {'defaultType': 'spot'}
        })
        self.cache_dir = 'data/ohlcv'
        os.makedirs(self.cache_dir, exist_ok=True)
        self._universe_cache = None
        self._last_universe_fetch = None

    def _build_universe(self, min_volume=200000, max_symbols=None):
        """
        Construye la lista de símbolos filtrando por volumen.
        Método extraído y adaptado del repositorio fuente (Se-ales-pro).
        """
        try:
            logger.info("🔄 Obteniendo tickers desde Binance para construir universo...")
            tickers = self.exchange.fetch_tickers()
            symbols = []
            for market_id, market in self.exchange.markets.items():
                sym = market['symbol']
                if not (sym.endswith('/USDT') and market['spot']):
                    continue
                ticker = tickers.get(market_id)
                if ticker is None:
                    continue
                vol = ticker.get('quoteVolume', 0) or ticker.get('turnover', 0)
                if vol < min_volume:
                    continue
                symbols.append(market_id)

            if not symbols:
                logger.warning("⚠️ No se encontraron símbolos con volumen suficiente. Usando fallback.")
                return self._fallback_universe()

            # Ordenar por volumen descendente
            symbols_sorted = sorted(
                symbols,
                key=lambda s: tickers.get(s, {}).get('quoteVolume', 0) or tickers.get(s, {}).get('turnover', 0),
                reverse=True
            )
            if max_symbols is not None:
                symbols_sorted = symbols_sorted[:max_symbols]

            logger.info(f"✅ Universo construido: {len(symbols_sorted)} símbolos.")
            # Guardar en config para compatibilidad con el resto del sistema
            config.UNIVERSE = symbols_sorted
            config.MAX_LEVERAGE_BY_ASSET = {sym: 10 for sym in symbols_sorted}
            self._universe_cache = symbols_sorted
            self._last_universe_fetch = time.time()
            return symbols_sorted

        except Exception as e:
            logger.error(f"❌ Error construyendo universo: {e}")
            return self._fallback_universe()

    def _fallback_universe(self):
        """Lista de respaldo si la API falla."""
        fallback = [
            'BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
            'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT',
            'MATIC/USDT', 'UNI/USDT', 'ATOM/USDT', 'LTC/USDT', 'BCH/USDT',
            'NEAR/USDT', 'ALGO/USDT', 'VET/USDT', 'ICP/USDT', 'FTM/USDT'
        ]
        logger.info(f"📌 Usando lista de fallback ({len(fallback)} símbolos).")
        config.UNIVERSE = fallback
        config.MAX_LEVERAGE_BY_ASSET = {sym: 10 for sym in fallback}
        return fallback

    def get_common_pairs(self, min_volume=200000, max_symbols=None, force_refresh=False):
        """
        Retorna el universo de activos comunes (Binance Spot USDT).
        Con caché de 1 hora para evitar llamadas excesivas.
        """
        if not force_refresh and self._universe_cache is not None:
            # Si el caché tiene menos de 1 hora, devolverlo
            if self._last_universe_fetch and (time.time() - self._last_universe_fetch) < 3600:
                return self._universe_cache

        # Si config.UNIVERSE ya está poblado y no forzamos refresco, usarlo
        if not force_refresh and hasattr(config, 'UNIVERSE') and config.UNIVERSE:
            self._universe_cache = config.UNIVERSE
            self._last_universe_fetch = time.time()
            return config.UNIVERSE

        return self._build_universe(min_volume, max_symbols)

    def fetch_ohlcv(self, symbol, timeframe='5m', limit=1000, since=None):
        """Obtiene velas, con reintentos y manejo de errores."""
        for attempt in range(3):
            try:
                return self.exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            except Exception as e:
                logger.warning(f"Intento {attempt+1} falló para {symbol}: {e}")
                time.sleep(1)
        return []

    def download_historical(self, symbol, timeframe='5m', days=365):
        """
        Descarga velas históricas con caché local (Parquet).
        Si falla la descarga, intenta usar datos cacheados.
        """
        filename = f"{self.cache_dir}/{symbol.replace('/', '_')}_{timeframe}.parquet"
        # Intentar cargar desde caché
        if os.path.exists(filename):
            try:
                df = pd.read_parquet(filename)
                if not df.empty:
                    last_ts = df.index[-1]
                    # Si los datos tienen menos de 2 días, devolverlos
                    if (datetime.now() - last_ts).total_seconds() < 3600 * 24 * 2:
                        return df
                    # Si no, actualizar incrementalmente
                    new_data = self._fetch_since(symbol, timeframe, last_ts + timedelta(minutes=1))
                    if not new_data.empty:
                        df = pd.concat([df, new_data]).drop_duplicates()
                        df.to_parquet(filename)
                    return df
            except Exception as e:
                logger.warning(f"Error leyendo caché para {symbol}: {e}")

        # Descarga completa si no hay caché o está corrupto
        df = self._fetch_since(symbol, timeframe, datetime.now() - timedelta(days=days))
        if not df.empty:
            df.to_parquet(filename)
        return df

    def _fetch_since(self, symbol, timeframe, since_dt):
        """Descarga fragmentos de velas desde una fecha específica."""
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
            time.sleep(0.1)  # Respetar rate limit
        if not all_ohlcv:
            return pd.DataFrame()
        df = pd.DataFrame(all_ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
        df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
        df.set_index('timestamp', inplace=True)
        return df

    def get_sample_data(self, symbol, timeframe='5m', days=7):
        """
        Genera datos sintéticos SOLO para demostración si la API falla.
        (Se mantiene por compatibilidad con la app Streamlit).
        """
        import numpy as np
        np.random.seed(42)
        periods = int(days * 24 * 60 / 5)
        base_price = {
            'BTC/USDT': 60000, 'ETH/USDT': 3000, 'BNB/USDT': 500,
            'SOL/USDT': 150, 'XRP/USDT': 0.5, 'DOGE/USDT': 0.08,
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
