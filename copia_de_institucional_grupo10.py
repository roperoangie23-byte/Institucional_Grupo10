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
#  VISTA 2: ANÁLISIS COMPARATIVO
# =====================================================
elif opcion == "Análisis comparativo":
    st.sidebar.header("Configuración comparativa")
    ticker1 = st.sidebar.text_input("Empresa 1:", "AAPL")
    ticker2 = st.sidebar.text_input("Empresa 2:", "MSFT")
    start_date = st.sidebar.date_input("Fecha inicial:", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("Fecha final:", pd.to_datetime("2024-12-31"))

    if st.sidebar.button("Comparar empresas"):
        data1 = yf.download(ticker1, start=start_date, end=end_date, progress=False)
        data2 = yf.download(ticker2, start=start_date, end=end_date, progress=False)

        if data1.empty or data2.empty:
            st.error("Verifica los tickers, no se encontraron datos.")
        else:
            st.success(f"Comparando *{ticker1}* y *{ticker2}*")

            # Cálculos
            for df in [data1, data2]:
                price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                df["Daily Return"] = df[price_col].pct_change()

            # Estadísticas
            avg1, avg2 = data1["Daily Return"].mean(), data2["Daily Return"].mean()
            std1, std2 = data1["Daily Return"].std(), data2["Daily Return"].std()
            corr = data1["Daily Return"].corr(data2["Daily Return"])

            # Resultados
            col1, col2, col3 = st.columns(3)
            col1.metric(f"Rentabilidad {ticker1}", f"{avg1*100:.2f}%")
            col2.metric(f"Rentabilidad {ticker2}", f"{avg2*100:.2f}%")
            col3.metric("Correlación", f"{corr:.2f}")

            # Gráfico comparativo
            st.subheader("Comparación de precios históricos")
            fig, ax = plt.subplots(figsize=(10, 5))
            for df, ticker in [(data1, ticker1), (data2, ticker2)]:
                price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                ax.plot(df[price_col], label=ticker, linewidth=2)
            ax.set_title("Evolución de precios ajustados")
            ax.legend()
            st.pyplot(fig)
            
            # Distribución conjunta
            st.subheader(" Relación entre los rendimientos")
            fig2, ax2 = plt.subplots(figsize=(7, 5))
            sns.scatterplot(x=data1["Daily Return"], y=data2["Daily Return"], ax=ax2)
            ax2.set_xlabel(f"Rendimientos {ticker1}")
            ax2.set_ylabel(f"Rendimientos {ticker2}")
            ax2.set_title("Correlación de rendimientos")
            st.pyplot(fig2)

            # 🧠 Conclusión automática
            st.markdown("Conclusión del análisis")
            if corr > 0.7:
                st.info(f"Los rendimientos de *{ticker1}* y *{ticker2}* están fuertemente correlacionados — se mueven en la misma dirección.")
            elif corr > 0.3:
                st.warning(f"Existe una correlación moderada entre *{ticker1}* y *{ticker2}*.")
            else:
                st.success(f"Los rendimientos de *{ticker1}* y *{ticker2}* son poco o nada correlacionados — buena opción para diversificar.")

# Footer
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>© 2025 FinSight | Desarrollado por Angie, Jhony y Dayana</p>", unsafe_allow_html=True)

