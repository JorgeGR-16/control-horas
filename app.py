import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as obj
import os
import datetime

# ---------------------------------------------------------
# CONFIGURACIÓN DE PÁGINA STREAMLIT
# ---------------------------------------------------------
st.set_page_config(
    page_title="Control de Asistencias y Servicio Social",
    page_icon="⏱️",
    layout="wide",
    initial_sidebar_state="expanded"
)

HORAS_OBJETIVO_DEFAULT = 480.0  # Horas meta estándar para liberación

# ---------------------------------------------------------
# CARGA Y PROCESAMIENTO DE DATOS CON CACHÉ
# ---------------------------------------------------------
@st.cache_data(ttl=60)  # Recarga automática si cambia el archivo en GitHub
def cargar_datos_excel(ruta_excel):
    if not os.path.exists(ruta_excel):
        st.error(f"No se encontró el archivo de base de datos en: {ruta_excel}")
        return None, {}

    xls = pd.ExcelFile(ruta_excel)
    
    # 1. Leer Datos Generales
    df_generales = pd.read_excel(xls, 'DATOS GENERALES')
    df_generales = df_generales.dropna(subset=['NOMBRE', 'ESTATUS'])
    
    # Clean up whitespace
    df_generales['NOMBRE'] = df_generales['NOMBRE'].astype(str).str.strip()
    df_generales['ESTATUS'] = df_generales['ESTATUS'].astype(str).str.strip()

    # 2. Leer hojas de cada usuario activo
    hojas_sistema = ['DATOS GENERALES', 'RESUMEN_GENERAL', 'FECHAS_PROCESADAS', 'COPIA']
    hojas_usuarios = [h for h in xls.sheet_names if h not in hojas_sistema]
    
    datos_usuarios = {}
    for hoja in hojas_usuarios:
        df_u = pd.read_excel(xls, sheet_name=hoja, header=1)
        # Renombrar primera columna
        df_u.rename(columns={df_u.columns[0]: 'FECHA'}, inplace=True)
        df_u = df_u.dropna(subset=['FECHA']).copy()
        
        # Filtrar solo fechas válidas
        df_u['FECHA_DT'] = pd.to_datetime(df_u['FECHA'], errors='coerce')
        df_u = df_u.dropna(subset=['FECHA_DT']).sort_values('FECHA_DT')
        
        # Calcular segundos acumulados de la columna 'TOTAL HORAS DIARIAS'
        def a_segundos(val):
            if pd.isna(val) or str(val).strip() in ['', 'nan', 'None']:
                return 0
            if isinstance(val, datetime.time):
                return val.hour * 3600 + val.minute * 60 + val.second
            if isinstance(val, str):
                partes = val.split(':')
                if len(partes) == 3:
                    try:
                        return int(partes[0])*3600 + int(partes[1])*60 + int(partes[2])
                    except:
                        return 0
            return 0

        if 'TOTAL HORAS DIARIAS' in df_u.columns:
            df_u['SEGUNDOS_DIARIOS'] = df_u['TOTAL HORAS DIARIAS'].apply(a_segundos)
            df_u['HORAS_DIARIAS'] = df_u['SEGUNDOS_DIARIOS'] / 3600.0
        else:
            df_u['HORAS_DIARIAS'] = 0.0

        datos_usuarios[hoja] = df_u

    return df_generales, datos_usuarios

def formatear_segundos(segundos):
    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    return f"{horas}h {minutos:02d}m"

# ---------------------------------------------------------
# CARGA DE ARCHIVO BASE_DATOS.xlsx
# ---------------------------------------------------------
RUTA_BASE = "data/BASE_DATOS.xlsx" if os.path.exists("data/BASE_DATOS.xlsx") else "BASE_DATOS.xlsx"
df_generales, datos_usuarios = cargar_datos_excel(RUTA_BASE)

if df_generales is None:
    st.stop()

# ---------------------------------------------------------
# BARRA LATERAL (SIDEBAR)
# ---------------------------------------------------------
st.sidebar.image("https://img.icons8.com/isometric-folders/100/time-card.png", width=70)
st.sidebar.title("Sistema de Asistencias")
st.sidebar.markdown("---")

opcion_vista = st.sidebar.radio(
    "Selecciona una vista:",
    ["📊 Resumen General", "👤 Panel Individual de Integrante"],
    index=0
)

st.sidebar.markdown("---")
st.sidebar.caption("🟢 Base de Datos sincornizada vía GitHub")

# ---------------------------------------------------------
# VISTA 1: RESUMEN GENERAL (GLOBAL)
# ---------------------------------------------------------
if opcion_vista == "📊 Resumen General":
    st.title("📊 Resumen General de Asistencias y Servicio")
    st.markdown("Visión consolidada del avance de los integrantes registrados.")
    
    # Calcular totales por usuario
    totales_lista = []
    for nombre_hoja, df_u in datos_usuarios.items():
        total_horas = df_u['HORAS_DIARIAS'].sum() if not df_u.empty else 0.0
        totales_lista.append({
            'HOJA': nombre_hoja,
            'HORAS_ACUMULADAS': round(total_horas, 2)
        })
    df_totales = pd.DataFrame(totales_lista)
    
    # Mapear datos generales
    activos_count = len(df_generales[df_generales['ESTATUS'] == 'ACTIVO'])
    concluidos_count = len(df_generales[df_generales['ESTATUS'] == 'CONCLUIDO'])
    total_horas_equipo = df_totales['HORAS_ACUMULADAS'].sum()
    
    # Tarjetas KPI
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Integrantes Activos", f"{activos_count} alumnos", delta="En proceso")
    col2.metric("Concluidos", f"{concluidos_count} alumnos", delta="Finalizado", delta_color="normal")
    col3.metric("Horas Totales del Equipo", f"{round(total_horas_equipo, 1)} hrs")
    col4.metric("Promedio por Activo", f"{round(total_horas_equipo / max(activos_count, 1), 1)} hrs")

    st.markdown("---")
    
    # Gráfico de Avance Comparativo
    col_g1, col_g2 = st.columns([3, 2])
    
    with col_g1:
        st.subheader("📈 Avance de Horas Acumuladas por Integrante")
        if not df_totales.empty:
            df_totales['PORCENTAJE'] = (df_totales['HORAS_ACUMULADAS'] / HORAS_OBJETIVO_DEFAULT) * 100
            df_totales['PORCENTAJE'] = df_totales['PORCENTAJE'].clip(upper=100)
            
            fig_bar = px.bar(
                df_totales.sort_values('HORAS_ACUMULADAS', ascending=True),
                x='HORAS_ACUMULADAS',
                y='HOJA',
                orientation='h',
                text='HORAS_ACUMULADAS',
                labels={'HOJA': 'Integrante', 'HORAS_ACUMULADAS': 'Horas Acumuladas'},
                color='HORAS_ACUMULADAS',
                color_continuous_scale='Blues'
            )
            fig_bar.add_vline(x=HORAS_OBJETIVO_DEFAULT, line_dash="dash", line_color="red", annotation_text="Meta 480h")
            fig_bar.update_layout(height=450, showlegend=False)
            st.plotly_chart(fig_bar, use_container_width=True)
        else:
            st.info("No hay datos individuales para graficar.")

    with col_g2:
        st.subheader("🎓 Distribución por Carrera")
        if 'CARRERA' in df_generales.columns:
            df_carrera = df_generales['CARRERA'].value_counts().reset_index()
            df_carrera.columns = ['CARRERA', 'CANTIDAD']
            fig_pie = px.pie(
                df_carrera,
                names='CARRERA',
                values='CANTIDAD',
                hole=0.4,
                color_discrete_sequence=px.colors.qualitative.Pastel
            )
            fig_pie.update_layout(height=450)
            st.plotly_chart(fig_pie, use_container_width=True)

    # Tabla General
    st.subheader("📋 Lista General de Integrantes")
    st.dataframe(
        df_generales[['ESTATUS', 'CARRERA', 'MATRÍCULA', 'NOMBRE', 'FECHA INICIO OFICIAL']],
        use_container_width=True,
        hide_index=True
    )

# ---------------------------------------------------------
# VISTA 2: PANEL INDIVIDUAL DE INTEGRANTE
# ---------------------------------------------------------
else:
    st.title("👤 Panel Individual de Integrante")
    
    lista_alumnos = sorted(list(datos_usuarios.keys()))
    if not lista_alumnos:
        st.warning("No se encontraron hojas individuales de alumnos en el archivo.")
        st.stop()
        
    alumno_sel = st.sidebar.selectbox("Selecciona un Integrante:", lista_alumnos)
    
    df_u = datos_usuarios[alumno_sel]
    
    # Buscar info personal en DATOS GENERALES
    info_personal = df_generales[df_generales['NOMBRE'].str.contains(alumno_sel.split()[0], case=False, na=False)]
    
    # Encabezado del Perfil
    st.subheader(f"📌 Expediente: {alumno_sel}")
    
    if not info_personal.empty:
        row_p = info_personal.iloc[0]
        c1, c2, c3, c4 = st.columns(4)
        c1.markdown(f"**Estatus:** `{row_p.get('ESTATUS', 'N/A')}`")
        c2.markdown(f"**Carrera:** {row_p.get('CARRERA', 'N/A')}")
        c3.markdown(f"**Matrícula:** {row_p.get('MATRÍCULA', 'N/A')}")
        c4.markdown(f"**Correo:** {row_p.get('CORREO\\n INSTITUCIONAL', 'N/A')}")
    
    st.markdown("---")
    
    # Totales individuales
    horas_acumuladas = df_u['HORAS_DIARIAS'].sum()
    horas_restantes = max(0.0, HORAS_OBJETIVO_DEFAULT - horas_acumuladas)
    porcentaje = min(100.0, (horas_acumuladas / HORAS_OBJETIVO_DEFAULT) * 100)
    
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Horas Acumuladas", f"{round(horas_acumuladas, 1)} h")
    m2.metric("Horas Restantes", f"{round(horas_restantes, 1)} h")
    m3.metric("Porcentaje de Avance", f"{round(porcentaje, 1)} %")
    m4.metric("Días Registrados", f"{len(df_u)} días")
    
    # Barra de progreso
    st.progress(porcentaje / 100.0)
    
    st.markdown("### 📅 Registros de Asistencia")
    
    if not df_u.empty:
        # Gráfica de asistencias diarias
        fig_ind = px.bar(
            df_u,
            x='FECHA_DT',
            y='HORAS_DIARIAS',
            labels={'FECHA_DT': 'Fecha', 'HORAS_DIARIAS': 'Horas Trabajadas'},
            title="Horas trabajadas por día",
            color_discrete_sequence=['#2b5c8f']
        )
        fig_ind.update_layout(height=350)
        st.plotly_chart(fig_ind, use_container_width=True)
        
        # Tabla de detalle diario
        cols_mostrar = [c for c in ['FECHA', 'ENTRADA 1', 'SALIDA 1', 'TOTAL 1', 'ENTRADA 2', 'SALIDA 2', 'TOTAL 2', 'TOTAL HORAS DIARIAS'] if c in df_u.columns]
        st.dataframe(df_u[cols_mostrar], use_container_width=True, hide_index=True)
    else:
        st.info("Este integrante aún no tiene registros de asistencia inyectados.")
