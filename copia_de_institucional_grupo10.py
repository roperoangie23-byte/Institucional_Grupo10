# 💼 FinSight – Analizador de Rentabilidad y Riesgo Empresarial (Versión extendida)
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

st.set_page_config(page_title="FinSight", page_icon="💼", layout="wide")

# 💠 Estilos personalizados
st.markdown("""
    <style>
    .main {
        background-color: #F9FAFB;
    }
    h1, h2, h3 {
        color: #002B5B;
    }
    .stButton>button {
        background-color: #0078D7;
        color: white;
        border-radius: 10px;
        height: 3em;
        font-weight: bold;
    }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

# 🧭 Encabezado principal
st.markdown("<h1 style='text-align: center;'>💼 FinSight</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Analizador de Rentabilidad y Riesgo Empresarial</h4>", unsafe_allow_html=True)
st.markdown("---")

# 📂 Navegación
opcion = st.sidebar.radio("Selecciona una vista:", ["Análisis individual", "Análisis comparativo"])

# =====================================================
# 📈 VISTA 1: ANÁLISIS INDIVIDUAL
# =====================================================
if opcion == "Análisis individual":
    st.sidebar.header("⚙ Configuración de análisis individual")
    ticker = st.sidebar.text_input("📊 Ticker de la empresa:", "AAPL")
    start_date = st.sidebar.date_input("📅 Fecha inicial:", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("📅 Fecha final:", pd.to_datetime("2024-12-31"))

    if st.sidebar.button("Analizar empresa"):
        data = yf.download(ticker, start=start_date, end=end_date, progress=False)
        if data.empty:
            st.error("❌ No se encontraron datos para el ticker especificado.")
        else:
            st.success(f"✅ Datos descargados correctamente para *{ticker}*")

            # Cálculos
            price_col = "Adj Close" if "Adj Close" in data.columns else "Close"
            data["Daily Return"] = data[price_col].pct_change()
            avg_return = data["Daily Return"].mean()
            std_dev = data["Daily Return"].std()
            sharpe_ratio = avg_return / std_dev if std_dev != 0 else 0

            # Mostrar resultados
            col1, col2, col3 = st.columns(3)
            col1.metric("Rentabilidad promedio", f"{avg_return*100:.2f}%")
            col2.metric("Riesgo (volatilidad)", f"{std_dev*100:.2f}%")
            col3.metric("Índice de Sharpe", f"{sharpe_ratio:.2f}")

            st.markdown("---")

            # Gráfico de precios
            st.subheader("Evolución del precio ajustado")
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.plot(data[price_col], color='#0078D7', linewidth=2)
            ax.set_title(f"Precio histórico de {ticker}")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Precio ($)")
            ax.grid(alpha=0.3)
            st.pyplot(fig)

            # 📊 Distribución de retornos
            st.subheader("📊 Distribución de los rendimientos diarios")
            fig2, ax2 = plt.subplots(figsize=(8, 4))
            sns.histplot(data["Daily Return"].dropna(), bins=30, kde=True, ax=ax2, color='#009688')
            st.pyplot(fig2)

            #  Datos recientes
            st.subheader("Últimos datos descargados")
            st.dataframe(data.tail(10), use_container_width=True)

# =====================================================
#  VISTA 2: ANÁLISIS COMPARATIVO (versión optimizada)
# =====================================================
elif opcion == "Análisis comparativo":
    st.sidebar.header("Configuración comparativa")

    # 🔹 Campo único para varios tickers separados por comas
    tickers_input = st.sidebar.text_input("Empresas (separa por comas):", "AAPL, MSFT, NFLX")
    start_date = st.sidebar.date_input("Fecha inicial:", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("Fecha final:", pd.to_datetime("2024-12-31"))

    # Convertir a lista limpia
    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if st.sidebar.button("Comparar empresas"):
        if len(tickers) < 2:
            st.warning("Por favor, ingresa al menos dos empresas para comparar.")
        else:
            # Descargar datos para todos los tickers
            st.info("Descargando datos...")
            data = yf.download(tickers, start=start_date, end=end_date, progress=False, group_by="ticker")

            # Verificar si algún ticker falló
            if data.empty:
                st.error("❌ No se encontraron datos para los tickers ingresados.")
            else:
                st.success(f"Comparando: {', '.join(tickers)}")

                # Preparar DataFrame combinado de retornos diarios
                daily_returns = pd.DataFrame()
                for ticker in tickers:
                    df = data[ticker]
                    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                    daily_returns[ticker] = df[price_col].pct_change()

                # 📊 Métricas resumen
                avg_returns = daily_returns.mean() * 100
                std_devs = daily_returns.std() * 100
                corr_matrix = daily_returns.corr()

                st.subheader("📈 Indicadores de Rentabilidad y Riesgo")
                for ticker in tickers:
                    st.metric(f"{ticker} – Rentabilidad promedio", f"{avg_returns[ticker]:.2f}%")

                # 📉 Gráfico comparativo de precios
                st.subheader("Comparación de precios históricos")
                fig, ax = plt.subplots(figsize=(10, 5))
                for ticker in tickers:
                    df = data[ticker]
                    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                    ax.plot(df[price_col], label=ticker, linewidth=2)
                ax.legend()
                ax.set_title("Evolución de precios ajustados")
                ax.set_xlabel("Fecha")
                ax.set_ylabel("Precio ($)")
                st.pyplot(fig)

                # 🔍 Matriz de correlación visual
                st.subheader("🔗 Matriz de correlación entre rendimientos")
                fig2, ax2 = plt.subplots(figsize=(6, 5))
                sns.heatmap(corr_matrix, annot=True, cmap="Blues", fmt=".2f", ax=ax2)
                st.pyplot(fig2)

                # 🧠 Conclusión automática
                st.markdown("### 🧠 Conclusión del análisis")
                avg_corr = corr_matrix.mean().mean()
                if avg_corr > 0.7:
                    st.info("Los rendimientos de las empresas están **fuertemente correlacionados** — se mueven en la misma dirección.")
                elif avg_corr > 0.3:
                    st.warning("Existe una **correlación moderada** entre las empresas analizadas.")
                else:
                    st.success("Las empresas tienen **baja correlación**, ideal para **diversificar el portafolio**.")


# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>© 2025 FinSight | Desarrollado por Angie, Jhony y Dayana</p>", unsafe_allow_html=True)

