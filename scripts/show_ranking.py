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
    symbols = de.get_common_pairs(min_volume=200000, max_symbols=50)
    print(f"📊 Símbolos obtenidos: {len(symbols)}")

    data = {}
    for sym in symbols:
        df = de.download_historical(sym, days=7)
        if not df.empty:
            data[sym] = df

    if not data:
        print("❌ No se obtuvieron datos reales. Usando datos de muestra...")
        for sym in symbols[:10]:
            df = de.get_sample_data(sym, days=7)
            data[sym] = df

    all_signals = []
    for sym, df in data.items():
        s = Signal(sym, df, DEFAULT_PARAMS)
        all_signals.append(s)

    longs = [s for s in all_signals if s.score > 0]
    shorts = [s for s in all_signals if s.score < 0]
    longs.sort(key=lambda x: abs(x.score), reverse=True)
    shorts.sort(key=lambda x: abs(x.score), reverse=True)

    def print_table(items, title, emoji):
        print(f"\n{emoji} TOP 10 {title}")
        if not items:
            print("   No hay señales.")
            return
        df = pd.DataFrame([{
            'Pos': i+1,
            'Activo': s.symbol,
            'Score': round(s.score, 3),
            'ADX': round(s.adx, 1),
            'KER': round(s.ker, 2),
            'Aprobado': '✅' if s.is_valid else '❌',
            'Motivo': '' if s.is_valid else s.reason
        } for i, s in enumerate(items[:10])])
        print(df.to_string(index=False))

    print_table(longs, "LONG", "🟢")
    print_table(shorts, "SHORT", "🔴")

    print("\n" + "=" * 60)
    print("🧸 Fin del ranking. ¡A operar con cuidado!")

if __name__ == '__main__':
    main()
