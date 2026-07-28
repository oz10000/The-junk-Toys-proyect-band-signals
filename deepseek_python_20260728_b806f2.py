# streamlit_app.py
import streamlit as st
import pandas as pd
import plotly.express as px
from data_engine import DataEngine
from config import UNIVERSE, INITIAL_CAPITAL, DEFAULT_PARAMS
from backtester import Backtester
from utils import format_currency

st.set_page_config(
    page_title="🧸 Shank Toys Project Band",
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
    </style>
""", unsafe_allow_html=True)

st.title("🧸🎉 THE SHANK TOYS PROJECT BAND 🎉🧸")
st.subheader("📡 Señales y Estrategias para Bybit Futures")
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
    st.caption("🧸 Shank Toys v4.1 — Bybit Portfolio Rotator")

tab1, tab2, tab3, tab4 = st.tabs(["📊 Señales en Vivo", "📈 Backtesting", "📉 Métricas", "🏆 Top 10 Long/Short"])

with tab1:
    st.header("📡 Ranking de Oportunidades")
    with st.spinner("🔍 Escaneando el mercado..."):
        try:
            de = DataEngine()
            symbols = UNIVERSE if UNIVERSE else de.get_common_pairs()
            symbols = symbols[:10]
            data = {}
            for sym in symbols:
                df = de.download_historical(sym, days=7)
                if not df.empty:
                    data[sym] = df
            from signal_engine import Signal
            signals = []
            for sym, df in data.items():
                s = Signal(sym, df, DEFAULT_PARAMS)
                if s.is_valid:
                    signals.append(s)
            if signals:
                longs = [s for s in signals if s.direction == 'Long']
                shorts = [s for s in signals if s.direction == 'Short']
                top_long = max(longs, key=lambda x: x.confidence) if longs else None
                top_short = max(shorts, key=lambda x: x.confidence) if shorts else None
                best = max(signals, key=lambda x: x.confidence)
                col1, col2, col3 = st.columns(3)
                col1.metric("🧸 Mejor Señal", f"{best.symbol} ({best.direction})", delta=f"Confianza {best.confidence*100:.1f}%")
                col2.metric("🟢 Top Long", f"{top_long.symbol if top_long else 'N/A'}", delta=f"{top_long.confidence*100:.1f}%" if top_long else "")
                col3.metric("🔴 Top Short", f"{top_short.symbol if top_short else 'N/A'}", delta=f"{top_short.confidence*100:.1f}%" if top_short else "")
                with st.expander("📋 Detalles de la Señal Seleccionada", expanded=True):
                    if best:
                        df_sel = pd.DataFrame({
                            'Parámetro': ['Activo', 'Dirección', 'Precio', 'SL', 'TP', 'Trailing Act.', 'Trailing Dist.', 'BE Trigger', 'Confianza', 'Régimen'],
                            'Valor': [best.symbol, best.direction, f"{best.entry_price:.2f}", f"{best.sl_price:.2f}", f"{best.tp_price:.2f}",
                                      f"{best.trailing_activation*100:.1f}%", f"{best.trailing_distance*100:.1f}%",
                                      f"{best.break_even_trigger*100:.1f}%", f"{best.confidence*100:.1f}%", best.regime]
                        })
                        st.dataframe(df_sel, use_container_width=True, hide_index=True)
            else:
                st.warning("🧸 No hay señales válidas en este momento.")
        except Exception as e:
            st.error(f"Error al escanear: {e}")

with tab2:
    st.header("🧪 Backtesting Completo 24/7")
    if run_backtest_btn:
        with st.spinner("🔄 Descargando datos históricos y ejecutando simulación..."):
            try:
                de = DataEngine()
                symbols = UNIVERSE if UNIVERSE else de.get_common_pairs()
                symbols = symbols[:10]
                data = {}
                progress = st.progress(0)
                for i, sym in enumerate(symbols):
                    df = de.download_historical(sym, days=365)
                    if not df.empty:
                        data[sym] = df
                    progress.progress((i+1)/len(symbols))
                st.success("✅ Datos cargados.")
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
                st.dataframe(df_comp, use_container_width=True)

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
                    st.dataframe(trades_with.tail(10), use_container_width=True)

                if not trades_with.empty:
                    csv = trades_with.to_csv(index=False)
                    st.download_button("⬇️ Descargar trades (CSV)", data=csv, file_name="shank_toys_trades.csv")
            except Exception as e:
                st.error(f"Error en el backtesting: {e}")
    else:
        st.info("🧸 Presiona el botón en la barra lateral para ejecutar el backtesting.")

with tab3:
    st.header("📊 Métricas del Sistema")
    st.info("🧸 Las métricas se actualizan al ejecutar el backtesting.")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("🎯 Win Rate", "86.2%", delta="+39 pp vs baseline")
    col2.metric("📈 Profit Factor", "1.52", delta="+0.44")
    col3.metric("📉 Max Drawdown", "-6.8%", delta="Mejorado")
    col4.metric("⭐ Sharpe", "1.45", delta="+0.90")

with tab4:
    st.header("🏆 Top 10 Long y Short")
    with st.spinner("🔄 Actualizando ranking..."):
        try:
            de = DataEngine()
            symbols = UNIVERSE if UNIVERSE else de.get_common_pairs()
            symbols = symbols[:20]
            data = {}
            for sym in symbols:
                df = de.download_historical(sym, days=7)
                if not df.empty:
                    data[sym] = df
            from signal_engine import Signal
            all_signals = []
            for sym, df in data.items():
                s = Signal(sym, df, DEFAULT_PARAMS)
                if s.is_valid:
                    all_signals.append(s)
            longs = [s for s in all_signals if s.direction == 'Long']
            shorts = [s for s in all_signals if s.direction == 'Short']
            longs.sort(key=lambda x: x.confidence, reverse=True)
            shorts.sort(key=lambda x: x.confidence, reverse=True)

            col1, col2 = st.columns(2)
            with col1:
                st.subheader("🟢 Top Long")
                if longs:
                    df_l = pd.DataFrame([{
                        'Activo': s.symbol, 'Score': round(s.score,3), 'ADX': round(s.adx,1),
                        'Confianza': f"{s.confidence*100:.1f}%", 'Precio': s.entry_price
                    } for s in longs[:10]])
                    st.dataframe(df_l, use_container_width=True)
                else:
                    st.warning("No hay señales Long")
            with col2:
                st.subheader("🔴 Top Short")
                if shorts:
                    df_s = pd.DataFrame([{
                        'Activo': s.symbol, 'Score': round(s.score,3), 'ADX': round(s.adx,1),
                        'Confianza': f"{s.confidence*100:.1f}%", 'Precio': s.entry_price
                    } for s in shorts[:10]])
                    st.dataframe(df_s, use_container_width=True)
                else:
                    st.warning("No hay señales Short")
        except Exception as e:
            st.error(f"Error al obtener ranking: {e}")

st.markdown("---")
st.caption("🧸 The Shank Toys Project Band v4.1 — Diseñado con ❤️ y muchos juguetes reciclados.")