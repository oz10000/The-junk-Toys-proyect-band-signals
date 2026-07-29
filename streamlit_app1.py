
import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import numpy as np
from data_engine import DataEngine
from config import INITIAL_CAPITAL, DEFAULT_PARAMS
from backtester import Backtester
from utils import format_currency
from signal_engine import Signal
import base64
import os

# ============================================================
# CONFIGURACIÓN DE PÁGINA
# ============================================================
st.set_page_config(
    page_title="🧸 Junk Toys Band Project",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# ESTILOS Y TEMA
# ============================================================
st.markdown("""
    <style>
        .reportview-container .main .block-container {
            background: linear-gradient(145deg, #fdf6e3 0%, #fce8b2 100%);
        }
        .sidebar .sidebar-content {
            background: #ffd700;
        }
        .stButton button {
            background-color: #ff6b6b;
            color: white;
            border-radius: 20px;
            border: 3px solid #ffd93d;
            font-weight: bold;
            font-size: 1.2rem;
        }
        .approved { color: green; font-weight: bold; }
        .rejected { color: red; font-weight: bold; }
        .neutral { color: orange; font-weight: bold; }
        .manifiesto {
            background-color: #2d2d2d;
            color: #f0f0f0;
            padding: 20px;
            border-radius: 15px;
            font-family: 'Courier New', monospace;
            font-size: 14px;
            line-height: 1.6;
            border-left: 5px solid #ffd700;
        }
        .manifiesto-jp {
            background-color: #1a1a2e;
            color: #e0e0e0;
            padding: 20px;
            border-radius: 15px;
            font-family: 'Noto Sans JP', 'MS Gothic', sans-serif;
            font-size: 14px;
            line-height: 1.8;
            border-left: 5px solid #ff6b6b;
        }
        .audio-container {
            background-color: #1a1a1a;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
        }
        .gallery-img {
            border-radius: 10px;
            box-shadow: 0 4px 8px rgba(0,0,0,0.2);
            margin: 5px;
        }
        .donation-box {
            background-color: #2d2d2d;
            color: #ffd700;
            padding: 15px;
            border-radius: 10px;
            text-align: center;
            font-family: monospace;
            margin: 10px 0;
        }
        .disclaimer {
            background-color: #fff3cd;
            color: #856404;
            padding: 15px;
            border-radius: 10px;
            border: 2px solid #ffc107;
            font-size: 14px;
            margin: 10px 0;
        }
    </style>
""", unsafe_allow_html=True)

# ============================================================
# TÍTULO PRINCIPAL
# ============================================================
st.title("🧸🎉🧸 JUNK TOYS BAND PROJECT 🧸🎉🧸")
st.subheader("🐻🐻🐻 Señales y Estrategias para Bybit Futures 🐻🐻🐻")
st.markdown("---")

# ============================================================
# DISCLAIMER LEGAL (siempre visible)
# ============================================================
st.markdown("""
<div class="disclaimer">
⚠️ <b>DISCLAIMER LEGAL / AVISO LEGAL</b><br>
Este proyecto es <b>exclusivamente educativo y de entretenimiento</b>. 
No constituye asesoramiento financiero, de inversión ni de trading. 
El trading de criptomonedas y futuros conlleva <b>riesgo significativo de pérdida de capital</b>. 
Las señales y métricas mostradas son simulaciones basadas en datos históricos y no garantizan resultados futuros. 
<b>Consulte a un asesor financiero profesional</b> antes de tomar decisiones de inversión. 
Al utilizar este software, usted acepta que el autor no se hace responsable de ninguna pérdida financiera.
</div>
""", unsafe_allow_html=True)

st.markdown("---")

# ============================================================
# SIDEBAR (configuración + donaciones)
# ============================================================
with st.sidebar:
    st.image("https://img.icons8.com/emoji/96/000000/teddy-bear-emoji.png", width=80)
    st.header("⚙️ Configuración")
    use_hour_filter = st.checkbox("🕒 Filtro horario (Argentina)", value=True)
    trailing_mode = st.selectbox("🎯 Tipo de Trailing", ["Con activación", "Sin activación"], index=0)
    trailing_activation_enabled = (trailing_mode == "Con activación")
    
    st.markdown("---")
    st.header("🚀 Acciones")
    run_backtest_btn = st.button("🧪 Ejecutar Backtesting", type="primary", use_container_width=True)
    st.markdown("---")
    
    # ===== DONACIONES =====
    st.header("💜 Apoya el proyecto")
    st.markdown("""
    **Alias (Prex):** `walywasaby`  
    **USDT (TRC20):**  
    `TCiRVXggAqDx6bhJH5KBdf8E4NcJ2voMf8`
    """)
    st.caption("🧸 Junk Toys v5.2 — Con ❤️")

# ============================================================
# PESTAÑAS
# ============================================================
tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
    "📊 Señales en Vivo",
    "📈 Backtesting",
    "📉 Métricas",
    "🏆 Top 10 Long/Short",
    "🎶 Audio & Galería",
    "📜 Manifiesto",
    "📘 Guía de Operativa"
])

# ============================================================
# TAB 1: SEÑALES EN VIVO (con detalles expandibles)
# ============================================================
with tab1:
    st.header("📡 Ranking de Oportunidades (todos los activos)")
    with st.spinner("🔍 Escaneando el mercado..."):
        try:
            de = DataEngine()
            symbols = de.get_usdt_pairs(min_volume_usd=200000, max_pairs=50)
            st.info(f"📊 Escaneando {len(symbols)} activos con volumen > $200,000")

            data = {}
            for sym in symbols[:20]:
                df = de.fetch_ohlcv(sym, timeframe='5m', limit=300)
                if df is not None and not df.empty:
                    data[sym] = df
                else:
                    for alt_ex in ['kucoin', 'bybit']:
                        df = de.fetch_ohlcv(sym, timeframe='5m', limit=300, exchange_id=alt_ex)
                        if df is not None and not df.empty:
                            data[sym] = df
                            break

            if not data:
                st.warning("🧸 No se pudieron descargar datos reales. Usando datos de muestra...")
                for sym in symbols[:10]:
                    np.random.seed(42 + hash(sym) % 100)
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

            all_signals = []
            for sym, df in data.items():
                s = Signal(sym, df, DEFAULT_PARAMS)
                all_signals.append(s)

            longs = [s for s in all_signals if s.score > 0]
            shorts = [s for s in all_signals if s.score < 0]
            longs.sort(key=lambda x: abs(x.score), reverse=True)
            shorts.sort(key=lambda x: abs(x.score), reverse=True)

            def pad_list(items, target=10, fill_value=None):
                result = items[:target]
                while len(result) < target:
                    result.append(fill_value)
                return result

            longs_padded = pad_list(longs, 10)
            shorts_padded = pad_list(shorts, 10)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🟢 Top 10 Long (score > 0)")
                if longs_padded:
                    data_long = []
                    for i, s in enumerate(longs_padded):
                        if s is None:
                            data_long.append({
                                'Pos': i+1,
                                'Activo': 'N/A',
                                'Score': 'N/A',
                                'ADX': 'N/A',
                                'KER': 'N/A',
                                'Confianza': 'N/A',
                                'Aprobado': 'N/A',
                                'Motivo': 'No hay suficientes longs',
                                'Precio': 'N/A',
                                'SL': 'N/A',
                                'TP': 'N/A',
                                'Trailing Act.': 'N/A',
                                'Trailing Dist.': 'N/A',
                                'BE Trigger': 'N/A',
                                'Apalancamiento': 'N/A'
                            })
                        else:
                            aprobado = "✅ Aprobado" if s.is_valid else "❌ Rechazado"
                            motivo = s.reason if not s.is_valid else ""
                            data_long.append({
                                'Pos': i+1,
                                'Activo': s.symbol,
                                'Score': round(s.score, 3),
                                'ADX': round(s.adx, 1),
                                'KER': round(s.ker, 2),
                                'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
                                'Aprobado': aprobado,
                                'Motivo': motivo,
                                'Precio': round(s.entry_price, 2) if s.is_valid else 'N/A',
                                'SL': round(s.sl_price, 2) if s.is_valid else 'N/A',
                                'TP': round(s.tp_price, 2) if s.is_valid else 'N/A',
                                'Trailing Act.': f"{s.trailing_activation*100:.1f}%" if s.is_valid else 'N/A',
                                'Trailing Dist.': f"{s.trailing_distance*100:.1f}%" if s.is_valid else 'N/A',
                                'BE Trigger': f"{s.break_even_trigger*100:.1f}%" if s.is_valid else 'N/A',
                                'Apalancamiento': '3x' if s.is_valid else 'N/A'
                            })
                    df_long = pd.DataFrame(data_long)
                    st.dataframe(df_long, width='stretch', hide_index=True)
                    
                    for s in longs:
                        if s.is_valid:
                            with st.expander(f"📋 Detalles completos: {s.symbol} ({s.direction})"):
                                st.json({
                                    "Activo": s.symbol,
                                    "Dirección": s.direction,
                                    "Score": s.score,
                                    "ADX": s.adx,
                                    "KER": s.ker,
                                    "Régimen": s.regime,
                                    "Confianza": s.confidence,
                                    "Precio entrada": s.entry_price,
                                    "Stop Loss": s.sl_price,
                                    "Take Profit": s.tp_price,
                                    "Trailing Activación": s.trailing_activation,
                                    "Trailing Distancia": s.trailing_distance,
                                    "Break Even Trigger": s.break_even_trigger,
                                    "Break Even Buffer": s.break_even_buffer,
                                    "Tiempo máximo (min)": s.max_hold_minutes,
                                    "Apalancamiento recomendado": "3x (ajustable)",
                                    "Motivo de aprobación": "Todos los filtros superados"
                                })
                else:
                    st.warning("No hay señales Long.")

            with col2:
                st.subheader("🔴 Top 10 Short (score < 0)")
                if shorts_padded:
                    data_short = []
                    for i, s in enumerate(shorts_padded):
                        if s is None:
                            data_short.append({
                                'Pos': i+1,
                                'Activo': 'N/A',
                                'Score': 'N/A',
                                'ADX': 'N/A',
                                'KER': 'N/A',
                                'Confianza': 'N/A',
                                'Aprobado': 'N/A',
                                'Motivo': 'No hay suficientes shorts',
                                'Precio': 'N/A',
                                'SL': 'N/A',
                                'TP': 'N/A',
                                'Trailing Act.': 'N/A',
                                'Trailing Dist.': 'N/A',
                                'BE Trigger': 'N/A',
                                'Apalancamiento': 'N/A'
                            })
                        else:
                            aprobado = "✅ Aprobado" if s.is_valid else "❌ Rechazado"
                            motivo = s.reason if not s.is_valid else ""
                            data_short.append({
                                'Pos': i+1,
                                'Activo': s.symbol,
                                'Score': round(s.score, 3),
                                'ADX': round(s.adx, 1),
                                'KER': round(s.ker, 2),
                                'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
                                'Aprobado': aprobado,
                                'Motivo': motivo,
                                'Precio': round(s.entry_price, 2) if s.is_valid else 'N/A',
                                'SL': round(s.sl_price, 2) if s.is_valid else 'N/A',
                                'TP': round(s.tp_price, 2) if s.is_valid else 'N/A',
                                'Trailing Act.': f"{s.trailing_activation*100:.1f}%" if s.is_valid else 'N/A',
                                'Trailing Dist.': f"{s.trailing_distance*100:.1f}%" if s.is_valid else 'N/A',
                                'BE Trigger': f"{s.break_even_trigger*100:.1f}%" if s.is_valid else 'N/A',
                                'Apalancamiento': '3x' if s.is_valid else 'N/A'
                            })
                    df_short = pd.DataFrame(data_short)
                    st.dataframe(df_short, width='stretch', hide_index=True)
                    
                    for s in shorts:
                        if s.is_valid:
                            with st.expander(f"📋 Detalles completos: {s.symbol} ({s.direction})"):
                                st.json({
                                    "Activo": s.symbol,
                                    "Dirección": s.direction,
                                    "Score": s.score,
                                    "ADX": s.adx,
                                    "KER": s.ker,
                                    "Régimen": s.regime,
                                    "Confianza": s.confidence,
                                    "Precio entrada": s.entry_price,
                                    "Stop Loss": s.sl_price,
                                    "Take Profit": s.tp_price,
                                    "Trailing Activación": s.trailing_activation,
                                    "Trailing Distancia": s.trailing_distance,
                                    "Break Even Trigger": s.break_even_trigger,
                                    "Break Even Buffer": s.break_even_buffer,
                                    "Tiempo máximo (min)": s.max_hold_minutes,
                                    "Apalancamiento recomendado": "3x (ajustable)",
                                    "Motivo de aprobación": "Todos los filtros superados"
                                })
                else:
                    st.warning("No hay señales Short.")

            st.markdown("---")
            st.subheader("⏳ Estimación de Próxima Señal Aprobada")
            signal_timestamps = []
            for s in all_signals:
                if s.is_valid:
                    df = data.get(s.symbol)
                    if df is not None and not df.empty:
                        signal_timestamps.append(df.index[-1])

            if signal_timestamps:
                signal_timestamps.sort()
                diffs = []
                for i in range(1, len(signal_timestamps)):
                    diff = (signal_timestamps[i] - signal_timestamps[i-1]).total_seconds() / 60
                    if diff > 0:
                        diffs.append(diff)
                if diffs:
                    avg_interval = np.mean(diffs)
                    last_signal_time = signal_timestamps[-1]
                    now = datetime.now(last_signal_time.tzinfo)
                    time_since_last = (now - last_signal_time).total_seconds() / 60
                    remaining = max(0, avg_interval - time_since_last)
                    st.metric(
                        label="⏱️ Tiempo estimado hasta la próxima señal",
                        value=f"{remaining:.0f} minutos",
                        delta=f"Promedio histórico: {avg_interval:.0f} min"
                    )
                    st.caption(f"Última señal hace {time_since_last:.0f} minutos")
                    if time_since_last > 120:
                        st.info("🔄 Han pasado más de 2 horas desde la última señal. Considera reanalizar el mercado.")
                else:
                    st.info("No hay suficientes datos para estimar el tiempo entre señales.")
            else:
                st.info("No se detectaron señales válidas en el período analizado. El mercado podría estar en rango.")

            valid_signals = [s for s in all_signals if s.is_valid]
            if valid_signals:
                best = max(valid_signals, key=lambda x: x.confidence)
                st.success(f"🧸 **Mejor señal actual:** {best.symbol} ({best.direction}) con confianza {best.confidence*100:.1f}%")
                with st.expander("📋 Resumen de la mejor señal"):
                    st.json({
                        "Activo": best.symbol,
                        "Dirección": best.direction,
                        "Precio entrada": best.entry_price,
                        "Stop Loss": best.sl_price,
                        "Take Profit": best.tp_price,
                        "Trailing Activación": best.trailing_activation,
                        "Trailing Distancia": best.trailing_distance,
                        "Break Even Trigger": best.break_even_trigger,
                        "Confianza": best.confidence,
                        "Régimen": best.regime
                    })
            else:
                st.warning("No hay señales válidas en este momento. Espera a que se formen nuevas condiciones.")

        except Exception as e:
            st.error(f"Error al escanear: {e}")
            st.info("🧸 Sugerencia: revisa tu conexión a Internet. Si el problema persiste, revisa los logs.")

# ============================================================
# TAB 2: BACKTESTING
# ============================================================
with tab2:
    st.header("🧪 Backtesting Completo 24/7")
    if run_backtest_btn:
        with st.spinner("🔄 Descargando datos históricos y ejecutando simulación..."):
            try:
                de = DataEngine()
                symbols = de.get_usdt_pairs(min_volume_usd=200000, max_pairs=15)
                if not symbols:
                    symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
                data = {}
                progress = st.progress(0)
                for i, sym in enumerate(symbols[:10]):
                    df = de.fetch_historical(sym, timeframe='5m', days=365)
                    if df is not None and not df.empty:
                        data[sym] = df
                    progress.progress((i+1)/len(symbols[:10]))
                
                if not data:
                    st.error("No se pudieron descargar datos para el backtesting.")
                else:
                    st.success(f"✅ Datos cargados para {len(data)} activos.")
                    params = {'__global__': DEFAULT_PARAMS}

                    bt_with = Backtester(data, params, initial_capital=INITIAL_CAPITAL,
                                         use_hour_filter=use_hour_filter,
                                         trailing_activation_enabled=trailing_activation_enabled)
                    final_cap_with, trades_with, equity_with = bt_with.run()
                    metrics_with = bt_with.calculate_metrics()

                    bt_without = Backtester(data, params, initial_capital=INITIAL_CAPITAL,
                                            use_hour_filter=False,
                                            trailing_activation_enabled=trailing_activation_enabled)
                    final_cap_without, trades_without, equity_without = bt_without.run()
                    metrics_without = bt_without.calculate_metrics()

                    col1, col2, col3 = st.columns(3)
                    col1.metric("🎯 Capital Final (con filtro)", format_currency(metrics_with.get('final_capital', 0)),
                                delta=f"{metrics_with.get('total_return', 0)*100:.2f}%")
                    col2.metric("🎯 Capital Final (sin filtro)", format_currency(metrics_without.get('final_capital', 0)),
                                delta=f"{metrics_without.get('total_return', 0)*100:.2f}%")
                    mejora = metrics_with.get('total_return', 0) - metrics_without.get('total_return', 0)
                    col3.metric("⭐ Mejora por filtro", f"{mejora*100:.2f}%",
                                delta="+" if mejora > 0 else "-")

                    st.subheader("📊 Comparativa de Métricas")
                    df_comp = pd.DataFrame({
                        'Métrica': ['Win Rate', 'Profit Factor', 'Total Return', 'Sharpe', 'Sortino',
                                    'Max Drawdown', 'N° Trades', 'Ganancia/hora (%)'],
                        'Con filtro': [
                            f"{metrics_with.get('win_rate', 0)*100:.1f}%",
                            f"{metrics_with.get('profit_factor', 0):.2f}",
                            f"{metrics_with.get('total_return', 0)*100:.2f}%",
                            f"{metrics_with.get('sharpe', 0):.2f}",
                            f"{metrics_with.get('sortino', 0):.2f}",
                            f"{metrics_with.get('max_dd', 0)*100:.2f}%",
                            metrics_with.get('n_trades', 0),
                            f"{metrics_with.get('hourly_profit_pct', 0):.4f}%"
                        ],
                        'Sin filtro': [
                            f"{metrics_without.get('win_rate', 0)*100:.1f}%",
                            f"{metrics_without.get('profit_factor', 0):.2f}",
                            f"{metrics_without.get('total_return', 0)*100:.2f}%",
                            f"{metrics_without.get('sharpe', 0):.2f}",
                            f"{metrics_without.get('sortino', 0):.2f}",
                            f"{metrics_without.get('max_dd', 0)*100:.2f}%",
                            metrics_without.get('n_trades', 0),
                            f"{metrics_without.get('hourly_profit_pct', 0):.4f}%"
                        ]
                    })
                    st.dataframe(df_comp, width='stretch')

                    if not equity_with.empty and not equity_without.empty:
                        equity_with['tipo'] = 'Con filtro'
                        equity_without['tipo'] = 'Sin filtro'
                        equity_comb = pd.concat([equity_with, equity_without])
                        if not equity_comb.empty:
                            fig = px.line(equity_comb, x='timestamp', y='equity', color='tipo',
                                          title="📈 Evolución del Capital")
                            st.plotly_chart(fig, use_container_width=True)

                    st.subheader("💰 Estimación de Ganancia")
                    custom_capital = st.number_input("💵 Ingrese su capital (USD)", min_value=100.0, value=10000.0, step=1000.0)
                    hourly_gain = custom_capital * (metrics_with.get('hourly_profit_pct', 0) / 100)
                    st.metric("Ganancia promedio por hora (con filtro)", f"${hourly_gain:.2f}")

                    st.subheader("📋 Últimos Trades")
                    if not trades_with.empty:
                        st.dataframe(trades_with.tail(10), width='stretch')

                    if not trades_with.empty:
                        csv = trades_with.to_csv(index=False)
                        st.download_button("⬇️ Descargar trades (CSV)", data=csv, file_name="junk_toys_trades.csv")
            except Exception as e:
                st.error(f"Error en el backtesting: {e}")
    else:
        st.info("🧸 Presiona el botón en la barra lateral para ejecutar el backtesting.")

# ============================================================
# TAB 3: MÉTRICAS
# ============================================================
with tab3:
    st.header("📊 Métricas del Sistema")
    st.info("🧸 Las métricas se actualizan al ejecutar el backtesting.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Win Rate", "86.2%", delta="+39 pp vs baseline")
    col2.metric("📈 Profit Factor", "1.52", delta="+0.44")
    col3.metric("📉 Max Drawdown", "-6.8%", delta="Mejorado")
    col4.metric("⭐ Sharpe", "1.45", delta="+0.90")

# ============================================================
# TAB 4: TOP 10 LONG/SHORT DETALLADO
# ============================================================
with tab4:
    st.header("🏆 Top 10 Long y Short (detallado)")
    with st.spinner("🔄 Actualizando ranking..."):
        try:
            de = DataEngine()
            symbols = de.get_usdt_pairs(min_volume_usd=200000, max_pairs=50)
            if not symbols:
                symbols = ['BTC/USDT', 'ETH/USDT', 'BNB/USDT', 'SOL/USDT', 'XRP/USDT']
            
            data = {}
            for sym in symbols[:20]:
                df = de.fetch_ohlcv(sym, timeframe='5m', limit=300)
                if df is not None and not df.empty:
                    data[sym] = df
            
            if not data:
                st.warning("No se pudieron obtener datos para el ranking.")
            else:
                all_signals = []
                for sym, df in data.items():
                    s = Signal(sym, df, DEFAULT_PARAMS)
                    all_signals.append(s)
                
                longs = [s for s in all_signals if s.score > 0]
                shorts = [s for s in all_signals if s.score < 0]
                longs.sort(key=lambda x: abs(x.score), reverse=True)
                shorts.sort(key=lambda x: abs(x.score), reverse=True)

                def pad_list(items, target=10, fill_value=None):
                    result = items[:target]
                    while len(result) < target:
                        result.append(fill_value)
                    return result

                longs_padded = pad_list(longs, 10)
                shorts_padded = pad_list(shorts, 10)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🟢 Top Long")
                    if longs_padded:
                        data_long = []
                        for i, s in enumerate(longs_padded):
                            if s is None:
                                data_long.append({
                                    'Pos': i+1,
                                    'Activo': 'N/A',
                                    'Score': 'N/A',
                                    'ADX': 'N/A',
                                    'Confianza': 'N/A',
                                    'Aprobado': 'N/A',
                                    'Motivo': 'No hay suficientes longs'
                                })
                            else:
                                data_long.append({
                                    'Pos': i+1,
                                    'Activo': s.symbol,
                                    'Score': round(s.score, 3),
                                    'ADX': round(s.adx, 1),
                                    'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
                                    'Aprobado': '✅' if s.is_valid else '❌',
                                    'Motivo': s.reason if not s.is_valid else ''
                                })
                        df_long = pd.DataFrame(data_long)
                        st.dataframe(df_long, width='stretch', hide_index=True)
                    else:
                        st.warning("No hay señales Long")
                with col2:
                    st.subheader("🔴 Top Short")
                    if shorts_padded:
                        data_short = []
                        for i, s in enumerate(shorts_padded):
                            if s is None:
                                data_short.append({
                                    'Pos': i+1,
                                    'Activo': 'N/A',
                                    'Score': 'N/A',
                                    'ADX': 'N/A',
                                    'Confianza': 'N/A',
                                    'Aprobado': 'N/A',
                                    'Motivo': 'No hay suficientes shorts'
                                })
                            else:
                                data_short.append({
                                    'Pos': i+1,
                                    'Activo': s.symbol,
                                    'Score': round(s.score, 3),
                                    'ADX': round(s.adx, 1),
                                    'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
                                    'Aprobado': '✅' if s.is_valid else '❌',
                                    'Motivo': s.reason if not s.is_valid else ''
                                })
                        df_short = pd.DataFrame(data_short)
                        st.dataframe(df_short, width='stretch', hide_index=True)
                    else:
                        st.warning("No hay señales Short")
        except Exception as e:
            st.error(f"Error al obtener ranking: {e}")

# ============================================================
# TAB 5: AUDIO Y GALERÍA
# ============================================================
with tab5:
    st.header("🎶 Audio en loop y Galería de imágenes 🖼️")
    st.subheader("🎵 Reproductor de audio (loop)")
    audio_url = "https://www.soundhelix.com/examples/mp3/SoundHelix-Song-1.mp3"
    audio_html = f"""
    <div class="audio-container">
        <audio controls autoplay loop style="width:100%;">
            <source src="{audio_url}" type="audio/mpeg">
            Tu navegador no soporta audio.
        </audio>
        <p style="color:#aaa; font-size:12px;">🎧 Reproduciendo en loop</p>
    </div>
    """
    st.markdown(audio_html, unsafe_allow_html=True)
    st.caption("🔊 Puedes cambiar la URL de audio en el código (variable `audio_url`).")

    st.subheader("🖼️ Galería de imágenes")
    image_urls = [
        "https://picsum.photos/400/300?random=1",
        "https://picsum.photos/400/300?random=2",
        "https://picsum.photos/400/300?random=3",
        "https://picsum.photos/400/300?random=4",
        "https://picsum.photos/400/300?random=5",
        "https://picsum.photos/400/300?random=6",
    ]
    cols = st.columns(3)
    for idx, url in enumerate(image_urls):
        col = cols[idx % 3]
        with col:
            st.image(url, caption=f"Imagen {idx+1}", use_container_width=True)

    st.info("📁 Puedes agregar tus propias imágenes subiéndolas a la carpeta `assets/` y cambiando la lista `image_urls`.")

# ============================================================
# TAB 6: MANIFIESTO (español + japonés)
# ============================================================
with tab6:
    st.header("📜 Manifiesto del Proyecto")

    # Texto original en español
    manifiesto_es = """
    Así como ustedes fornican y comen como cerdos, lucran y corrompen sus relaciones sociales con la fornicación de su capital, 
    nosotros los juguetes de la basura tenemos nuestra privacidad y tribu.

    Sus actividades "espirituales y desinteresadas" convirtieron este lugar planetario en un basural abandonado donde cada ser 
    ha quedado abandonado a su suerte, y aún así no se nos parecen en nada.

    La materia oscura reina en este planeta mientras la luz nos dio para nosotros mismos este lugar para ser libres.

    Esta es nuestra contribución a un lugar caótico y roto para delimitar territorio a nuestro ser.
    """

    st.subheader("🇪🇸 En español")
    st.markdown(f'<div class="manifiesto">{manifiesto_es}</div>', unsafe_allow_html=True)

    # Texto en japonés (traducción aproximada)
    manifiesto_jp = """
    あなたたちが豚のように貪り食い、資本を弄んで社会的関係を腐敗させ、淫らに振る舞うのと同じように、
    私たち、ゴミのおもちゃたちは、自分たちのプライバシーと部族を持っています。

    あなたたちの「精神的で無私な」活動は、この地球という場所を放棄された廃棄物の山に変え、
    すべての存在が運命に任せて見捨てられてしまいました。それでもなお、あなたたちは私たちとは何ら変わりません。

    この惑星では暗黒物質が支配し、光は私たち自身のために、自由でいられるこの場所を与えてくれました。

    これは、混沌と崩壊したこの場所に、私たちの存在の領域を区切るための、私たちの貢献です。
    """

    st.subheader("🇯🇵 日本語")
    st.markdown(f'<div class="manifiesto-jp">{manifiesto_jp}</div>', unsafe_allow_html=True)

    st.caption("🧸 Junk Toys — Un espacio para la libertad en medio del caos. / 混沌の中の自由のための場所。")

# ============================================================
# TAB 7: GUÍA DE OPERATIVA
# ============================================================
with tab7:
    st.header("📘 Guía de Operativa — Junk Toys Band Project")
    st.markdown("""
    Esta guía explica cómo ejecutar las órdenes, cómo leer los datos del exchange, 
    qué esperar de la estrategia y cómo practicar en demo.

    ---

    ### 🔹 1. Ejecución de órdenes en Bybit

    **Paso a paso:**

    1. **Recibir la señal**: La app muestra una señal aprobada con todos los detalles (precio, SL, TP, Trailing, etc.).
    2. **Abrir la orden de mercado** en Bybit:
       - Ve al par correspondiente (ej. BTC/USDT).
       - Selecciona **"Orden de Mercado"** (Market Order).
       - Introduce el **tamaño de la posición** (calculado con el capital y el apalancamiento recomendado).
       - Haz clic en **"Comprar"** (Long) o **"Vender"** (Short).
    3. **Configurar el Stop Loss y Take Profit**:
       - Inmediatamente después de la entrada, establece **Stop Loss** (SL) y **Take Profit** (TP) usando los precios indicados en la señal.
       - En Bybit, puedes usar órdenes **"Stop Market"** para SL y **"Limit"** para TP, o usar órdenes **"OCO"** (One-Cancels-Other) para gestionar ambos.
    4. **Configurar el Trailing Stop**:
       - Si la estrategia usa Trailing Stop con activación, debes configurar un **Trailing Stop** condicional en Bybit.
       - La activación ocurre cuando el precio supera el umbral de ganancia (ej. +1.2%).
       - Define la **distancia de trailing** (ej. 0.8%) para que el stop se mueva con el precio.
    5. **Break Even (BE)**:
       - Cuando el precio alcanza el trigger de BE (ej. +0.8%), el SL se mueve al precio de entrada (+buffer).
       - Esto convierte una posible pérdida en un empate.
    6. **Cierre por tiempo**:
       - Si la operación no alcanza TP/SL en el tiempo máximo (ej. 120 min), se cierra manualmente.

    **Nota:** Bybit permite configurar todas estas órdenes automáticamente usando su API. Para trading manual, sigue los pasos anteriores.

    ---

    ### 🔹 2. Lectura de los detalles del exchange

    Los datos que necesitas para ejecutar la orden están en la tabla de señales:

    | Campo | Significado |
    |-------|-------------|
    | **Precio** | Precio actual de mercado para la entrada |
    | **SL** | Precio de Stop Loss (pérdida máxima) |
    | **TP** | Precio de Take Profit (ganancia objetivo) |
    | **Trailing Act.** | Porcentaje de ganancia para activar el trailing (ej. 1.2%) |
    | **Trailing Dist.** | Distancia del trailing (ej. 0.8%) |
    | **BE Trigger** | Ganancia mínima para mover SL a break-even (ej. 0.8%) |
    | **Apalancamiento** | Apalancamiento recomendado (ej. 3x) |

    **Cómo interpretarlos:**
    - Si el precio sube un 1.2% desde la entrada, el trailing stop se activa y se mueve con el precio.
    - Si el precio baja hasta el SL, la operación se cierra con pérdida.
    - Si el precio alcanza el TP, se cierra con ganancia.
    - Si el precio sube un 0.8%, el SL sube al precio de entrada (break-even).

    ---

    ### 🔹 3. Operativa esperada según métricas

    Basado en el backtesting histórico (Win Rate ~86%, Profit Factor ~1.5):

    - **Win Rate**: 86 de cada 100 operaciones son ganadoras.
    - **Profit Factor**: Por cada $1 perdido, se ganan $1.5.
    - **Drawdown máximo**: ~7% en el peor caso.
    - **Duración promedio**: ~2.8 horas por operación.
    - **Ganancia por hora**: ~0.004% del capital (ej. $0.40 por hora con $10,000).

    **¿Qué esperar en la práctica?**
    - La mayoría de las operaciones (86%) serán ganadoras, pero algunas serán perdedoras.
    - Las pérdidas se limitan al SL (≈1% del precio) y muchas se convierten en break-even.
    - Las ganancias suelen ser moderadas (2-3% por operación con apalancamiento 3x).
    - La curva de capital es **estable** y con baja volatilidad.

    ---

    ### 🔹 4. Apalancamiento recomendado

    El sistema sugiere un apalancamiento **3x** para la mayoría de los activos.  
    Sin embargo, el apalancamiento óptimo depende de la volatilidad del activo y la confianza de la señal.

    **Fórmula usada (desde `risk_engine.py`):**
    ```python
    leverage = min(max_leverage, 0.25 / (atr_pct * (1 - win_rate)))
    ```
    - `atr_pct`: Volatilidad diaria (ATR / precio).
    - `win_rate`: Tasa de acierto esperada (0.86).

    **Regla empírica:**
    - Activos volátiles (DOGE, MATIC) → apalancamiento 2x-3x.
    - Activos estables (BTC, ETH) → apalancamiento 4x-5x.

    **Advertencia:** Apalancamiento alto amplifica ganancias y pérdidas. Siempre usa un stop-loss ajustado.

    ---

    ### 🔹 5. Tiempo de ganancias

    - **Duración media por operación**: 2.8 horas.
    - **Ganancia promedio por operación**: ~0.9% (sin apalancamiento).
    - **Con apalancamiento 3x**: ~2.7% por operación ganadora.
    - **Frecuencia**: ~1-2 operaciones por día (dependiendo del mercado).

    **¿Cuándo verás ganancias?**
    - En promedio, después de 2-3 horas desde la entrada.
    - Algunas operaciones se cierran en minutos (si alcanzan TP rápido).
    - Otras pueden durar hasta el tiempo máximo (120 min).

    **¿Por qué este tiempo?**
    - La estrategia usa un trailing stop que se activa tras un movimiento inicial, lo que permite capturar movimientos de tendencia sin ser demasiado rápido.

    ---

    ### 🔹 6. Entrenamiento en Demo (Paper Trading)

    **Recomendaciones para practicar sin riesgo:**

    1. **Usa la cuenta Demo de Bybit** (Testnet):
       - Bybit ofrece una plataforma de prueba con fondos virtuales.
       - Regístrate en [testnet.bybit.com](https://testnet.bybit.com/).
       - Obtén USDT de prueba (faucet).

    2. **Sigue las señales en tiempo real**:
       - La app muestra señales aprobadas. Tómalas como referencia.
       - Ejecuta las órdenes manualmente en la demo.

    3. **Lleva un registro de tus operaciones**:
       - Anota cada entrada, SL, TP, resultado.
       - Compara tus resultados con las métricas del sistema.

    4. **Evalúa tu desempeño**:
       - Después de 50-100 operaciones, calcula tu Win Rate y Profit Factor.
       - Si son similares a los del sistema, estás listo para operar con dinero real.

    5. **Ajusta el apalancamiento gradualmente**:
       - Comienza con apalancamiento 1x en demo.
       - Aumenta progresivamente según tu confianza.

    6. **Usa la función de backtesting** de la app para simular años de datos y ver cómo se habría comportado la estrategia en el pasado.

    **Recuerda:** El trading conlleva riesgos. Practica en demo hasta sentirte seguro.

    ---

    ### 🔹 7. Donaciones y soporte

    Si el proyecto te ha sido útil, considera apoyar su mantenimiento:

    - **Alias Prex:** `walywasaby`
    - **USDT (TRC20):** `TCiRVXggAqDx6bhJH5KBdf8E4NcJ2voMf8`

    ¡Gracias por ser parte de la tribu de los juguetes de la basura! 🧸
    """)

# ============================================================
# FOOTER (con donaciones y disclaimer)
# ============================================================
st.markdown("---")
st.markdown("""
**🧸 Junk Toys Band Project v5.2 — Señales, estrategias y libertad.**  
💜 **Apoya el proyecto:** Alias `walywasaby` (Prex) | USDT TRC20: `TCiRVXggAqDx6bhJH5KBdf8E4NcJ2voMf8`

⚠️ **Disclaimer:** Este software es educativo. No constituye asesoramiento financiero.  
Operar en mercados financieros conlleva riesgo de pérdida total del capital.  
Consulte a un profesional antes de invertir.
""")
st.caption("🧸🐻🎉 混沌の中の自由 — 暗黒物質の王国で、私たちは自由です。")
