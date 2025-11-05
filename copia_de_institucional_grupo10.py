# -- coding: utf-8 --
"""
FinSight PRO+ — Analizador de Rentabilidad y Riesgo (versión con mejoras avanzadas y visual premium)
Autor: Angie (adaptado)
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from datetime import datetime

sns.set_style("whitegrid")

# -------------------------
# Configuración página
# -------------------------
st.set_page_config(page_title="FinSight PRO+", page_icon="💼", layout="wide")

# -------------------------
# Estilos (modo claro/oscuro básico)
# -------------------------
def set_theme(dark_mode: bool):
    if dark_mode:
        st.markdown(
            "<style>body{background-color:#0b1220;color:#e6eef8} .stMetric {color: #e6eef8}</style>",
            unsafe_allow_html=True,
        )
    else:
        st.markdown(
            "<style>body{background-color:#F9FAFB;color:#0b1220} .stMetric {color: #0b1220}</style>",
            unsafe_allow_html=True,
        )

# -------------------------
# Sidebar - Inputs
# -------------------------
st.sidebar.header("⚙ Configuración")

# Tickers (entrada única, separados por comas)
tickers_input = st.sidebar.text_input(
    "Empresas (separa por comas):", value="AAPL, MSFT, NVDA"
)
tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

# Rango de fechas
start_date = st.sidebar.date_input("Fecha inicio", pd.to_datetime("2020-01-01"))
end_date = st.sidebar.date_input("Fecha fin", pd.to_datetime(datetime.today().date()))

# Visual + parámetros
dark_mode = st.sidebar.checkbox("🌙 Modo oscuro", value=False)
set_theme(dark_mode)

initial_investment = st.sidebar.number_input(
    "Inversión inicial (USD) para rendimiento acumulado", min_value=1, value=1000, step=100
)

show_montecarlo = st.sidebar.checkbox("🔮 Simulación Monte Carlo (opcional)", value=False)
mc_sims = st.sidebar.slider("N° simulaciones (Monte Carlo)", 50, 1000, value=200, step=50)
mc_days = st.sidebar.slider("Horizonte (días) Monte Carlo", 30, 252, value=252, step=30)

st.sidebar.markdown("---")
st.sidebar.markdown("Desarrollado por **Angie, Jhony y Dayana** — FinSight PRO+")

# -------------------------
# Header
# -------------------------
st.markdown("<h1 style='text-align:center;'>💼 FinSight PRO+</h1>", unsafe_allow_html=True)
st.markdown(
    "<h4 style='text-align:center;color:gray;'>Analizador avanzado de rentabilidad, riesgo y estrategias</h4>",
    unsafe_allow_html=True,
)
st.markdown("---")

# -------------------------
# Funciones utilitarias
# -------------------------
def download_ticker(ticker, start, end):
    try:
        df = yf.download(ticker, start=start, end=end, progress=False)
        if df.empty:
            return None
        # Preferir 'Adj Close' si existe
        price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
        df = df[[price_col]].rename(columns={price_col: "AdjClose"})
        df.index = pd.to_datetime(df.index)
        return df
    except Exception:
        return None

def calc_metrics(df_returns):
    # df_returns: Series of daily returns
    daily = df_returns.dropna()
    mean_daily = daily.mean()
    vol_daily = daily.std()
    ann_return = mean_daily * 252
    ann_vol = vol_daily * np.sqrt(252)
    sharpe = ann_return / ann_vol if ann_vol != 0 else np.nan
    # Sortino (downside std)
    negative_returns = daily[daily < 0]
    downside_std = negative_returns.std() * np.sqrt(252) if not negative_returns.empty else np.nan
    sortino = ann_return / downside_std if downside_std and downside_std != 0 else np.nan
    return {
        "mean_daily": mean_daily,
        "vol_daily": vol_daily,
        "ann_return": ann_return,
        "ann_vol": ann_vol,
        "sharpe": sharpe,
        "sortino": sortino,
    }

def compute_beta_alpha(returns_asset, returns_market):
    # Align
    df = pd.concat([returns_asset, returns_market], axis=1).dropna()
    if df.shape[0] < 2:
        return np.nan, np.nan
    cov = np.cov(df.iloc[:,0], df.iloc[:,1])
    beta = cov[0,1] / cov[1,1] if cov[1,1] != 0 else np.nan
    alpha = df.iloc[:,0].mean()*252 - beta * (df.iloc[:,1].mean()*252)
    return beta, alpha

def to_csv_bytes(df: pd.DataFrame):
    buffer = BytesIO()
    df.to_csv(buffer, index=True)
    buffer.seek(0)
    return buffer

# -------------------------
# Data download for selected tickers
# -------------------------
if st.sidebar.button("🚀 Ejecutar análisis"):
    if len(tickers) < 2:
        st.warning("Ingresa al menos 2 tickers para comparar (separados por comas).")
    else:
        status = st.info("Descargando datos... espera un momento.")
        # Descargar ticker por ticker (más robusto que multiindex)
        price_dfs = {}
        failed = []
        for t in tickers:
            df = download_ticker(t, start_date, end_date)
            if df is None:
                failed.append(t)
            else:
                price_dfs[t] = df

        # Descargar índice de mercado S&P500 para Beta/Alpha
        market_df = download_ticker("^GSPC", start_date, end_date)

        if len(price_dfs) < 2:
            status.error("No se encontraron suficientes datos válidos. Revisa los tickers ingresados.")
            if failed:
                st.error(f"Tickers inválidos o sin datos: {', '.join(failed)}")
        else:
            status.success(f"Datos descargados para: {', '.join(price_dfs.keys())}")
            # Construir DataFrame de precios y retornos
            prices = pd.DataFrame({t: df["AdjClose"] for t, df in price_dfs.items()})
            returns = prices.pct_change()

            # Normalized prices (inicio 100) y rendimiento acumulado
            norm_prices = prices / prices.iloc[0] * 100
            accum = (1 + returns).cumprod() * initial_investment

            # --- Estadísticas por ticker ---
            stats = []
            for t in prices.columns:
                m = calc_metrics(returns[t])
                beta, alpha = (np.nan, np.nan)
                if market_df is not None:
                    # build market returns aligned
                    market_returns = market_df["AdjClose"].pct_change()
                    beta, alpha = compute_beta_alpha(returns[t], market_returns)
                stats.append({
                    "Ticker": t,
                    "Annual Return": m["ann_return"],
                    "Annual Volatility": m["ann_vol"],
                    "Sharpe": m["sharpe"],
                    "Sortino": m["sortino"],
                    "Beta": beta,
                    "Alpha": alpha,
                })
            stats_df = pd.DataFrame(stats).set_index("Ticker")

            # Mostrar tarjetas principales: top performer y menor riesgo
            st.markdown("### 📊 Resumen rápido")
            best = stats_df["Annual Return"].idxmax()
            worst_vol = stats_df["Annual Volatility"].idxmin()
            col1, col2, col3 = st.columns(3)
            col1.markdown(f"<div style='padding:10px;border-radius:10px;background:#E8F4FF;text-align:center;'><h4>🏆 Mejor rendimiento</h4><b>{best}</b><p>{stats_df.loc[best,'Annual Return']*100:.2f}% anual</p></div>", unsafe_allow_html=True)
            col2.markdown(f"<div style='padding:10px;border-radius:10px;background:#FFF0F6;text-align:center;'><h4>🛡️ Menor volatilidad</h4><b>{worst_vol}</b><p>{stats_df.loc[worst_vol,'Annual Volatility']*100:.2f}% anual</p></div>", unsafe_allow_html=True)
            col3.markdown(f"<div style='padding:10px;border-radius:10px;background:#F6FFF0;text-align:center;'><h4>📈 Promedio Sharpe</h4><b>{stats_df['Sharpe'].mean():.2f}</b><p>Relación riesgo/retorno</p></div>", unsafe_allow_html=True)

            st.markdown("---")

            # --- Panel de gráficos: precios normalizados y acumulado ---
            tab1, tab2, tab3 = st.tabs(["📈 Precios normalizados", "💰 Rendimiento acumulado", "🔍 Correlación"])
            with tab1:
                st.subheader("Precios normalizados (base 100)")
                fig, ax = plt.subplots(figsize=(10,5))
                for t in norm_prices.columns:
                    ax.plot(norm_prices[t], label=t, linewidth=2)
                ax.set_ylabel("Índice (base 100)")
                ax.legend()
                st.pyplot(fig)

            with tab2:
                st.subheader(f"Rendimiento acumulado (inversión inicial: ${initial_investment})")
                fig2, ax2 = plt.subplots(figsize=(10,5))
                for t in accum.columns:
                    ax2.plot(accum[t], label=t, linewidth=2)
                ax2.set_ylabel("Valor de la inversión (USD)")
                ax2.legend()
                st.pyplot(fig2)

            with tab3:
                st.subheader("Matriz de correlación de retornos")
                corr = returns.corr()
                fig3, ax3 = plt.subplots(figsize=(7,6))
                sns.heatmap(corr, annot=True, cmap="coolwarm", center=0, ax=ax3)
                st.pyplot(fig3)

            st.markdown("---")

            # --- Scatter Riesgo vs Retorno ---
            st.subheader("🔎 Riesgo vs Rentabilidad (anualizadas)")
            fig4, ax4 = plt.subplots(figsize=(8,6))
            for t in stats_df.index:
                ax4.scatter(stats_df.loc[t,"Annual Volatility"], stats_df.loc[t,"Annual Return"],
                            s=max(50, (stats_df.loc[t,"Sharpe"] or 0)*60 + 20), label=t, alpha=0.85)
                ax4.annotate(t, (stats_df.loc[t,"Annual Volatility"], stats_df.loc[t,"Annual Return"]))
            ax4.set_xlabel("Volatilidad anual")
            ax4.set_ylabel("Rentabilidad anual")
            ax4.grid(alpha=0.3)
            st.pyplot(fig4)

            st.markdown("---")

            # --- Mostrar tabla de estadísticas y permitir descarga ---
            st.subheader("📋 Tabla resumen de métricas")
            display_stats = stats_df.copy()
            display_stats["Annual Return"] = display_stats["Annual Return"].map("{:.2%}".format)
            display_stats["Annual Volatility"] = display_stats["Annual Volatility"].map("{:.2%}".format)
            display_stats["Sharpe"] = display_stats["Sharpe"].map("{:.2f}".format)
            display_stats["Sortino"] = display_stats["Sortino"].map(lambda x: "{:.2f}".format(x) if not pd.isna(x) else "N/A")
            display_stats["Beta"] = display_stats["Beta"].map(lambda x: "{:.2f}".format(x) if not pd.isna(x) else "N/A")
            display_stats["Alpha"] = display_stats["Alpha"].map(lambda x: "{:.2%}".format(x) if not pd.isna(x) else "N/A")
            st.dataframe(display_stats, use_container_width=True)

            csv_buffer = to_csv_bytes(stats_df)
            st.download_button("📥 Descargar métricas (CSV)", data=csv_buffer, file_name="finsight_metrics.csv", mime="text/csv")

            # --- Monte Carlo opcional ---
            if show_montecarlo:
                st.markdown("---")
                st.subheader("🔮 Simulación Monte Carlo (proyección de precios)")
                last_prices = prices.iloc[-1]
                fig_mc, ax_mc = plt.subplots(figsize=(10,5))
                for t in prices.columns:
                    sims = np.zeros((mc_days, mc_sims))
                    mu = returns[t].mean()
                    sigma = returns[t].std()
                    for i in range(mc_sims):
                        daily_rets = np.random.normal(mu, sigma, mc_days)
                        sims[:, i] = last_prices[t] * np.cumprod(1 + daily_rets)
                    ax_mc.plot(sims, linewidth=0.5, alpha=0.1)
                ax_mc.set_title("Simulaciones Monte Carlo (trayectorias)")
                st.pyplot(fig_mc)

            # --- Resumen ejecutivo automático ---
            st.markdown("---")
            st.subheader("🧾 Resumen ejecutivo (interpretación automática)")
            # choose top return and lowest volatility
            text = f"Entre {start_date} y {end_date}, se analizaron {', '.join(stats_df.index)}. "
            text += f"El mejor rendimiento anual promedio lo presentó **{best}** ({stats_df.loc[best,'Annual Return']*100:.2f}%). "
            text += f"La menor volatilidad anual correspondió a **{worst_vol}** ({stats_df.loc[worst_vol,'Annual Volatility']*100:.2f}%). "
            if stats_df['Sharpe'].mean() > 1:
                text += "En promedio los activos muestran una buena relación riesgo-retorno (Sharpe > 1). "
            else:
                text += "La relación riesgo-retorno promedio es moderada (Sharpe cercano a 1 o inferior). "
            st.markdown(text)

            # final note
            st.success("✅ Análisis completado — revisa las pestañas y descarga las métricas si lo deseas.")


