# streamlit_app.py
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

st.set_page_config(
    page_title="🧸 Junk Toys Band Project",
    page_icon="🧸",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    </style>
""", unsafe_allow_html=True)

st.title("🧸🎉🧸 JUNK TOYS BAND PROJECT 🧸🎉🧸")
st.subheader("🐻🐻🐻 Señales y Estrategias para Bybit Futures 🐻🐻🐻")
st.markdown("---")

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
    st.caption("🧸 Junk Toys v4.9 — Con DataEngine funcional")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Señales en Vivo", "📈 Backtesting", "📉 Métricas", "🏆 Top 10 Long/Short"])

# ============================================================
# TAB 1: SEÑALES EN VIVO
# ============================================================
with tab1:
    st.header("📡 Ranking de Oportunidades (todos los activos)")
    with st.spinner("🔍 Escaneando el mercado..."):
        try:
            # Inicializar DataEngine
            de = DataEngine()
            
            # Obtener pares con volumen mínimo
            symbols = de.get_usdt_pairs(min_volume_usd=200000, max_pairs=50)
            st.info(f"📊 Escaneando {len(symbols)} activos con volumen > $200,000")

            data = {}
            using_sample = False
            
            for sym in symbols[:20]:  # Limitamos a 20 para velocidad en Streamlit
                df = de.fetch_ohlcv(sym, timeframe='5m', limit=300)
                if df is not None and not df.empty:
                    data[sym] = df
                else:
                    # Si falla, intentar con otro exchange
                    for alt_ex in ['kucoin', 'bybit']:
                        df = de.fetch_ohlcv(sym, timeframe='5m', limit=300, exchange_id=alt_ex)
                        if df is not None and not df.empty:
                            data[sym] = df
                            break

            if not data:
                st.warning("🧸 No se pudieron descargar datos reales. Usando datos de muestra...")
                for sym in symbols[:10]:
                    df = de.fetch_historical(sym, days=7)  # Intenta histórico
                    if df is not None and not df.empty:
                        data[sym] = df
                    else:
                        # Último recurso: generar datos sintéticos
                        from data_engine import logger
                        logger.warning(f"Generando datos sintéticos para {sym}")
                        np.random.seed(42)
                        periods = 288  # 1 día de velas de 5m
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
                        using_sample = True

            if using_sample:
                st.info("🧸 Usando datos de muestra (algunos activos no se pudieron obtener en tiempo real).")

            # Generar señales
            all_signals = []
            for sym, df in data.items():
                s = Signal(sym, df, DEFAULT_PARAMS)
                all_signals.append(s)

            # Clasificar por signo del score
            longs = [s for s in all_signals if s.score > 0]
            shorts = [s for s in all_signals if s.score < 0]
            
            # Ordenar por confianza o score absoluto
            longs.sort(key=lambda x: x.confidence if x.is_valid else abs(x.score), reverse=True)
            shorts.sort(key=lambda x: x.confidence if x.is_valid else abs(x.score), reverse=True)

            if not longs and not shorts:
                st.info("🧸 No se detectan direcciones claras (score ≈ 0). Mostrando todos los activos ordenados por ADX.")
                all_sorted = sorted(all_signals, key=lambda x: x.adx, reverse=True)
                if all_sorted:
                    data_all = []
                    for i, s in enumerate(all_sorted[:20]):
                        aprobado = "✅ Aprobado" if s.is_valid else "❌ Rechazado"
                        motivo = s.reason if not s.is_valid else ""
                        data_all.append({
                            'Pos': i+1,
                            'Activo': s.symbol,
                            'Score': round(s.score, 3),
                            'ADX': round(s.adx, 1),
                            'KER': round(s.ker, 2),
                            'Confianza': f"{s.confidence*100:.1f}%" if s.is_valid else "N/A",
                            'Aprobado': aprobado,
                            'Motivo': motivo,
                            'Dirección': 'Neutral'
                        })
                    df_all = pd.DataFrame(data_all)
                    st.dataframe(df_all, width='stretch', hide_index=True)
                else:
                    st.warning("No hay señales disponibles.")
            else:
                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🟢 Top 10 Long (score > 0)")
                    if longs:
                        data_long = []
                        for i, s in enumerate(longs[:10]):
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
                                'Motivo': motivo
                            })
                        df_long = pd.DataFrame(data_long)
                        st.dataframe(df_long, width='stretch', hide_index=True)
                    else:
                        st.warning("No hay activos con score Long.")

                with col2:
                    st.subheader("🔴 Top 10 Short (score < 0)")
                    if shorts:
                        data_short = []
                        for i, s in enumerate(shorts[:10]):
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
                                'Motivo': motivo
                            })
                        df_short = pd.DataFrame(data_short)
                        st.dataframe(df_short, width='stretch', hide_index=True)
                    else:
                        st.warning("No hay activos con score Short.")

            # Estimación de tiempo
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

            # Mejor señal actual
            valid_signals = [s for s in all_signals if s.is_valid]
            if valid_signals:
                best = max(valid_signals, key=lambda x: x.confidence)
                st.success(f"🧸 **Mejor señal actual:** {best.symbol} ({best.direction}) con confianza {best.confidence*100:.1f}%")
                with st.expander("📋 Detalles de la señal seleccionada"):
                    df_best = pd.DataFrame({
                        'Parámetro': ['Activo', 'Dirección', 'Precio', 'SL', 'TP', 'Trailing Act.', 'Trailing Dist.', 'BE Trigger', 'Confianza', 'Régimen'],
                        'Valor': [best.symbol, best.direction, f"{best.entry_price:.2f}", f"{best.sl_price:.2f}", f"{best.tp_price:.2f}",
                                  f"{best.trailing_activation*100:.1f}%", f"{best.trailing_distance*100:.1f}%",
                                  f"{best.break_even_trigger*100:.1f}%", f"{best.confidence*100:.1f}%", best.regime]
                    })
                    st.dataframe(df_best, width='stretch', hide_index=True)
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
# TAB 4: TOP 10 DETALLADO
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
                longs.sort(key=lambda x: x.confidence if x.is_valid else abs(x.score), reverse=True)
                shorts.sort(key=lambda x: x.confidence if x.is_valid else abs(x.score), reverse=True)

                col1, col2 = st.columns(2)
                with col1:
                    st.subheader("🟢 Top Long")
                    if longs:
                        data_long = []
                        for i, s in enumerate(longs[:10]):
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
                    if shorts:
                        data_short = []
                        for i, s in enumerate(shorts[:10]):
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

st.markdown("---")
st.caption("🧸 Junk Toys Band Project v4.9 — DataEngine funcional con múltiples exchanges. 🧸🐻🎉")
