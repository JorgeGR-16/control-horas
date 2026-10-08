import streamlit as st
import pandas as pd
import plotly.express as px
import os
import datetime

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Asistencias",
    page_icon="⏱️",
    layout="wide"
)

RUTA_BASE = "BASE_DATOS.xlsx"

# ---------------------------------------------------------
# FUNCIONES AUXILIARES DE CONVERSIÓN DE HORAS
# ---------------------------------------------------------
def horas_a_decimal(val):
    """Convierte cadenas HH:MM:SS u objetos datetime.time a horas flotantes/decimales."""
    if pd.isna(val) or str(val).strip() in ['', 'nan', 'None']:
        return 0.0
    if isinstance(val, datetime.time):
        return val.hour + val.minute / 60.0 + val.second / 3600.0
    if isinstance(val, (int, float)):
        # Si ya viene como fracción de día de Excel
        return val * 24.0
    if isinstance(val, str):
        partes = val.split(':')
        if len(partes) == 3:
            try:
                return float(partes[0]) + float(partes[1])/60.0 + float(partes[2])/3600.0
            except:
                return 0.0
        elif len(partes) == 2:
            try:
                return float(partes[0]) + float(partes[1])/60.0
            except:
                return 0.0
    return 0.0

def formato_porcentaje(val):
    """Convierte decimales (0.7398) o cadenas ('73,98%') a número flotante 0-100."""
    if pd.isna(val):
        return 0.0
    if isinstance(val, (int, float)):
        return val * 100.0 if val <= 1.0 else float(val)
    if isinstance(val, str):
        val_clean = val.replace('%', '').replace(',', '.').strip()
        try:
            num = float(val_clean)
            return num if num > 1.0 else num * 100.0
        except:
            return 0.0
    return 0.0

# ---------------------------------------------------------
# CARGA DE DATOS DE RESUMEN GENERAL
# ---------------------------------------------------------
@st.cache_data(ttl=60)
def cargar_resumen_general(ruta):
    if not os.path.exists(ruta):
        return None
    
    # Leer especificamente la hoja RESUMEN_GENERAL desde la fila del encabezado (Fila 3 de Excel -> header=2)
    df = pd.read_excel(ruta, sheet_name='RESUMEN_GENERAL', header=2)
    
    # Quedarnos solo con las columnas relevantes
    cols_necesarias = ['NOMBRE', 'HORAS CONTABILIZADAS', 'HORAS RESTANTES', 'AVANCE']
    df = df[[c for c in cols_necesarias if c in df.columns]].dropna(subset=['NOMBRE']).copy()
    
    # Limpiar cadenas
    df['NOMBRE'] = df['NOMBRE'].astype(str).str.strip()
    
    # Crear versiones numéricas para gráficos y KPIs
    df['HORAS_CONT_DECIMAL'] = df['HORAS CONTABILIZADAS'].apply(horas_a_decimal)
    df['HORAS_REST_DECIMAL'] = df['HORAS RESTANTES'].apply(horas_a_decimal)
    df['PORCENTAJE_AVANCE'] = df['AVANCE'].apply(formato_porcentaje)
    
    return df

df_resumen = cargar_resumen_general(RUTA_BASE)

# ---------------------------------------------------------
# BARRA LATERAL
# ---------------------------------------------------------
st.sidebar.title("Sistema de Asistencias")
opcion_vista = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Resumen General", "👤 Panel Individual de Integrante"]
)

# ---------------------------------------------------------
# VISTA 1: RESUMEN GENERAL (EXCLUSIVO DE "RESUMEN_GENERAL")
# ---------------------------------------------------------
if opcion_vista == "📊 Resumen General":
    st.title("📊 Resumen General de Asistencias")
    st.caption("Datos cargados directamente de la hoja RESUMEN_GENERAL")

    if df_resumen is not None and not df_resumen.empty:
        # 1. Indicadores / KPIs Superiores
        total_integrantes = len(df_resumen)
        promedio_avance = df_resumen['PORCENTAJE_AVANCE'].mean()
        total_horas_equipo = df_resumen['HORAS_CONT_DECIMAL'].sum()

        kpi1, kpi2, kpi3 = st.columns(3)
        kpi1.metric("Total Integrantes", f"{total_integrantes} alumnos")
        kpi2.metric("Horas Totales Equipo", f"{round(total_horas_equipo, 1)} hrs")
        kpi3.metric("Promedio de Avance", f"{round(promedio_avance, 1)} %")

        st.markdown("---")

        # 2. Gráfico de Porcentaje de Avance por Integrante
        st.subheader("📈 Avance Porcentual de Integrantes")
        
        fig_bar = px.bar(
            df_resumen.sort_values('PORCENTAJE_AVANCE', ascending=True),
            x='PORCENTAJE_AVANCE',
            y='NOMBRE',
            orientation='h',
            text=df_resumen.sort_values('PORCENTAJE_AVANCE', ascending=True)['PORCENTAJE_AVANCE'].apply(lambda x: f"{x:.1f}%"),
            labels={'PORCENTAJE_AVANCE': '% Avance', 'NOMBRE': 'Integrante'},
            color='PORCENTAJE_AVANCE',
            color_continuous_scale='Blues'
        )
        fig_bar.add_vline(x=100.0, line_dash="dash", line_color="green", annotation_text="Meta 100%")
        fig_bar.update_layout(height=500, showlegend=False, xaxis_range=[0, 105])
        st.plotly_chart(fig_bar, use_container_width=True)

        st.markdown("---")

        # 3. Tabla Exacta del RESUMEN_GENERAL
        st.subheader("📋 Tabla de Datos de Resumen General")
        
        # Formatear la tabla visual para mostrar avance con formato %
        df_display = df_resumen[['NOMBRE', 'HORAS CONTABILIZADAS', 'HORAS RESTANTES', 'PORCENTAJE_AVANCE']].copy()
        df_display.columns = ['Nombre', 'Horas Contabilizadas', 'Horas Restantes', '% Avance']
        df_display['% Avance'] = df_display['% Avance'].apply(lambda x: f"{x:.2f}%")
        
        st.dataframe(
            df_display,
            use_container_width=True,
            hide_index=True
        )
    else:
        st.error("No se pudieron cargar los datos de la hoja RESUMEN_GENERAL.")
