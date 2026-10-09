import streamlit as st
import pandas as pd
import plotly.express as px
import os

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Asistencias",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

RUTA_BASE = "BASE_DATOS.xlsx"

# ---------------------------------------------------------
# 1. TABLA EXTRAÍDA DIRECTAMENTE DE "RESUMEN_GENERAL"
# ---------------------------------------------------------
datos_resumen_general = [
    {"NOMBRE": "ALEJANDRO RAMOS MAYEN", "HORAS CONTABILIZADAS": "355:07:39", "HORAS RESTANTES": "124:52:21", "AVANCE": "73,98%", "HOJA": "ALEJANDRO R.M"},
    {"NOMBRE": "CESAR YAIR ESPINOSA MARTINEZ", "HORAS CONTABILIZADAS": "281:44:07", "HORAS RESTANTES": "198:15:53", "AVANCE": "58,69%", "HOJA": "CESAR Y.E.M"},
    {"NOMBRE": "CHRISTIAN GONZÁLEZ GUTIÉRREZ", "HORAS CONTABILIZADAS": "353:28:05", "HORAS RESTANTES": "126:31:55", "AVANCE": "73,64%", "HOJA": "CHRISTIAN G.G"},
    {"NOMBRE": "FÁTIMA PACHECO ZACARÍAS", "HORAS CONTABILIZADAS": "443:14:41", "HORAS RESTANTES": "36:45:19", "AVANCE": "92,34%", "HOJA": "FÁTIMA P.Z"},
    {"NOMBRE": "FERNANDO JAVIER RAMIREZ GARCIA", "HORAS CONTABILIZADAS": "327:58:51", "HORAS RESTANTES": "152:01:09", "AVANCE": "68,33%", "HOJA": "FERNANDO J.R.G"},
    {"NOMBRE": "KARLA YAMILET AGUILAR RAMÍREZ", "HORAS CONTABILIZADAS": "319:40:28", "HORAS RESTANTES": "160:19:32", "AVANCE": "66,60%", "HOJA": "KARLA Y.A.R"},
    {"NOMBRE": "KATHERINE MENDEZ MARQUEZ", "HORAS CONTABILIZADAS": "453:48:44", "HORAS RESTANTES": "26:11:16", "AVANCE": "94,54%", "HOJA": "KATHERINE M.M"},
    {"NOMBRE": "LUDWING PINEDA CUEVAS", "HORAS CONTABILIZADAS": "40:43:43", "HORAS RESTANTES": "439:16:17", "AVANCE": "8,49%", "HOJA": "LUDWING P.C"},
    {"NOMBRE": "LUIS FERNANDO CASTILLO GARCÍA", "HORAS CONTABILIZADAS": "344:01:47", "HORAS RESTANTES": "135:58:13", "AVANCE": "71,67%", "HOJA": "LUIS F.C.G"},
    {"NOMBRE": "MARIA NATALIA CABRERA MONJARAS", "HORAS CONTABILIZADAS": "288:26:44", "HORAS RESTANTES": "191:33:16", "AVANCE": "60,09%", "HOJA": "MARIA N.C.M"},
    {"NOMBRE": "MISAEL RIVERA LÓPEZ", "HORAS CONTABILIZADAS": "198:52:14", "HORAS RESTANTES": "281:07:46", "AVANCE": "41,43%", "HOJA": "MISAEL R.L"},
    {"NOMBRE": "RAFAEL EDUARDO LAGUNAS GÓMEZ", "HORAS CONTABILIZADAS": "327:36:46", "HORAS RESTANTES": "152:23:14", "AVANCE": "68,25%", "HOJA": "RAFAEL E.L.G"},
    {"NOMBRE": "CARLOS CRISTOPHER TERRAZAS MARTINEZ", "HORAS CONTABILIZADAS": "32:20:46", "HORAS RESTANTES": "447:39:14", "AVANCE": "6,74%", "HOJA": "CARLOS C.T.M"}
]

df_resumen = pd.DataFrame(datos_resumen_general)

# Conversiones numéricas
def texto_a_segundos(h_str):
    try:
        partes = str(h_str).split(':')
        return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])
    except:
        return 0

df_resumen['HORAS_DECIMAL'] = df_resumen['HORAS CONTABILIZADAS'].apply(texto_a_segundos) / 3600.0
df_resumen['PORCENTAJE_NUMERICO'] = df_resumen['AVANCE'].str.replace('%', '').str.replace(',', '.').astype(float)

# ---------------------------------------------------------
# BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.title("Sistema de Asistencias")
st.sidebar.markdown("---")
opcion_vista = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Resumen General", "👤 Panel Individual de Integrante"]
)

# ---------------------------------------------------------
# VISTA 1: RESUMEN GENERAL
# ---------------------------------------------------------
if opcion_vista == "📊 Resumen General":
    st.title("📊 Resumen General de Asistencias")
    st.caption("Visión global del avance extraído de la tabla de Resumen General")

    # KPIs Globales
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Integrantes", f"{len(df_resumen)} alumnos")
    k2.metric("Total Horas Acumuladas", f"{round(df_resumen['HORAS_DECIMAL'].sum(), 1)} hrs")
    k3.metric("Promedio de Avance", f"{round(df_resumen['PORCENTAJE_NUMERICO'].mean(), 1)} %")

    st.markdown("---")

    # Gráfico de Barras
    st.subheader("📈 Avance por Integrante")
    df_sorted = df_resumen.sort_values('PORCENTAJE_NUMERICO', ascending=True)
    fig_bar = px.bar(
        df_sorted,
        x='PORCENTAJE_NUMERICO',
        y='NOMBRE',
        orientation='h',
        text=df_sorted['AVANCE'],
        labels={'PORCENTAJE_NUMERICO': '% Avance', 'NOMBRE': 'Integrante'},
        color='PORCENTAJE_NUMERICO',
        color_continuous_scale='Blues'
    )
    fig_bar.add_vline(x=100.0, line_dash="dash", line_color="green", annotation_text="Meta 100%")
    fig_bar.update_layout(height=500, showlegend=False, xaxis_range=[0, 105])
    st.plotly_chart(fig_bar, use_container_width=True)

    st.markdown("---")

    # Tabla de Datos
    st.subheader("📋 Tabla de Datos")
    st.dataframe(
        df_resumen[['NOMBRE', 'HORAS CONTABILIZADAS', 'HORAS RESTANTES', 'AVANCE']],
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------------------------------
# VISTA 2: PANEL INDIVIDUAL CON FILTRO SEMANAL
# ---------------------------------------------------------
else:
    st.title("👤 Panel Individual de Integrante")
    
    # Lista de usuarios
