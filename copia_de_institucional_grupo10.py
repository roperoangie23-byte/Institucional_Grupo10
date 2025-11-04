# 💼 FinSight 2.0 – Analizador Interactivo de Rentabilidad y Riesgo
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

st.set_page_config(page_title="FinSight 2.0", page_icon="💼", layout="wide")

# 💠 Estilos
st.markdown("""
    <style>
    .main { background-color: #F9FAFB; }
    h1, h2, h3 { color: #002B5B; }
    .stButton>button { background-color: #0078D7; color: white; border-radius: 10px; height: 3em; font-weight: bold; }
    footer {visibility: hidden;}
    </style>
""", unsafe_allow_html=True)

st.markdown("<h1 style='text-align: center;'>💼 FinSight 2.0</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Analizador Interactivo de Rentabilidad y Riesgo Empresarial</h4>", unsafe_allow_html=True)
st.markdown("---")

# --------------------------
# Funciones
# --------------------------
def prepare_data(df):
    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
    df["Daily Return"] = df[price_col].pct_change()
    return df, price_col

def calculate_metrics(df):
    avg_return = df["Daily Return"].mean()
    std_dev = df["Daily Return"].std()
    sharpe_ratio = (avg_return / std_dev) * np.sqrt(252) if std_dev != 0 else 0
    return avg_return, std_dev, sharpe_ratio

def display_metrics(avg, std, sharpe):
    col1, col2, col3 = st.columns(3)
    col1.metric("Rentabilidad promedio", f"{avg*100:.2f}%")
    col2.metric("Riesgo (volatilidad)", f"{std*100:.2f}%")
    col3.metric("Índice de Sharpe (anualizado)", f"{sharpe:.2f}")

def plot_interactive_price(df, price_col, ticker):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df.index, y=df[price_col], mode='lines', name=ticker, line=dict(color='#0078D7')))
    fig.update_layout(title=f"Precio histórico de {ticker}", xaxis_title="Fecha", yaxis_title="Precio ($)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

def plot_interactive_returns(df, ticker):
    fig = px.histogram(df, x="Daily Return", nbins=50, title=f"Distribución de retornos diarios - {ticker}", marginal="box", color_discrete_sequence=['#009688'])
    st.plotly_chart(fig, use_container_width=True)

def plot_comparative(df1, df2, price1, price2, ticker1, ticker2):
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df1.index, y=df1[price1], mode='lines', name=ticker1, line=dict(color='#0078D7')))
    fig.add_trace(go.Scatter(x=df2.index, y=df2[price2], mode='lines', name=ticker2, line=dict(color='#FF5733')))
    fig.update_layout(title="Comparación de precios históricos", xaxis_title="Fecha", yaxis_title="Precio ($)", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)

def plot_scatter_returns(df1, df2, ticker1, ticker2):
    fig = px.scatter(x=df1["Daily Return"], y=df2["Daily Return"],
                     labels={"x": f"Rendimientos {ticker1}", "y": f"Rendimientos {ticker2}"},
                     title="Correlación de rendimientos", trendline="ols")
    st.plotly_chart(fig, use_container_width=True)

# --------------------------
# Navegación
# --------------------------
opcion = st.sidebar.radio("Selecciona una vista:", ["Análisis individual", "Análisis comparativo"])

# --------------------------
# Análisis individual
# --------------------------
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
            data, price_col = prepare_data(data)
            avg, std, sharpe = calculate_metrics(data)
            display_metrics(avg, std, sharpe)
            st.markdown("---")
            plot_interactive_price(data, price_col, ticker)
            plot_interactive_returns(data, ticker)
            st.subheader("Últimos datos descargados")
            st.dataframe(data.tail(10), use_container_width=True)

# --------------------------
# Análisis comparativo
# --------------------------
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
            data1, price1 = prepare_data(data1)
            data2, price2 = prepare_data(data2)
            avg1, std1, sharpe1 = calculate_metrics(data1)
            avg2, std2, sharpe2 = calculate_metrics(data2)
            display_metrics(avg1, std1, sharpe1)
            display_metrics(avg2, std2, sharpe2)
            plot_comparative(data1, data2, price1, price2, ticker1, ticker2)
            plot_scatter_returns(data1, data2, ticker1, ticker2)

            corr = data1["Daily Return"].corr(data2["Daily Return"])
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

