# 💼 FinSight – Analizador de Rentabilidad y Riesgo Empresarial (Versión Final)
import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
from fpdf import FPDF

# ==========================================
# CONFIGURACIÓN INICIAL
# ==========================================
st.set_page_config(page_title="FinSight", page_icon="💼", layout="wide")

st.markdown("""
    <style>
    .main { background-color: #F9FAFB; }
    h1, h2, h3 { color: #002B5B; }
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

st.markdown("<h1 style='text-align: center;'>💼 FinSight</h1>", unsafe_allow_html=True)
st.markdown("<h4 style='text-align: center; color: gray;'>Analizador de Rentabilidad y Riesgo Empresarial</h4>", unsafe_allow_html=True)
st.markdown("---")

# ==========================================
# FUNCIONES DE EXPORTACIÓN
# ==========================================
def exportar_excel(df):
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=True, sheet_name='FinSight Report')
    return output.getvalue()

def exportar_pdf(df):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", size=12)
    pdf.cell(200, 10, txt="Reporte FinSight – Rentabilidad y Riesgo", ln=True, align='C')
    pdf.ln(10)
    for col in df.columns:
        pdf.cell(60, 10, txt=col, border=1, align='C')
    pdf.ln()
    for i in range(len(df)):
        for val in df.iloc[i]:
            pdf.cell(60, 10, txt=str(val), border=1, align='C')
        pdf.ln()
    pdf_output = BytesIO()
    pdf.output(pdf_output)
    return pdf_output.getvalue()

# ==========================================
# MENÚ PRINCIPAL
# ==========================================
opcion = st.sidebar.radio("Selecciona una vista:", ["Análisis individual", "Análisis comparativo"])

# ==========================================
# 📈 ANÁLISIS INDIVIDUAL
# ==========================================
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

            price_col = "Adj Close" if "Adj Close" in data.columns else "Close"
            data["Daily Return"] = data[price_col].pct_change()
            avg_return = data["Daily Return"].mean()
            std_dev = data["Daily Return"].std()
            risk_free_rate = 0
            sharpe_ratio = (avg_return - risk_free_rate) / std_dev if std_dev != 0 else 0
            vol_anual = std_dev * np.sqrt(252)
            cum_return = (1 + data["Daily Return"]).prod() - 1

            # --- Métricas ---
            col1, col2, col3, col4 = st.columns(4)
            col1.metric("Rentabilidad promedio", f"{avg_return*100:.2f}%")
            col2.metric("Volatilidad diaria", f"{std_dev*100:.2f}%")
            col3.metric("Volatilidad anualizada", f"{vol_anual*100:.2f}%")
            col4.metric("Índice de Sharpe", f"{sharpe_ratio:.2f}")

            st.markdown(f"### 📊 Rentabilidad acumulada: **{cum_return*100:.2f}%**")

            # --- Exportación ---
            resumen_df = pd.DataFrame({
                "Métrica": ["Rentabilidad promedio (%)", "Volatilidad diaria (%)", "Volatilidad anualizada (%)", "Índice de Sharpe", "Rentabilidad acumulada (%)"],
                "Valor": [f"{avg_return*100:.2f}", f"{std_dev*100:.2f}", f"{vol_anual*100:.2f}", f"{sharpe_ratio:.2f}", f"{cum_return*100:.2f}"]
            })

            excel_data = exportar_excel(resumen_df)
            pdf_data = exportar_pdf(resumen_df)
            colx, coly = st.columns(2)
            colx.download_button("⬇️ Descargar reporte Excel", data=excel_data, file_name=f"FinSight_{ticker}.xlsx")
            coly.download_button("📄 Descargar reporte PDF", data=pdf_data, file_name=f"FinSight_{ticker}.pdf")

            # --- Gráficos ---
            st.subheader("📈 Evolución del precio ajustado")
            fig, ax = plt.subplots(figsize=(10,5))
            ax.plot(data[price_col], color='#0078D7', linewidth=2)
            ax.set_title(f"Precio histórico de {ticker}")
            ax.set_xlabel("Fecha")
            ax.set_ylabel("Precio ($)")
            st.pyplot(fig)

            st.subheader("📊 Distribución de los rendimientos diarios")
            fig2, ax2 = plt.subplots(figsize=(8,4))
            sns.histplot(data["Daily Return"].dropna(), bins=40, kde=True, color='#009688', ax=ax2)
            st.pyplot(fig2)

# ==========================================
# 📊 ANÁLISIS COMPARATIVO
# ==========================================
elif opcion == "Análisis comparativo":
    st.sidebar.header("⚙ Configuración comparativa")
    tickers_input = st.sidebar.text_input("Empresas (separa por comas):", "AAPL, MSFT, NFLX, IBM")
    start_date = st.sidebar.date_input("Fecha inicial:", pd.to_datetime("2020-01-01"))
    end_date = st.sidebar.date_input("Fecha final:", pd.to_datetime("2024-12-31"))
    inversion_inicial = st.sidebar.number_input("💰 Inversión inicial ($):", value=10000.0, min_value=100.0)
    frecuencia = st.sidebar.selectbox("📅 Frecuencia temporal:", ["Diaria", "Semanal", "Mensual"])
    intervalo = {"Diaria": "1d", "Semanal": "1wk", "Mensual": "1mo"}[frecuencia]

    tickers = [t.strip().upper() for t in tickers_input.split(",") if t.strip()]

    if st.sidebar.button("Comparar empresas"):
        if len(tickers) < 2:
            st.warning("Por favor, ingresa al menos dos empresas para comparar.")
        else:
            st.info("Descargando datos...")
            data = yf.download(tickers, start=start_date, end=end_date, interval=intervalo, progress=False, group_by="ticker")

            if data.empty:
                st.error("❌ No se encontraron datos para los tickers ingresados.")
            else:
                st.success(f"Comparando: {', '.join(tickers)}")

                # Calcular retornos
                daily_returns = pd.DataFrame()
                for ticker in tickers:
                    df = data[ticker]
                    price_col = "Adj Close" if "Adj Close" in df.columns else "Close"
                    daily_returns[ticker] = df[price_col].pct_change()

                avg_returns = daily_returns.mean()
                std_devs = daily_returns.std()
                vol_anual = std_devs * np.sqrt(252)
                sharpe_ratios = (avg_returns - 0) / std_devs
                corr_matrix = daily_returns.corr()

                # --- Valor del portafolio ---
                retornos_acum = (1 + daily_returns).cumprod()
                valor_portafolio = inversion_inicial * retornos_acum

                # --- Tabla resumen ---
                metrics_df = pd.DataFrame({
                    "Rentabilidad promedio (%)": avg_returns * 100,
                    "Volatilidad diaria (%)": std_devs * 100,
                    "Volatilidad anualizada (%)": vol_anual * 100,
                    "Índice de Sharpe": sharpe_ratios
                }).round(2)
                st.dataframe(metrics_df.style.highlight_max(color="#FF69B4", axis=0))

                # --- Descargas ---
                excel_data = exportar_excel(metrics_df)
                pdf_data = exportar_pdf(metrics_df)
                colx, coly = st.columns(2)
                colx.download_button("⬇️ Descargar comparativo Excel", data=excel_data, file_name="FinSight_Comparativo.xlsx")
                coly.download_button("📄 Descargar comparativo PDF", data=pdf_data, file_name="FinSight_Comparativo.pdf")

                # --- Gráficos ---
                st.subheader("📈 Índice de Sharpe por empresa")
                fig3, ax3 = plt.subplots(figsize=(8,4))
                sharpe_ratios.sort_values().plot(kind='bar', color='#009688', ax=ax3)
                st.pyplot(fig3)

                st.subheader("📊 Evolución del valor del portafolio")
                fig4, ax4 = plt.subplots(figsize=(10,5))
                for ticker in tickers:
                    ax4.plot(valor_portafolio.index, valor_portafolio[ticker], label=ticker)
                ax4.set_title("Evolución del valor del portafolio")
                ax4.set_xlabel("Fecha")
                ax4.set_ylabel("Valor ($)")
                ax4.legend()
                st.pyplot(fig4)

                st.subheader("🔗 Matriz de correlación")
                fig5, ax5 = plt.subplots(figsize=(6,5))
                sns.heatmap(corr_matrix, annot=True, cmap="Blues", fmt=".2f", ax=ax5)
                st.pyplot(fig5)

                st.subheader("📈 Diagrama riesgo–retorno (Rendimiento vs Volatilidad)")
                fig6, ax6 = plt.subplots(figsize=(7,5))
                ax6.scatter(std_devs * 100, avg_returns * 100, s=120, color="#0078D7")
                for i, ticker in enumerate(tickers):
                    ax6.text(std_devs[i] * 100 + 0.05, avg_returns[i] * 100, ticker, fontsize=9)
                ax6.set_xlabel("Riesgo (Volatilidad %)")
                ax6.set_ylabel("Rentabilidad promedio (%)")
                ax6.set_title("Diagrama riesgo–retorno")
                st.pyplot(fig6)

# ==========================================
# FOOTER
# ==========================================
st.markdown("---")
st.markdown("<p style='text-align:center; color:gray;'>© 2025 FinSight | Desarrollado por Angie, Jhony y Dayana</p>", unsafe_allow_html=True)


