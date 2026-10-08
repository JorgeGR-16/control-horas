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
# FUNCIONES AUXILIARES DE CÁLCULO DE HORAS
# ---------------------------------------------------------
def convertir_a_segundos_desde_medianoche(val):
    """Convierte un objeto de hora o texto HH:MM:SS a segundos acumulados del día."""
    if pd.isna(val) or str(val).strip() in ['', 'nan', 'None', 'NaT', '0:00:00', '00:00:00']:
        return None
    
    if isinstance(val, pd.Timedelta):
        return int(val.total_seconds())
    
    if hasattr(val, 'hour'):  # datetime.time o Timestamp
        return val.hour * 3600 + val.minute * 60 + val.second

    if isinstance(val, str):
        partes = val.strip().split(':')
        try:
            if len(partes) == 3:
                return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(partes[2])
            elif len(partes) == 2:
                return int(partes[0]) * 3600 + int(partes[1]) * 60
        except ValueError:
            return None
    return None

def calcular_diferencia_par(entrada, salida):
    """Calcula la diferencia en segundos entre Entrada y Salida (Salida - Entrada)."""
    seg_e = convertir_a_segundos_desde_medianoche(entrada)
    seg_s = convertir_a_segundos_desde_medianoche(salida)
    
    if seg_e is not None and seg_s is not None:
        diff = seg_s - seg_e
        return diff if diff >= 0 else diff + 86400  # Manejo por si cruza medianoche
    return 0

def segundos_a_formato_horas(segundos):
    """Formatea segundos acumulados a una cadena legible HH:MM:SS."""
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segs = int(segundos % 60)
    return f"{horas:02d}:{minutos:02d}:{segs:02d}"

# ---------------------------------------------------------
# CARGA Y CÁLCULO DIRECTO DE ASISTENCIAS
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
        # 1. Obtener nombre completo del integrante
        df_head = pd.read_excel(xls, sheet_name=hoja, header=None, nrows=1)
        nombre_completo = str(df_head.iloc[0, 0]).strip() if not df_head.empty and pd.notna(df_head.iloc[0, 0]) else hoja

        # 2. Leer datos de la hoja a partir de la fila de encabezados
        df_u = pd.read_excel(xls, sheet_name=hoja, header=1)
        df_u.rename(columns={df_u.columns[0]: 'FECHA'}, inplace=True)

        segundos_totales_hoja = 0

        # Iterar sobre las filas para calcular asistencias reales desde pares Entrada/Salida
        for idx, row in df_u.iterrows():
            # Par 1
            e1 = row.get('ENTRADA 1')
            s1 = row.get('SALIDA 1')
            t1 = calcular_diferencia_par(e1, s1)

            # Par 2
            e2 = row.get('ENTRADA 2')
            s2 = row.get('SALIDA 2')
            t2 = calcular_diferencia_par(e2, s2)

            # Par 3
            e3 = row.get('ENTRADA 3')
            s3 = row.get('SALIDA 3')
            t3 = calcular_diferencia_par(e3, s3)

            # Ajuste (-)
            ajuste_val = row.get('AJUSTE (-)')
            seg_ajuste = convertir_a_segundos_desde_medianoche(ajuste_val) or 0

            # Suma neta del día
            subtotal_dia = max(0, (t1 + t2 + t3) - seg_ajuste)
            segundos_totales_hoja += subtotal_dia

        # Conversiones para las métricas del Dashboard
        total_horas_dec = segundos_totales_hoja / 3600.0
        segundos_restantes = max(0, int((HORAS_OBJETIVO * 3600) - segundos_totales_hoja))
        horas_restantes_dec = segundos_restantes / 3600.0
        porcentaje_avance = min(100.0, (total_horas_dec / HORAS_OBJETIVO) * 100.0)

        resumen_filas.append({
            'NOMBRE': nombre_completo,
            'HOJA': hoja,
            'HORAS_CONTABILIZADAS_STR': segundos_a_formato_horas(segundos_totales_hoja),
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
    st.caption("Cálculo en tiempo real directo desde los marcajes de entrada y salida.")

    if df_resumen is not None and not df_resumen.empty:
        # KPIs
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
        
        m1, m2, m3 = st.columns(3)
        m1.metric("Horas Contabilizadas", info_resumen['HORAS_CONTABILIZADAS_STR'])
        m2.metric("Horas Restantes", info_resumen['HORAS_RESTANTES_STR'])
        m3.metric("Porcentaje de Avance", f"{round(info_resumen['PORCENTAJE_AVANCE'], 1)} %")
        
        st.progress(info_resumen['PORCENTAJE_AVANCE'] / 100.0)
        
        st.markdown("### 📅 Detalle Diario de Asistencias")
        if not df_u.empty:
            cols_ver = [c for c in ['FECHA', 'ENTRADA 1', 'SALIDA 1', 'ENTRADA 2', 'SALIDA 2', 'AJUSTE (-)', 'JUSTIFICACIÓN'] if c in df_u.columns]
            st.dataframe(df_u[cols_ver].dropna(how='all'), use_container_width=True, hide_index=True)
        else:
            st.info("No hay asistencias registradas aún para este usuario.")
