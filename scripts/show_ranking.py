#!/usr/bin/env python3
# scripts/show_ranking.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
import numpy as np
from datetime import datetime
from data_engine import DataEngine
from signal_engine import Signal
from config import DEFAULT_PARAMS

def main():
    print("🧸🐻 JUNK TOYS BAND PROJECT — TOP 10 LONG / SHORT 🐻🧸")
    print("=" * 60)

    # Inicializar DataEngine
    de = DataEngine()
    
    # Obtener pares con volumen mínimo
    symbols = de.get_usdt_pairs(min_volume_usd=200000, max_pairs=50)
    print(f"📊 Símbolos obtenidos: {len(symbols)}")
    
    if not symbols:
        print("❌ No se obtuvieron símbolos. Usando lista de fallback.")
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
        print(f"📌 Fallback: {len(symbols)} símbolos")

    # Descargar velas
    data = {}
    using_sample = False
    for sym in symbols[:20]:
        df = de.fetch_ohlcv(sym, timeframe='5m', limit=300)
        if df is not None and not df.empty:
            data[sym] = df
        else:
            # Intentar con otro exchange
            for alt_ex in ['kucoin', 'bybit']:
                df = de.fetch_ohlcv(sym, timeframe='5m', limit=300, exchange_id=alt_ex)
                if df is not None and not df.empty:
                    data[sym] = df
                    break

    if not data:
        print("❌ No se obtuvieron datos reales. Usando datos de muestra...")
        using_sample = True
        for sym in symbols[:10]:
            # Generar datos sintéticos
            np.random.seed(42)
            periods = 300
            base_price = 50000 if 'BTC' in sym else 3000 if 'ETH' in sym else 100
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
            data[sym] = df

    if using_sample:
        print("📌 Usando datos de muestra (sin conexión real a Binance).")

    # Generar señales
    all_signals = []
    for sym, df in data.items():
        s = Signal(sym, df, DEFAULT_PARAMS)
        all_signals.append(s)

    # Clasificar
    longs = [s for s in all_signals if s.score > 0]
    shorts = [s for s in all_signals if s.score < 0]
    longs.sort(key=lambda x: abs(x.score), reverse=True)
    shorts.sort(key=lambda x: abs(x.score), reverse=True)

    # Mostrar Top 10 Long
    print("\n🟢 TOP 10 LONG (score > 0)")
    if longs:
        df_long = pd.DataFrame([{
            'Pos': i+1,
            'Activo': s.symbol,
            'Score': round(s.score, 3),
            'ADX': round(s.adx, 1),
            'KER': round(s.ker, 2),
            'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
            'Aprobado': '✅' if s.is_valid else '❌',
            'Motivo': s.reason if not s.is_valid else ''
        } for i, s in enumerate(longs[:10])])
        print(df_long.to_string(index=False))
    else:
        print("   No hay señales Long.")

    # Mostrar Top 10 Short
    print("\n🔴 TOP 10 SHORT (score < 0)")
    if shorts:
        df_short = pd.DataFrame([{
            'Pos': i+1,
            'Activo': s.symbol,
            'Score': round(s.score, 3),
            'ADX': round(s.adx, 1),
            'KER': round(s.ker, 2),
            'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
            'Aprobado': '✅' if s.is_valid else '❌',
            'Motivo': s.reason if not s.is_valid else ''
        } for i, s in enumerate(shorts[:10])])
        print(df_short.to_string(index=False))
    else:
        print("   No hay señales Short.")

    print("\n" + "=" * 60)
    print("🧸 Fin del ranking. ¡A operar con cuidado!")

    # Guardar salida para artefacto
    with open('ranking_output.txt', 'w') as f:
        f.write("🧸 JUNK TOYS RANKING\n")
        f.write("="*60 + "\n")
        if longs:
            f.write("🟢 LONG\n")
            f.write(df_long.to_string(index=False) + "\n\n")
        if shorts:
            f.write("🔴 SHORT\n")
            f.write(df_short.to_string(index=False) + "\n")

if __name__ == '__main__':
    main()
