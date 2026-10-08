import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime


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
HORAS_OBJETIVO = 480.0  # Meta estándar de horas a cubrir

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE CONVERSIÓN DE TIEMPO
# ---------------------------------------------------------
def convertir_total_semana_a_segundos(val):
    """
    Convierte cualquier valor presente en la columna 'TOTAL DE SEMANA' 
    (Timestamp de Excel, datetime.time, Timedelta o str HH:MM:SS) a segundos.
    """
    if pd.isna(val) or str(val).strip() in ['', 'nan', 'None', 'NaT']:
        return 0
    
    # Si viene como Timedelta de pandas/Python
    if isinstance(val, pd.Timedelta):
        return int(val.total_seconds())
    
    # Si viene como Timestamp/datetime de Excel (ej: 1900-01-12 09:37:37 equivale a 11 días + 09:37:37)
    if isinstance(val, (pd.Timestamp, datetime.datetime)):
        if val.year == 1900:
            dias = val.day - 1
            return dias * 86400 + val.hour * 3600 + val.minute * 60 + val.second
        else:
            return val.hour * 3600 + val.minute * 60 + val.second

    if isinstance(val, datetime.time):
        return val.hour * 3600 + val.minute * 60 + val.second

    if isinstance(val, str):
        partes = val.split(':')
        if len(partes) == 3:
            try:
                return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])
            except:
                return 0
        elif len(partes) == 2:
            try:
                return int(partes[0]) * 3600 + int(partes[1]) * 60
            except:
                return 0

    return 0

def segundos_a_formato_horas(segundos):
    """Formatea segundos acumulados a una cadena legible HH:MM:SS."""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

# ---------------------------------------------------------
# CARGA Y CÁLCULO SUMANDO LA COLUMNA 'TOTAL DE SEMANA'
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_y_calcular_resumen(ruta):
    if not os.path.exists(ruta):
        return None, {}

    xls = pd.ExcelFile(ruta)
    hojas_excluidas = ['DATOS GENERALES', 'RESUMEN_GENERAL', 'FECHAS_PROCESADAS', 'COPIA']
    hojas_usuarios = [h for h in xls.sheet_names if h not in hojas_excluidas]

    resumen_filas = []
    datos_detallados = {}

    for hoja in hojas_usuarios:
        # 1. Nombre completo desde la primera celda
        df_head = pd.read_excel(xls, sheet_name=hoja, header=None, nrows=1)
        nombre_completo = str(df_head.iloc[0, 0]).strip() if not df_head.empty and pd.notna(df_head.iloc[0, 0]) else hoja

        # 2. Leer datos de la hoja
        df_u = pd.read_excel(xls, sheet_name=hoja, header=1)
        df_u.rename(columns={df_u.columns[0]: 'FECHA'}, inplace=True)

        # 3. SUMA DIRECTA DE LA COLUMNA "TOTAL DE SEMANA"
        if 'TOTAL DE SEMANA' in df_u.columns:
            segundos_semana = df_u['TOTAL DE SEMANA'].apply(convertir_total_semana_a_segundos).sum()
        else:
            segundos_semana = 0

        # Respaldo en caso de que 'TOTAL DE SEMANA' esté vacía: sumar 'TOTAL HORAS DIARIAS'
        if segundos_semana == 0 and 'TOTAL HORAS DIARIAS' in df_u.columns:
            def a_seg_diario(v):
                if pd.isna(v): return 0
                if hasattr(v, 'hour'): return v.hour*3600 + v.minute*60 + v.second
                return 0
            segundos_semana = df_u['TOTAL HORAS DIARIAS'].apply(a_seg_diario).sum()

        # Conversiones para métricas
        total_horas_dec = segundos_semana / 3600.0
        segundos_restantes = max(0, int((HORAS_OBJETIVO * 3600) - segundos_semana))
        horas_restantes_dec = segundos_restantes / 3600.0
        porcentaje_avance = min(100.0, (total_horas_dec / HORAS_OBJETIVO) * 100.0)

        resumen_filas.append({
            'NOMBRE': nombre_completo,
            'HOJA': hoja,
            'HORAS_CONTABILIZADAS_STR': segundos_a_formato_horas(segundos_semana),
            'HORAS_RESTANTES_STR': segundos_a_formato_horas(segundos_restantes),
            'HORAS_CONT_DECIMAL': total_horas_dec,
            'HORAS_REST_DECIMAL': horas_restantes_dec,
            'PORCENTAJE_AVANCE': porcentaje_avance
        })

        datos_detallados[hoja] = df_u

    df_resumen = pd.DataFrame(resumen_filas)
    return df_resumen, datos_detallados

# Cargar los datos
df_resumen, datos_detallados = cargar_y_calcular_resumen(RUTA_BASE)

# ---------------------------------------------------------
# BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.title("Sistema de Asistencias")
st.sidebar.markdown("---")
opcion_vista = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Resumen General", "👤 Panel Individual de Integrante"]
)
st.sidebar.markdown("---")
st.sidebar.caption("🟢 Sincronizado vía GitHub")

# ---------------------------------------------------------
# VISTA 1: RESUMEN GENERAL
# ---------------------------------------------------------
if opcion_vista == "📊 Resumen General":
    st.title("📊 Resumen General de Asistencias y Servicio")
    st.caption("Visión consolidada del avance calculando la columna TOTAL DE SEMANA de cada integrante.")

    if df_resumen is not None and not df_resumen.empty:
        # KPIs Superiores
        total_integrantes = len(df_resumen)
        promedio_avance = df_resumen['PORCENTAJE_AVANCE'].mean()
        total_horas_equipo = df_resumen['HORAS_CONT_DECIMAL'].sum()

        k1, k2, k3 = st.columns(3)
        k1.metric("Total Integrantes", f"{total_integrantes} alumnos")
        k2.metric("Horas Totales del Equipo", f"{round(total_horas_equipo, 1)} hrs")
        k3.metric("Promedio de Avance", f"{round(promedio_avance, 1)} %")

        st.markdown("---")

        # Gráfico de Avance
        st.subheader("📈 Porcentaje de Avance por Integrante")
        df_sorted = df_resumen.sort_values('PORCENTAJE_AVANCE', ascending=True)
        
        fig_bar = px.bar(
            df_sorted,
            x='PORCENTAJE_AVANCE',
            y='NOMBRE',
            orientation='h',
            text=df_sorted['PORCENTAJE_AVANCE'].apply(lambda x: f"{x:.1f}%"),
            labels={'PORCENTAJE_AVANCE': '% Avance', 'NOMBRE': 'Integrante'},
            color='PORCENTAJE_AVANCE',
            color_continuous_scale='Blues'
        )
        fig_bar.add_vline(x=100.0, line_dash="dash", line_color="green", annotation_text="Meta 100%")
        fig_bar.update_layout(height=500, showlegend=False, xaxis_range=[0, 105])
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # Tabla de Datos
        st.subheader("📋 Tabla de Datos de Resumen General")
        
        df_tabla = df_resumen[['NOMBRE', 'HORAS_CONTABILIZADAS_STR', 'HORAS_RESTANTES_STR', 'PORCENTAJE_AVANCE']].copy()
        df_tabla.columns = ['Nombre', 'Horas Contabilizadas', 'Horas Restantes', '% Avance']
        df_tabla['% Avance'] = df_tabla['% Avance'].apply(lambda x: f"{x:.2f}%")

        st.dataframe(
            df_tabla,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("No se encontró la base de datos o el archivo no contiene hojas de integrantes.")

# ---------------------------------------------------------
# VISTA 2: PANEL INDIVIDUAL DE INTEGRANTE
# ---------------------------------------------------------
else:
    st.title("👤 Panel Individual de Integrante")
    
    if datos_detallados:
        hojas_alumnos = sorted(list(datos_detallados.keys()))
        hoja_sel = st.sidebar.selectbox("Selecciona un Integrante:", hojas_alumnos)
        
        df_u = datos_detallados[hoja_sel]
        info_resumen = df_resumen[df_resumen['HOJA'] == hoja_sel].iloc[0]
        
        st.subheader(f"📌 Expediente: {info_resumen['NOMBRE']}")
        
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Horas Contabilizadas", info_resumen['HORAS_CONTABILIZADAS_STR'])
        m2.metric("Horas Restantes", info_resumen['HORAS_RESTANTES_STR'])
        m3.metric("Porcentaje de Avance", f"{round(info_resumen['PORCENTAJE_AVANCE'], 1)} %")
        m4.metric("Registros Encontrados", f"{len(df_u)} días")
        
        st.progress(info_resumen['PORCENTAJE_AVANCE'] / 100.0)
        
        st.markdown("### 📅 Detalle Diario de Asistencias")
        if not df_u.empty:
            cols_ver = [c for c in ['FECHA', 'ENTRADA 1', 'SALIDA 1', 'TOTAL 1', 'ENTRADA 2', 'SALIDA 2', 'TOTAL 2', 'TOTAL HORAS DIARIAS', 'TOTAL DE SEMANA'] if c in df_u.columns]
            st.dataframe(df_u[cols_ver], use_container_width=True, hide_index=True)
        else:
            st.info("No hay asistencias registradas aún para este usuario.")
