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
        partes = str(h_str).strip().split(':')
        if len(partes) == 3:
            return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(float(partes[2]))
        elif len(partes) == 2:
            return int(partes[0]) * 3600 + int(partes[1]) * 60
    except:
        return 0
    return 0

def segundos_a_formato(segundos):
    if segundos <= 0:
        return "00:00:00"
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

df_resumen['HORAS_DECIMAL'] = df_resumen['HORAS CONTABILIZADAS'].apply(texto_a_segundos) / 3600.0
df_resumen['PORCENTAJE_NUMERICO'] = df_resumen['AVANCE'].str.replace('%', '').str.replace(',', '.').astype(float)

# ---------------------------------------------------------
# BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.title("Sistema de Asistencias")
st.sidebar.markdown("---")
opcion_vista = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Resumen General", "👤 Panel Individual de Integrante de SS"]
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
# VISTA 2: PANEL INDIVIDUAL CON CÁLCULO DE TOTAL HORAS DIARIAS
# ---------------------------------------------------------
else:
    st.title("👤 Panel Individual de Integrante")
    
    usuario_sel = st.sidebar.selectbox("Selecciona un Integrante:", df_resumen['NOMBRE'].tolist())
    info_user = df_resumen[df_resumen['NOMBRE'] == usuario_sel].iloc[0]
    hoja_user = info_user['HOJA']
    
    st.subheader(f"📌 Expediente: {usuario_sel}")
    
    m1, m2, m3 = st.columns(3)
    m1.metric("Horas Contabilizadas", info_user['HORAS CONTABILIZADAS'])
    m2.metric("Horas Restantes", info_user['HORAS RESTANTES'])
    m3.metric("Porcentaje de Avance", info_user['AVANCE'])
    
    st.progress(info_user['PORCENTAJE_NUMERICO'] / 100.0)
    
    st.markdown("---")

    if os.path.exists(RUTA_BASE):
        xls = pd.ExcelFile(RUTA_BASE)
        if hoja_user in xls.sheet_names:
            df_u = pd.read_excel(xls, sheet_name=hoja_user, header=1)
            df_u.rename(columns={df_u.columns[0]: 'FECHA'}, inplace=True)
            df_u['FECHA_DT'] = pd.to_datetime(df_u['FECHA'], errors='coerce')
            df_u_valid = df_u.dropna(subset=['FECHA_DT']).copy()
            
            if not df_u_valid.empty:
                # Agrupar por semanas
                df_u_valid['AÑO_SEMANA'] = df_u_valid['FECHA_DT'].dt.strftime('Semana %U (%Y)')
                semanas_disponibles = df_u_valid['AÑO_SEMANA'].unique()
                
                st.subheader("📅 Consulta de Avance por Semana")
                semana_sel = st.selectbox("Selecciona la semana que deseas consultar:", semanas_disponibles)
                
                # Filtrar la semana seleccionada
                df_semana = df_u_valid[df_u_valid['AÑO_SEMANA'] == semana_sel].copy()
                
                # -----------------------------------------------------
                # CÁLCULO AUTOMÁTICO DE 'TOTAL HORAS DIARIAS'
                # -----------------------------------------------------
                def calcular_total_diario_row(row):
                    e1 = texto_a_segundos(row.get('ENTRADA 1'))
                    s1 = texto_a_segundos(row.get('SALIDA 1'))
                    t1 = max(0, s1 - e1) if s1 > e1 else 0

                    e2 = texto_a_segundos(row.get('ENTRADA 2'))
                    s2 = texto_a_segundos(row.get('SALIDA 2'))
                    t2 = max(0, s2 - e2) if s2 > e2 else 0

                    ajuste = texto_a_segundos(row.get('AJUSTE (-)'))
                    
                    total_seg = max(0, (t1 + t2) - ajuste)
                    return segundos_a_formato(total_seg)

                df_semana['TOTAL HORAS DIARIAS'] = df_semana.apply(calcular_total_diario_row, axis=1)
                
                # Formatear fecha limpia (YYYY-MM-DD)
                df_semana['FECHA'] = df_semana['FECHA_DT'].dt.strftime('%Y-%m-%d')

                # Columnas a mostrar en la tabla en orden correcto
                cols_orden = ['FECHA', 'ENTRADA 1', 'SALIDA 1', 'ENTRADA 2', 'SALIDA 2', 'TOTAL HORAS DIARIAS', 'AJUSTE (-)', 'JUSTIFICACIÓN']
                cols_presentes = [c for c in cols_orden if c in df_semana.columns]

                # Rellenar valores nulos con vacío para que no muestre "None"
                df_display = df_semana[cols_presentes].fillna("")

                st.markdown(f"#### Registros de la {semana_sel}")
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Este usuario no tiene registros de asistencias con fecha aún.")
        else:
            st.warning(f"No se encontró la hoja individual '{hoja_user}' en el archivo Excel.")
    else:
        st.info("El archivo 'BASE_DATOS.xlsx' no está presente localmente para mostrar el detalle diario.")
