#!/usr/bin/env python3
# scripts/show_ranking.py
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pandas as pd
from data_engine import DataEngine
from signal_engine import Signal
from config import DEFAULT_PARAMS

def main():
    print("🧸🐻 JUNK TOYS BAND PROJECT — TOP 10 LONG / SHORT 🐻🧸")
    print("=" * 60)

    de = DataEngine()
    symbols = de.get_common_pairs()
    if not symbols:
        symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT',
                   'DOGE/USDT', 'ADA/USDT', 'AVAX/USDT', 'DOT/USDT', 'LINK/USDT']
    symbols = symbols[:20]

    data = {}
    using_sample = False
    for sym in symbols:
        df = de.download_historical(sym, days=7)
        if df.empty:
            df = de.get_sample_data(sym, days=7)
            using_sample = True
        if not df.empty:
            data[sym] = df

    if using_sample:
        print("📌 Usando datos de muestra (sin conexión a Binance).")

    if not data:
        print("❌ No se pudo obtener datos para ningún activo.")
        return

    all_signals = []
    for sym, df in data.items():
        s = Signal(sym, df, DEFAULT_PARAMS)
        all_signals.append(s)

    longs = [s for s in all_signals if s.score > 0]
    shorts = [s for s in all_signals if s.score < 0]
    longs.sort(key=lambda x: x.confidence if x.is_valid else abs(x.score), reverse=True)
    shorts.sort(key=lambda x: x.confidence if x.is_valid else abs(x.score), reverse=True)

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

    # Guardar salida en archivo para artefacto
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
