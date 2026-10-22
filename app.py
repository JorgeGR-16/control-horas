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
    {"NOMBRE": "ALEJANDRO RAMOS MAYEN", "HORAS CONTABILIZADAS": "383:34:00", "HORAS RESTANTES": "96:26:00", "AVANCE": "79,91%", "HOJA": "ALEJANDRO R.M"},
    {"NOMBRE": "CESAR YAIR ESPINOSA MARTINEZ", "HORAS CONTABILIZADAS": "316:39:31", "HORAS RESTANTES": "163:20:29", "AVANCE": "65,97%", "HOJA": "CESAR Y.E.M"},
    {"NOMBRE": "CHRISTIAN GONZÁLEZ GUTIÉRREZ", "HORAS CONTABILIZADAS": "377:19:07", "HORAS RESTANTES": "102:40:53", "AVANCE": "78,61%", "HOJA": "CHRISTIAN G.G"},
    {"NOMBRE": "FÁTIMA PACHECO ZACARÍAS", "HORAS CONTABILIZADAS": "476:13:02", "HORAS RESTANTES": "3:46:58", "AVANCE": "99,21%", "HOJA": "FÁTIMA P.Z"},
    {"NOMBRE": "FERNANDO JAVIER RAMIREZ GARCIA", "HORAS CONTABILIZADAS": "357:44:41", "HORAS RESTANTES": "122:15:19", "AVANCE": "74,53%", "HOJA": "FERNANDO J.R.G"},
    {"NOMBRE": "KARLA YAMILET AGUILAR RAMÍREZ", "HORAS CONTABILIZADAS": "351:07:49", "HORAS RESTANTES": "128:52:11", "AVANCE": "73,15%", "HOJA": "KARLA Y.A.R"},
    {"NOMBRE": "KATHERINE MENDEZ MARQUEZ", "HORAS CONTABILIZADAS": "483:25:54", "HORAS RESTANTES": "-3:25:54", "AVANCE": "100,71%", "HOJA": "KATHERINE M.M"},
    {"NOMBRE": "LUDWING PINEDA CUEVAS", "HORAS CONTABILIZADAS": "75:44:40", "HORAS RESTANTES": "404:15:20", "AVANCE": "15,78%", "HOJA": "LUDWING P.C"},
    {"NOMBRE": "LUIS FERNANDO CASTILLO GARCÍA", "HORAS CONTABILIZADAS": "375:51:57", "HORAS RESTANTES": "104:08:03", "AVANCE": "78,31%", "HOJA": "LUIS F.C.G"},
    {"NOMBRE": "MARIA NATALIA CABRERA MONJARAS", "HORAS CONTABILIZADAS": "320:03:25", "HORAS RESTANTES": "159:56:35", "AVANCE": "66,68%", "HOJA": "MARIA N.C.M"},
    {"NOMBRE": "MISAEL RIVERA LÓPEZ", "HORAS CONTABILIZADAS": "217:37:55", "HORAS RESTANTES": "262:22:05", "AVANCE": "45,34%", "HOJA": "MISAEL R.L"},
    {"NOMBRE": "RAFAEL EDUARDO LAGUNAS GÓMEZ", "HORAS CONTABILIZADAS": "365:14:07", "HORAS RESTANTES": "114:45:53", "AVANCE": "76,09%", "HOJA": "RAFAEL E.L.G"},
    {"NOMBRE": "CARLOS CRISTOPHER TERRAZAS MARTINEZ", "HORAS CONTABILIZADAS": "61:25:19", "HORAS RESTANTES": "418:34:41", "AVANCE": "12,80%", "HOJA": "CARLOS C.T.M"}
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
    ["📊 Resumen General", "👤 Avance Individual"]
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




else:
    st.title("👤 AVANCE INDIVIDUAL")
    
    usuario_sel = st.sidebar.selectbox("Selecciona un Integrante:", df_resumen['NOMBRE'].tolist())
    info_user = df_resumen[df_resumen['NOMBRE'] == usuario_sel].iloc[0]
    hoja_user = info_user['HOJA']
    
    st.subheader(f"📌 AVANCE DE: {usuario_sel}")
    
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
            
            # Normalizar nombres de columnas para eliminar espacios accidentales
            df_u.columns = df_u.columns.astype(str).str.strip()
            
            # Renombrar variaciones comunes de la primera columna a 'FECHA'
            df_u.rename(columns={df_u.columns[0]: 'FECHA'}, inplace=True)
            
            # Renombrar variaciones de la columna 'JUSTIFICACIÓN'
            renombres = {
                'JUSTIFICACION': 'JUSTIFICACIÓN',
                'justificacion': 'JUSTIFICACIÓN',
                'justificación': 'JUSTIFICACIÓN',
                'MOTIVO': 'JUSTIFICACIÓN',
                'OBSERVACIONES': 'JUSTIFICACIÓN'
            }
            df_u.rename(columns=renombres, inplace=True)

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
                
                # Función auxiliar para convertir valores de hora (str, datetime.time, pd.Timestamp) a segundos
                def parsear_a_segundos(valor):
                    if pd.isna(valor) or valor is None:
                        return 0
                    if isinstance(valor, (pd.Timestamp, pd.Series)):
                        return valor.hour * 3600 + valor.minute * 60 + valor.second
                    if hasattr(valor, 'hour'):  # Para objetos datetime.time
                        return valor.hour * 3600 + valor.minute * 60 + valor.second
                    return texto_a_segundos(valor)

                # -----------------------------------------------------
                # CÁLCULO AUTOMÁTICO DE 'TOTAL HORAS DIARIAS' (INCLUYE TURNO 1, 2 Y 3)
                # -----------------------------------------------------
                def calcular_total_diario_row(row):
                    # Turno 1
                    e1 = parsear_a_segundos(row.get('ENTRADA 1'))
                    s1 = parsear_a_segundos(row.get('SALIDA 1'))
                    t1 = max(0, s1 - e1) if s1 > e1 else 0

                    # Turno 2
                    e2 = parsear_a_segundos(row.get('ENTRADA 2'))
                    s2 = parsear_a_segundos(row.get('SALIDA 2'))
                    t2 = max(0, s2 - e2) if s2 > e2 else 0

                    # Turno 3
                    e3 = parsear_a_segundos(row.get('ENTRADA 3'))
                    s3 = parsear_a_segundos(row.get('SALIDA 3'))
                    t3 = max(0, s3 - e3) if s3 > e3 else 0

                    # Ajustes
                    ajuste = parsear_a_segundos(row.get('AJUSTE (-)'))
                    
                    total_seg = max(0, (t1 + t2 + t3) - ajuste)
                    return segundos_a_formato(total_seg)

                df_semana['TOTAL HORAS DIARIAS'] = df_semana.apply(calcular_total_diario_row, axis=1)
                
                # Formatear fecha limpia (YYYY-MM-DD)
                df_semana['FECHA'] = df_semana['FECHA_DT'].dt.strftime('%Y-%m-%d')

                # Si la columna 'JUSTIFICACIÓN' no existía en el archivo, se crea vacía para evitar fallos
                if 'JUSTIFICACIÓN' not in df_semana.columns:
                    df_semana['JUSTIFICACIÓN'] = ""

                # Columnas a mostrar en el orden deseado
                cols_orden = [
                    'FECHA', 
                    'ENTRADA 1', 'SALIDA 1', 
                    'ENTRADA 2', 'SALIDA 2', 
                    'ENTRADA 3', 'SALIDA 3', 
                    'TOTAL HORAS DIARIAS', 
                    'AJUSTE (-)', 
                    'JUSTIFICACIÓN'
                ]

                cols_presentes = [c for c in cols_orden if c in df_semana.columns]

                # Rellenar nulos de forma segura para no perder la visualización
                df_display = df_semana[cols_presentes].copy()
                df_display['JUSTIFICACIÓN'] = df_display['JUSTIFICACIÓN'].astype(str).replace(['nan', 'None', 'NaN'], '')
                df_display = df_display.fillna("")

                st.markdown(f"#### Registros de la {semana_sel}")
                st.dataframe(df_display, use_container_width=True, hide_index=True)
            else:
                st.info("Este usuario no tiene registros de asistencias con fecha aún.")
        else:
            st.warning(f"No se encontró la hoja individual '{hoja_user}' en el archivo Excel.")
    else:
        st.info("El archivo 'BASE_DATOS.xlsx' no está presente localmente para mostrar el detalle diario.")
