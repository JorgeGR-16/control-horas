import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# 1. DATAFRAME EXTRAÍDO DE "RESUMEN_GENERAL" (TAL CUAL TU IMAGEN)
# ---------------------------------------------------------
raw_data = [
    {"NOMBRE": "ALEJANDRO RAMOS MAYEN", "HORAS CONTABILIZADAS": "355:07:39", "HORAS RESTANTES": "124:52:21", "AVANCE": "73,98%"},
    {"NOMBRE": "CESAR YAIR ESPINOSA MARTINEZ", "HORAS CONTABILIZADAS": "281:44:07", "HORAS RESTANTES": "198:15:53", "AVANCE": "58,69%"},
    {"NOMBRE": "CHRISTIAN GONZÁLEZ GUTIÉRREZ", "HORAS CONTABILIZADAS": "353:28:05", "HORAS RESTANTES": "126:31:55", "AVANCE": "73,64%"},
    {"NOMBRE": "FÁTIMA PACHECO ZACARÍAS", "HORAS CONTABILIZADAS": "443:14:41", "HORAS RESTANTES": "36:45:19", "AVANCE": "92,34%"},
    {"NOMBRE": "FERNANDO JAVIER RAMIREZ GARCIA", "HORAS CONTABILIZADAS": "327:58:51", "HORAS RESTANTES": "152:01:09", "AVANCE": "68,33%"},
    {"NOMBRE": "KARLA YAMILET AGUILAR RAMÍREZ", "HORAS CONTABILIZADAS": "319:40:28", "HORAS RESTANTES": "160:19:32", "AVANCE": "66,60%"},
    {"NOMBRE": "KATHERINE MENDEZ MARQUEZ", "HORAS CONTABILIZADAS": "453:48:44", "HORAS RESTANTES": "26:11:16", "AVANCE": "94,54%"},
    {"NOMBRE": "LUDWING PINEDA CUEVAS", "HORAS CONTABILIZADAS": "40:43:43", "HORAS RESTANTES": "439:16:17", "AVANCE": "8,49%"},
    {"NOMBRE": "LUIS FERNANDO CASTILLO GARCÍA", "HORAS CONTABILIZADAS": "344:01:47", "HORAS RESTANTES": "135:58:13", "AVANCE": "71,67%"},
    {"NOMBRE": "MARIA NATALIA CABRERA MONJARAS", "HORAS CONTABILIZADAS": "288:26:44", "HORAS RESTANTES": "191:33:16", "AVANCE": "60,09%"},
    {"NOMBRE": "MISAEL RIVERA LÓPEZ", "HORAS CONTABILIZADAS": "198:52:14", "HORAS RESTANTES": "281:07:46", "AVANCE": "41,43%"},
    {"NOMBRE": "RAFAEL EDUARDO LAGUNAS GÓMEZ", "HORAS CONTABILIZADAS": "327:36:46", "HORAS RESTANTES": "152:23:14", "AVANCE": "68,25%"},
    {"NOMBRE": "CARLOS CRISTOPHER TERRAZAS MARTINEZ", "HORAS CONTABILIZADAS": "32:20:46", "HORAS RESTANTES": "447:39:14", "AVANCE": "6,74%"}
]

df = pd.DataFrame(raw_data)

# ---------------------------------------------------------
# 2. CONVERSIÓN DE CADA VALOR A TIEMPO REAL Y NÚMEROS
# ---------------------------------------------------------
def texto_a_segundos(h_str):
    partes = str(h_str).split(':')
    return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])

# Conversión a datos de tiempo usable
df['SEG_CONTABILIZADOS'] = df['HORAS CONTABILIZADAS'].apply(texto_a_segundos)
df['HORAS_DECIMAL'] = df['SEG_CONTABILIZADOS'] / 3600.0
df['TIMEDELTA_CONTABILIZADAS'] = pd.to_timedelta(df['SEG_CONTABILIZADOS'], unit='s')

df['SEG_RESTANTES'] = df['HORAS RESTANTES'].apply(texto_a_segundos)
df['TIMEDELTA_RESTANTES'] = pd.to_timedelta(df['SEG_RESTANTES'], unit='s')

df['PORCENTAJE_NUMERICO'] = df['AVANCE'].str.replace('%', '').str.replace(',', '.').astype(float)

# ---------------------------------------------------------
# 3. INTERFAZ STREAMLIT
# ---------------------------------------------------------
st.set_page_config(page_title="Resumen General", layout="wide")
st.title("📊 Resumen General de Asistencias")

# KPIs
k1, k2, k3 = st.columns(3)
k1.metric("Total Integrantes", f"{len(df)} alumnos")

k3.metric("Promedio de Avance", f"{round(df['PORCENTAJE_NUMERICO'].mean(), 1)} %")

st.markdown("---")

# Gráfico
fig = px.bar(
    df.sort_values('PORCENTAJE_NUMERICO', ascending=True),
    x='PORCENTAJE_NUMERICO',
    y='NOMBRE',
    orientation='h',
    text=df.sort_values('PORCENTAJE_NUMERICO', ascending=True)['AVANCE'],
    title="Avance por Integrante",
    labels={'PORCENTAJE_NUMERICO': '% Avance', 'NOMBRE': 'Integrante'},
    color='PORCENTAJE_NUMERICO',
    color_continuous_scale='Blues'
)
st.plotly_chart(fig, use_container_width=True)

# Tabla limpia mostrando las columnas originales de la imagen
st.subheader("📋 Tabla de Datos Extraída")
st.dataframe(
    df[['NOMBRE', 'HORAS CONTABILIZADAS', 'HORAS RESTANTES', 'AVANCE']],
    use_container_width=True,
    hide_index=True
)
