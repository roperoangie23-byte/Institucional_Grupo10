# =====================================================
# FinSight 💼 - Analizador de Rentabilidad y Riesgo Empresarial
# =====================================================

import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import yfinance as yf
from datetime import datetime

# =====================================================
# CONFIGURACIÓN INICIAL
# =====================================================
st.set_page_config(page_title="FinSight", page_icon="💼", layout="wide")

st.markdown("""
    <h1 style='text-align:center; color:#0078D7;'>💼 FinSight</h1>
    <h3 style='text-align:center; color:#FF69B4;'>Analizador de Rentabilidad y Riesgo Empresarial</h3>
    <hr>
""", unsafe_allow_html=True)

# =====================================================
# MENÚ PRINCIPAL
# =====================================================
opcion = st.sidebar.selectbox(
    "Selecciona el tipo de análisis",
    ["Análisis individual", "Análisis comparativo"]
)

# =====================================================
# FUNCIÓN AUXILIAR PARA DESCARGAR DATOS
# =====================================================
def descargar_datos(ticker, start, end):
    """
    Descarga los datos de Yahoo Finance y aplana columnas si es necesario.
    """
    df = yf.download(ticker, start=start, end=end, progress=False)

    # Aplanar columnas si son MultiIndex
    if isinstance(df.columns, pd.MultiIndex):
        df.columns = df.columns.get_level_values(0)

    return df


# =====================================================
# VISTA 1: ANÁLISIS INDIVIDUAL
# =====================================================
if opcion == "Análisis individual":
    st.sidebar.header("Configuración del análisis")
    ticker = st.sidebar.text_input("Símbolo de la empresa (Ticker):", "AAPL")
    start_date = st.sidebar.date_input("Fecha inicial:", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("Fecha final:", pd.to_datetime("2024-12-31"))

    if st.sidebar.button("Analizar"):
        data = descargar_datos(ticker, start_date, end_date)

        if data.empty:
            st.error("No se encontraron datos para el ticker ingresado.")
        else:
            st.success(f"Datos cargados correctamente para **{ticker}** ✅")

            # Cálculos
            if "Adj Close" in data.columns:
                data["Daily Return"] = data["Adj Close"].pct_change()
            else:
                st.error("El dataset no contiene la columna 'Adj Close'. Verifica el ticker.")
                st.stop()

            avg_return = data["Daily Return"].mean()
            volatility = data["Daily Return"].std()
            cumulative_return = (1 + data["Daily Return"]).prod() - 1

            # Mostrar métricas
            col1, col2, col3 = st.columns(3)
            col1.metric("Rentabilidad promedio diaria", f"{avg_return*100:.2f}%")
            col2.metric("Volatilidad", f"{volatility*100:.2f}%")
            col3.metric("Rentabilidad acumulada", f"{cumulative_return*100:.2f}%")

            # Gráfico de precios
            st.subheader("📈 Evolución del precio ajustado")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(data["Adj Close"], label=ticker, color="#0078D7", linewidth=2)
            ax.set_title(f"Evolución histórica del precio - {ticker}")
            ax.legend()
            st.pyplot(fig)

            # Distribución de rendimientos
            st.subheader("📊 Distribución de los rendimientos diarios")
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            sns.histplot(data["Daily Return"].dropna(), bins=40, kde=True, color="#FF69B4", ax=ax2)
            ax2.set_title("Distribución de rendimientos")
            st.pyplot(fig2)

# =====================================================
# VISTA 2: ANÁLISIS COMPARATIVO
# =====================================================
elif opcion == "Análisis comparativo":
    st.sidebar.header("Configuración comparativa")
    tickers_input = st.sidebar.text_input(
        "Empresas (separa los tickers con comas):",
        "AAPL, MSFT, NFLX, IBM"
    )
    start_date = st.sidebar.date_input("Fecha inicial:", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("Fecha final:", pd.to_datetime("2024-12-31"))

    if st.sidebar.button("Comparar empresas"):
        tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

        price_dfs = {}
        for ticker in tickers:
            df = descargar_datos(ticker, start_date, end_date)
            if not df.empty:
                if "Adj Close" in df.columns:
                    df["Daily Return"] = df["Adj Close"].pct_change()
                    price_dfs[ticker] = df
                else:
                    st.warning(f"⚠️ El ticker {ticker} no contiene columna 'Adj Close'.")
            else:
                st.warning(f"No se encontraron datos para {ticker}")

        if len(price_dfs) < 2:
            st.error("Por favor, ingresa al menos dos tickers válidos.")
        else:
            st.success(f"Comparando empresas: {', '.join(price_dfs.keys())}")

            # Crear DataFrame conjunto de precios
            prices = pd.DataFrame({t: df["Adj Close"] for t, df in price_dfs.items()})
            returns = prices.pct_change().dropna()

            # Mostrar métricas
            avg_returns = returns.mean() * 100
            volatilities = returns.std() * 100

            st.subheader("📊 Métricas comparativas")
            metrics_df = pd.DataFrame({
                "Rentabilidad promedio (%)": avg_returns.round(2),
                "Volatilidad (%)": volatilities.round(2)
            })
            st.dataframe(metrics_df.style.highlight_max(color="#FF69B4", axis=0))

            # Gráfico comparativo
            st.subheader("📈 Evolución de precios ajustados")
            fig, ax = plt.subplots(figsize=(10, 5))
            for ticker in prices.columns:
                ax.plot(prices[ticker], label=ticker, linewidth=2)
            ax.set_title("Evolución histórica de precios ajustados")
            ax.legend()
            st.pyplot(fig)

            # Correlación
            st.subheader("🔗 Correlación de rendimientos")
            fig2, ax2 = plt.subplots(figsize=(8, 5))
            sns.heatmap(returns.corr(), annot=True, cmap="coolwarm", ax=ax2)
            st.pyplot(fig2)

            # Conclusión automática
            st.markdown("### 🧠 Conclusión del análisis")
            avg_corr = returns.corr().mean().mean()
            if avg_corr > 0.7:
                st.info("Las empresas tienen una **alta correlación** — tienden a moverse juntas.")
            elif avg_corr > 0.3:
                st.warning("Las empresas presentan una **correlación moderada** — hay cierta relación.")
            else:
                st.success("Las empresas muestran **baja correlación** — buena oportunidad de diversificación.")


