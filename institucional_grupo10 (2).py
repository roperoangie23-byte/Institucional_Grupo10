# -*- coding: utf-8 -*-
"""institucional_grupo10.py"""

# ============================
# IMPORTACIÓN DE LIBRERÍAS
# ============================
import streamlit as st
import pandas as pd
import yfinance as yf
import matplotlib.pyplot as plt

# ============================
# ENCABEZADO
# ============================
with st.container():
    st.markdown(
        """
        <h1 style='text-align: center; 
                   color: #0056D2; 
                   font-weight: bold; 
                   text-shadow: 2px 2px 4px #A9CCE3;'>
            BIENVENIDOS AL GRUPO 10 💼
        </h1>
        """,
        unsafe_allow_html=True
    )

st.header("Análisis de Rentabilidad y Riesgo 📊")
st.write("""
Este proyecto analiza el comportamiento financiero de **tres grandes empresas colombianas**.  
A través de indicadores como la **rentabilidad esperada**, la **volatilidad** y el **Ratio de Sharpe**,  
evaluamos la relación entre riesgo y retorno para identificar el portafolio más eficiente. 💼📈
""")

# ============================
# EMPRESAS COLOMBIANAS (TICKERS)
# ============================
lista_tickers = {
    "Ecopetrol": "ECOPETROL.BO",
    "Bancolombia": "CIB",          # ADR en NYSE
    "Grupo Sura": "GIVSY"          # ADR en OTC
}

# Multiselector
tickers_seleccionados = st.multiselect("Seleccione una o más empresas:", list(lista_tickers.keys()))

# Imagen decorativa
st.image(
    "https://cdn.pixabay.com/photo/2017/06/16/07/37/stock-exchange-2408858_1280.jpg",
    use_container_width=True
)

# ============================
# BOTÓN Y CÁLCULOS
# ============================
if st.button("Calcular Rentabilidad y Riesgo"):
    if not tickers_seleccionados:
        st.warning("⚠️ Debes seleccionar al menos una empresa para continuar.")
    else:
        tickers_yf = [lista_tickers[t] for t in tickers_seleccionados]

        # Descargar datos históricos (últimos 6 meses)
        data = yf.download(tickers=tickers_yf, period="6mo")["Close"]

        # Calcular rentabilidad diaria
        rent_diaria = data.pct_change().dropna()

        # Métricas
        rent_promedio = rent_diaria.mean() * 252
        riesgo = rent_diaria.std() * (252 ** 0.5)
        sharpe = rent_promedio / riesgo

        # Tabla resumen
        resumen = pd.DataFrame({
            "Rentabilidad esperada (%)": rent_promedio * 100,
            "Riesgo (Volatilidad %)": riesgo * 100,
            "Ratio Sharpe": sharpe
        })

        st.subheader("📋 Comparación de Empresas")
        st.dataframe(resumen.style.format("{:.2f}"))

        # ============================
        # TIPO DE GRÁFICO
        # ============================
        tipo_grafico = st.radio(
            "Seleccione el tipo de gráfico a visualizar:",
            ("Dispersión (Riesgo vs Rentabilidad)", "Barras", "Torta")
        )

        # Gráfico de dispersión
        if tipo_grafico == "Dispersión (Riesgo vs Rentabilidad)":
            fig, ax = plt.subplots()
            ax.scatter(riesgo * 100, rent_promedio * 100, color="#0056D2", s=80)
            for i, txt in enumerate(resumen.index):
                ax.annotate(txt, (riesgo[i] * 100, rent_promedio[i] * 100))
            ax.set_xlabel("Riesgo (Volatilidad %)")
            ax.set_ylabel("Rentabilidad Esperada (%)")
            ax.set_title("Rendimiento vs Riesgo - Empresas Colombianas")
            st.pyplot(fig)

        # Gráfico de barras
        elif tipo_grafico == "Barras":
            st.bar_chart(resumen[["Rentabilidad esperada (%)", "Riesgo (Volatilidad %)"]])

        # Gráfico de torta
        elif tipo_grafico == "Torta":
            fig, ax = plt.subplots()
            ax.pie(
                resumen["Rentabilidad esperada (%)"],
                labels=resumen.index,
                autopct="%1.1f%%",
                startangle=90,
                colors=["#0056D2", "#1E90FF", "#87CEFA"]
            )
            ax.set_title("Proporción de Rentabilidad entre Empresas Colombianas")
            st.pyplot(fig)

else:
    st.info("💡 Presiona el botón para calcular la rentabilidad y el riesgo de las empresas seleccionadas.")

