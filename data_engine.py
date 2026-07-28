# data_engine.py
import ccxt
import pandas as pd
import time
import logging
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class DataEngine:
    def __init__(self, exchanges=None, rate_limit=True, retries=2):
        """
        Motor de datos que intenta conectarse a múltiples exchanges.
        Prioridad: Binance → KuCoin → Bybit (en ese orden).
        """
        self.exchanges = {}
        if exchanges is None:
            exchanges = ['binance', 'kucoin', 'bybit']
        
        for ex_id in exchanges:
            for attempt in range(retries):
                try:
                    if ex_id == 'binance':
                        exchange = ccxt.binance({
                            'enableRateLimit': rate_limit,
                            'options': {'defaultType': 'spot'}
                        })
                    elif ex_id == 'kucoin':
                        exchange = ccxt.kucoin({
                            'enableRateLimit': rate_limit,
                            'options': {'defaultType': 'spot'}
                        })
                    elif ex_id == 'bybit':
                        exchange = ccxt.bybit({
                            'enableRateLimit': rate_limit,
                            'options': {'defaultType': 'spot'}
                        })
                    else:
                        exchange_class = getattr(ccxt, ex_id)
                        exchange = exchange_class({'enableRateLimit': rate_limit})
                    
                    exchange.load_markets()
                    self.exchanges[ex_id] = exchange
                    logger.info(f"✅ Conectado a {ex_id}")
                    break
                except Exception as e:
                    logger.warning(f"Intento {attempt+1}/{retries} para {ex_id} falló: {e}")
                    time.sleep(2)
            else:
                self.exchanges[ex_id] = None
                logger.error(f"❌ No se pudo conectar a {ex_id}")
        
        working_exchanges = [ex_id for ex_id, ex in self.exchanges.items() if ex is not None]
        if not working_exchanges:
            raise ConnectionError("No se pudo conectar a ningún exchange. Revisa tu conexión.")
        else:
            logger.info(f"Exchanges disponibles: {working_exchanges}")
        
        self.primary_exchange = working_exchanges[0]
        self._cache = {}
        self._cache_timestamps = {}

    def get_exchange(self, exchange_id=None):
        """Devuelve el exchange solicitado o el principal si no se especifica."""
        if exchange_id and exchange_id in self.exchanges and self.exchanges[exchange_id] is not None:
            return self.exchanges[exchange_id], exchange_id
        if self.primary_exchange:
            return self.exchanges[self.primary_exchange], self.primary_exchange
        for ex_id, ex in self.exchanges.items():
            if ex is not None:
                return ex, ex_id
        return None, None

    def get_usdt_pairs(self, min_volume_usd=None, max_pairs=200, exchange_id=None, force_refresh=False):
        """
        Obtiene pares USDT del exchange especificado.
        - min_volume_usd: volumen mínimo en USDT para filtrar (ej. 200000)
        - max_pairs: número máximo de pares a devolver
        - exchange_id: 'binance', 'kucoin', 'bybit' (None = usar el principal)
        - force_refresh: True para forzar recarga desde la API
        """
        cache_key = f"pairs_{exchange_id or self.primary_exchange}_{min_volume_usd}_{max_pairs}"
        
        if not force_refresh and cache_key in self._cache:
            cache_age = time.time() - self._cache_timestamps.get(cache_key, 0)
            if cache_age < 3600:  # 1 hora de caché
                logger.info(f"📦 Usando caché para pares USDT ({len(self._cache[cache_key])} símbolos)")
                return self._cache[cache_key]

        exchange, ex_id = self.get_exchange(exchange_id)
        if exchange is None:
            logger.warning("⚠️ No hay exchange disponible. Usando lista de fallback.")
            return self._fallback_pairs(max_pairs)

        try:
            logger.info(f"🔄 Obteniendo pares USDT desde {ex_id}...")
            markets = exchange.load_markets()
            usdt_pairs = []
            
            for symbol, market in markets.items():
                if symbol.endswith('/USDT') and market.get('spot', False):
                    usdt_pairs.append(symbol)

            if min_volume_usd:
                logger.info(f"📊 Filtrando por volumen mínimo: ${min_volume_usd:,.0f}")
                tickers = exchange.fetch_tickers()
                filtered = []
                for symbol in usdt_pairs:
                    ticker = tickers.get(symbol)
                    if ticker:
                        vol = ticker.get('quoteVolume', 0) or ticker.get('turnover', 0)
                        if vol >= min_volume_usd:
                            filtered.append(symbol)
                usdt_pairs = filtered
                logger.info(f"✅ {len(usdt_pairs)} pares superan el volumen mínimo")

            # Ordenar alfabéticamente y limitar
            usdt_pairs = sorted(usdt_pairs)[:max_pairs]
            logger.info(f"📋 Obtenidos {len(usdt_pairs)} pares USDT desde {ex_id}")
            
            # Guardar en caché
            self._cache[cache_key] = usdt_pairs
            self._cache_timestamps[cache_key] = time.time()
            
            return usdt_pairs

        except Exception as e:
            logger.error(f"❌ Error obteniendo pares desde {ex_id}: {e}")
            return self._fallback_pairs(max_pairs)

    def _fallback_pairs(self, max_pairs=200):
        """Lista de respaldo de pares USDT si la API falla."""
        fallback = [
            "BTC/USDT", "ETH/USDT", "BNB/USDT", "SOL/USDT", "XRP/USDT",
            "DOGE/USDT", "ADA/USDT", "AVAX/USDT", "DOT/USDT", "LINK/USDT",
            "MATIC/USDT", "UNI/USDT", "ATOM/USDT", "LTC/USDT", "BCH/USDT",
            "NEAR/USDT", "ALGO/USDT", "VET/USDT", "ICP/USDT", "FTM/USDT",
            "ARB/USDT", "OP/USDT", "INJ/USDT", "SUI/USDT", "APT/USDT",
            "RNDR/USDT", "GRT/USDT", "AAVE/USDT", "MKR/USDT", "CRV/USDT"
        ]
        logger.info(f"📌 Usando lista de fallback ({len(fallback[:max_pairs])} símbolos)")
        return fallback[:max_pairs]

    def fetch_ohlcv(self, symbol, timeframe='5m', limit=300, exchange_id=None, force_refresh=False):
        """
        Obtiene velas OHLCV para un símbolo.
        - symbol: 'BTC/USDT', 'ETH/USDT', etc.
        - timeframe: '5m', '15m', '1h', etc.
        - limit: número de velas a obtener
        - exchange_id: exchange específico o None para usar el principal
        - force_refresh: True para ignorar caché
        """
        cache_key = f"ohlcv_{symbol}_{timeframe}_{limit}_{exchange_id or self.primary_exchange}"
        
        if not force_refresh and cache_key in self._cache:
            cache_age = time.time() - self._cache_timestamps.get(cache_key, 0)
            if cache_age < 300:  # 5 minutos de caché para OHLCV
                logger.info(f"📦 Usando caché para {symbol} ({timeframe})")
                return self._cache[cache_key]

        exchange, ex_id = self.get_exchange(exchange_id)
        if exchange is None:
            logger.error(f"❌ No hay exchange disponible para {symbol}")
            return None

        try:
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, limit=limit)
            if not ohlcv:
                logger.warning(f"⚠️ No se obtuvieron datos para {symbol} en {ex_id}")
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Guardar en caché
            self._cache[cache_key] = df
            self._cache_timestamps[cache_key] = time.time()
            
            logger.info(f"✅ {len(df)} velas obtenidas para {symbol} desde {ex_id}")
            return df

        except Exception as e:
            logger.error(f"❌ Error obteniendo OHLCV de {symbol} en {ex_id}: {e}")
            return None

    def fetch_historical(self, symbol, timeframe='5m', days=30, exchange_id=None):
        """
        Obtiene velas históricas para un período de días.
        - days: número de días hacia atrás
        """
        exchange, ex_id = self.get_exchange(exchange_id)
        if exchange is None:
            return None

        # Calcular el límite aproximado de velas
        if timeframe.endswith('m'):
            minutes = int(timeframe[:-1])
            candles_per_day = 1440 // minutes
        elif timeframe.endswith('h'):
            hours = int(timeframe[:-1])
            candles_per_day = 24 // hours
        else:
            candles_per_day = 288  # default para 5m

        limit = int(days * candles_per_day) + 100  # margen extra

        try:
            since = exchange.parse8601((datetime.now() - timedelta(days=days)).isoformat())
            ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since=since, limit=limit)
            if not ohlcv:
                return None

            df = pd.DataFrame(ohlcv, columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            # Filtrar por los días solicitados
            cutoff = datetime.now() - timedelta(days=days)
            df = df[df.index >= cutoff]
            
            logger.info(f"✅ {len(df)} velas históricas obtenidas para {symbol} ({days} días)")
            return df

        except Exception as e:
            logger.error(f"❌ Error obteniendo histórico de {symbol}: {e}")
            return None

    def fetch_multi_timeframe(self, symbol, timeframes=None, exchange_id=None):
        """
        Obtiene velas para múltiples temporalidades.
        - timeframes: lista de timeframes ['5m', '15m', '1h', ...]
        """
        if timeframes is None:
            timeframes = ['5m', '15m', '30m', '45m', '1h']
        
        result = {}
        for tf in timeframes:
            df = self.fetch_ohlcv(symbol, timeframe=tf, limit=300, exchange_id=exchange_id)
            if df is not None and not df.empty:
                result[tf] = df
            else:
                logger.warning(f"⚠️ No se obtuvieron datos para {symbol} en {tf}")
        return result

    def clear_cache(self):
        """Limpia la caché de datos."""
        self._cache.clear()
        self._cache_timestamps.clear()
        logger.info("🧹 Caché limpiada")

    def get_common_pairs(self, min_volume_usd=200000, max_pairs=100):
        """
        Alias para get_usdt_pairs (compatibilidad con versiones anteriores).
        """
        return self.get_usdt_pairs(min_volume_usd=min_volume_usd, max_pairs=max_pairs)

    def download_historical(self, symbol, timeframe='5m', days=365):
        """
        Alias para fetch_historical (compatibilidad con versiones anteriores).
        """
        return self.fetch_historical(symbol, timeframe=timeframe, days=days)
