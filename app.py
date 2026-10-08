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
HORAS_OBJETIVO = 480.0  # Meta estándar de horas a cubrir

# ---------------------------------------------------------
# FUNCIÓN PARA CONVERTIR CUALQUIER VALOR A SEGUNDOS
# ---------------------------------------------------------
def convertir_a_segundos(val):
    """Convierte cualquier celda (texto, float, timedelta) a segundos acumulados."""
    if pd.isna(val) or val is None:
        return 0
    
    # Si viene como número (fracción de día de Excel o horas directas)
    if isinstance(val, (int, float)):
        return int(val * 86400) if val < 1.0 else int(val * 3600)
    
    # Si viene como objeto Timedelta
    if isinstance(val, pd.Timedelta):
        return int(val.total_seconds())
    
    # Si viene como objeto Time/Timestamp
    if hasattr(val, 'hour'):
        return val.hour * 3600 + val.minute * 60 + val.second

    # Si viene como texto
    s = str(val).strip()
    if not s or s.lower() in ['nan', 'none', 'nat', '0:00:00', '00:00:00', '-']:
        return 0

    partes = s.split(':')
    try:
        if len(partes) == 3:
            return int(partes[0]) * 3600 + int(partes[1]) * 60 + int(float(partes[2]))
        elif len(partes) == 2:
            return int(partes[0]) * 3600 + int(partes[1]) * 60
        elif len(partes) == 1:
            return int(float(partes[0]) * 3600)
    except ValueError:
        return 0
    return 0

def segundos_a_formato_horas(segundos):
    """Formatea segundos a una cadena HH:MM:SS."""
    h = int(segundos // 3600)
    m = int((segundos % 3600) // 60)
    s = int(segundos % 60)
    return f"{h:02d}:{m:02d}:{s:02d}"

# ---------------------------------------------------------
# EXTRACCIÓN DIRECTA DE LA HOJA DE DATOS GENERALES
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_datos_generales(ruta):
    if not os.path.exists(ruta):
        return None

    # Leer únicamente la hoja 'DATOS GENERALES'
    df_raw = pd.read_excel(ruta, sheet_name='DATOS GENERALES')

    # Limpiar nombres de columnas eliminando espacios y saltos de línea
    df_raw.columns = [str(c).replace('\n', ' ').strip() for c in df_raw.columns]

    # Verificar si existen las columnas necesarias
    col_nombre = 'NOMBRE' if 'NOMBRE' in df_raw.columns else df_raw.columns[0]
    col_horas = 'HORAS CONTABILIZADAS' if 'HORAS CONTABILIZADAS' in df_raw.columns else None

    if col_horas is None:
        return None

    # Extraer valores crudos como texto/objetos y convertirlos directamente a formato de tiempo
    resumen_filas = []
    
    for _, row in df_raw.iterrows():
        nombre = str(row[col_nombre]).strip()
        if not nombre or nombre.lower() in ['nan', 'none', 'nombre']:
            continue

        # Convertir el valor crudo extraído del Excel a segundos
        valor_bruto = row[col_horas]
        segundos_totales = convertir_a_segundos(valor_bruto)

        # Cálculos de avance
        total_horas_dec = segundos_totales / 3600.0
        segundos_restantes = max(0, int((HORAS_OBJETIVO * 3600) - segundos_totales))
        horas_restantes_dec = segundos_restantes / 3600.0
        porcentaje_avance = min(100.0, (total_horas_dec / HORAS_OBJETIVO) * 100.0)

        resumen_filas.append({
            'NOMBRE': nombre,
            'HORAS_CONTABILIZADAS_STR': segundos_a_formato_horas(segundos_totales),
            'HORAS_RESTANTES_STR': segundos_a_formato_horas(segundos_restantes),
            'HORAS_CONT_DECIMAL': total_horas_dec,
            'HORAS_REST_DECIMAL': horas_restantes_dec,
            'PORCENTAJE_AVANCE': porcentaje_avance,
            'CARRERA': str(row.get('CARRERA', '')),
            'ESTATUS': str(row.get('ESTATUS', ''))
        })

    return pd.DataFrame(resumen_filas)

# Cargar el DataFrame transformado
df_resumen = cargar_datos_generales(RUTA_BASE)

# ---------------------------------------------------------
# INTERFAZ STREAMLIT
# ---------------------------------------------------------
st.title("📊 Resumen General - Datos Generales de Excel")
st.caption("Extracción directa de datos crudos transformados a métricas de tiempo.")

if df_resumen is not None and not df_resumen.empty:
    # Métricas Globales (KPIs)
    k1, k2, k3 = st.columns(3)
    k1.metric("Total Integrantes", f"{len(df_resumen)} alumnos")
    k2.metric("Horas Totales Acumuladas", f"{round(df_resumen['HORAS_CONT_DECIMAL'].sum(), 1)} hrs")
    k3.metric("Promedio de Avance", f"{round(df_resumen['PORCENTAJE_AVANCE'].mean(), 1)} %")

    st.markdown("---")

    # Gráfico de Barras de Avance
    st.subheader("📈 Porcentaje de Avance")
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

    # Tabla de Datos Convertidos
    st.subheader("📋 Tabla de Datos de Tiempo")
    df_tabla = df_resumen[['NOMBRE', 'CARRERA', 'ESTATUS', 'HORAS_CONTABILIZADAS_STR', 'HORAS_RESTANTES_STR', 'PORCENTAJE_AVANCE']].copy()
    df_tabla.columns = ['Nombre', 'Carrera', 'Estatus', 'Horas Contabilizadas', 'Horas Restantes', '% Avance']
    df_tabla['% Avance'] = df_tabla['% Avance'].apply(lambda x: f"{x:.2f}%")

    st.dataframe(df_tabla, use_container_width=True, hide_index=True)
else:
    st.error("No se pudieron extraer los datos generales del archivo Excel.")
