import pandas as pd
import streamlit as st

# Configuración de la interfaz web
st.set_page_config(page_title="Control de Horas", layout="wide", page_icon="⏱️")
st.title("⏱️ Consulta Visual de Horas y Asistencias")

# ---------------------------------------------------------
# 1. CARGA DEL ARCHIVO (SUBIR DESDE LA INTERFAZ)
# ---------------------------------------------------------
st.sidebar.header("📁 Cargar Datos")
archivo_subido = st.sidebar.file_uploader("Sube tu archivo conteo.xlsx", type=["xlsx", "xls"])

if archivo_subido is not None:
    df_archivo = pd.read_excel(archivo_subido)

    df_archivo["FECHAS/HORAS"] = pd.to_datetime(df_archivo["FECHAS/HORAS"], errors="coerce")
    usuarios = {
        1: "MISAEL RIVERA LÓPEZ",
        2: "LUDWING PINEDA CUEVAS",
        3: "JAVIER GUERRERO SALAS",
        5: "KATHERINE MENDEZ MARQUEZ",
        6: "FÁTIMA PACHECO ZACARÍAS",
        7: "LUIS FERNANDO CASTILLO GARCÍA",
        9: "KARLA YAMILET AGUILAR RAMÍREZ",
        10: "ALEJANDRO RAMOS MAYEN",
        12: "CHRISTIAN GONZÁLEZ GUTIÉRREZ",
        13: "CESAR YAIR ESPINOSA MARTINEZ",
        15: "FERNANDO JAVIER RAMIREZ GARCIA",
        17: "RAFAEL EDUARDO LAGUNAS GÓMEZ",
        19: "MARIA NATALIA CABRERA MONJARAS",
    }

    df_archivo["NOMBRE"] = df_archivo["NOMBRE"].map(usuarios)
    df_archivo["ASISTENCIAS"] = df_archivo["ASISTENCIAS"].map({0: "ENTRADA", 1: "SALIDA"})

    # ---------------------------------------------------------
    # 2. LIMPIEZA DE DUPLICADOS Y CREACIÓN DE IDENTIFICADOR
    # ---------------------------------------------------------
    df_archivo = df_archivo.sort_values(by=["NOMBRE", "FECHAS/HORAS"])
    df_archivo["MARCA_ANTERIOR"] = df_archivo.groupby("NOMBRE")["ASISTENCIAS"].shift(1)

    df_archivo = df_archivo[df_archivo["ASISTENCIAS"] != df_archivo["MARCA_ANTERIOR"]].copy()
    df_archivo.drop(columns=["MARCA_ANTERIOR"], inplace=True)

    df_archivo["FECHA"] = df_archivo["FECHAS/HORAS"].dt.date
    df_archivo = df_archivo.sort_values(by=["NOMBRE", "FECHAS/HORAS"]).reset_index(drop=True)

    df_archivo["IDENTIFICADOR"] = df_archivo.groupby(["NOMBRE", "FECHA"])["ASISTENCIAS"].apply(
        lambda x: (x == "ENTRADA").cumsum()
    ).reset_index(level=[0,1], drop=True)

    def formatear_timedelta(td):
        if pd.isna(td):
            return "00:00:00"
        total_segundos = int(td.total_seconds())
        horas = total_segundos // 3600
        minutos = (total_segundos % 3600) // 60
        segundos = total_segundos % 60
        return f"{horas:02d}:{minutos:02d}:{segundos:02d}"

    # ---------------------------------------------------------
    # 3. CREACIÓN DE TURNOS Y CÁLCULO DE TIEMPOS
    # ---------------------------------------------------------
    df_turno = df_archivo.pivot_table(
        index=["NOMBRE", "FECHA", "IDENTIFICADOR"],
        columns="ASISTENCIAS",
        values="FECHAS/HORAS",
        aggfunc="first"
    ).reset_index()

    df_turno["TURNO"] = df_turno.groupby(["NOMBRE", "FECHA"]).cumcount() + 1
    df_turno = df_turno[df_turno["TURNO"] <= 3].copy()

    df_turno["TIEMPO_TURNO"] = df_turno["SALIDA"] - df_turno["ENTRADA"]

    df_turno["ENTRADA"] = df_turno["ENTRADA"].dt.strftime("%H:%M:%S")
    df_turno["SALIDA"] = df_turno["SALIDA"].dt.strftime("%H:%M:%S")
    df_turno["TOTAL_TURNO"] = df_turno["TIEMPO_TURNO"].apply(formatear_timedelta)

    # ---------------------------------------------------------
    # 4. REORGANIZACIÓN HORIZONTAL A 3 TURNOS
    # ---------------------------------------------------------
    df_semana = df_turno.pivot(
        index=["NOMBRE", "FECHA"],
        columns="TURNO",
        values=["ENTRADA", "SALIDA", "TOTAL_TURNO"]
    )

    columnas_fijas = [
        ("ENTRADA", 1), ("SALIDA", 1), ("TOTAL_TURNO", 1),
        ("ENTRADA", 2), ("SALIDA", 2), ("TOTAL_TURNO", 2),
        ("ENTRADA", 3), ("SALIDA", 3), ("TOTAL_TURNO", 3)
    ]

    df_semana = df_semana.reindex(columns=pd.MultiIndex.from_tuples(columnas_fijas))
    df_semana.columns = [f"{col[0]} {col[1]}" for col in df_semana.columns]
    df_semana = df_semana.reset_index()

    # ---------------------------------------------------------
    # 5. CÁLCULO DE TOTAL HORAS DIARIAS
    # ---------------------------------------------------------
    horas_totales_dia = df_turno.groupby(['NOMBRE', 'FECHA'])['TIEMPO_TURNO'].sum().reset_index()

    horas_totales_dia['HORAS_DECIMAL'] = horas_totales_dia['TIEMPO_TURNO'].dt.total_seconds() / 3600
    horas_totales_dia['TOTAL HORAS DIARIAS'] = horas_totales_dia['TIEMPO_TURNO'].apply(formatear_timedelta)

    df_semana = df_semana.merge(horas_totales_dia[['NOMBRE', 'FECHA', 'TOTAL HORAS DIARIAS']], on=['NOMBRE', 'FECHA'], how='left')

    # ---------------------------------------------------------
    # 6. TRADUCCIÓN DE FECHAS A ESPAÑOL
    # ---------------------------------------------------------
    dias = {
        'Monday': 'lunes', 'Tuesday': 'martes', 'Wednesday': 'miércoles',
        'Thursday': 'jueves', 'Friday': 'viernes', 'Saturday': 'sábado', 'Sunday': 'domingo'
    }
    meses = {
        'January': 'enero', 'February': 'febrero', 'March': 'marzo', 'April': 'abril',
        'May': 'mayo', 'June': 'junio', 'July': 'julio', 'August': 'agosto',
        'September': 'septiembre', 'October': 'octubre', 'November': 'noviembre', 'December': 'diciembre'
    }

    fechas_dt = pd.to_datetime(df_semana['FECHA'])
    dia_nom = fechas_dt.dt.day_name().map(dias)
    mes_nom = fechas_dt.dt.month_name().map(meses)

    df_semana['FECHA_FORMATO'] = dia_nom + ', ' + fechas_dt.dt.day.astype(str) + ' de ' + mes_nom + ' del ' + fechas_dt.dt.year.astype(str)

    # ---------------------------------------------------------
    # 7. INTERFAZ VISUAL EN STREAMLIT POR USUARIO
    # ---------------------------------------------------------
    st.subheader("👤 Consulta por Colaborador")

    lista_usuarios = sorted([n for n in df_semana["NOMBRE"].dropna().unique()])
    usuario_seleccionado = st.selectbox("Selecciona o escribe el nombre del colaborador:", lista_usuarios)

    if usuario_seleccionado:
        df_usr_semana = df_semana[df_semana["NOMBRE"] == usuario_seleccionado]
        df_usr_horas = horas_totales_dia[horas_totales_dia["NOMBRE"] == usuario_seleccionado]

        # Métricas
        horas_acumuladas = df_usr_horas["HORAS_DECIMAL"].sum()
        META_SEMANAL = 48.0
        horas_faltantes = max(0.0, META_SEMANAL - horas_acumuladas)
        porcentaje = min(100.0, (horas_acumuladas / META_SEMANAL) * 100)

        col1, col2, col3 = st.columns(3)
        col1.metric("Horas Trabajadas", f"{horas_acumuladas:.2f} hrs")
        col2.metric("Meta Semanal", f"{META_SEMANAL:.2f} hrs")
        col3.metric("Cumplimiento", f"{porcentaje:.1f}%")

        st.progress(porcentaje / 100)

        # Gráficas
        st.subheader("📊 Comparativa y Avance")
        col_g1, col_g2 = st.columns(2)

        with col_g1:
            st.markdown("**Horas por Día**")
            df_graf_dia = df_usr_horas.copy()
            df_graf_dia["FECHA"] = df_graf_dia["FECHA"].astype(str)
            st.bar_chart(data=df_graf_dia, x="FECHA", y="HORAS_DECIMAL")

        with col_g2:
            st.markdown("**Horas Trabajadas vs. Restantes**")
            df_progreso = pd.DataFrame({
                "Estatus": ["Acumuladas", "Faltantes"],
                "Horas": [horas_acumuladas, horas_faltantes]
            })
            st.bar_chart(data=df_progreso, x="Estatus", y="Horas")

        # Tabla con detalle
        st.subheader("📋 Detalle de Asistencias")
        cols_mostrar = [
            "FECHA_FORMATO", "ENTRADA 1", "SALIDA 1", "TOTAL_TURNO 1",
            "ENTRADA 2", "SALIDA 2", "TOTAL_TURNO 2",
            "ENTRADA 3", "SALIDA 3", "TOTAL_TURNO 3", "TOTAL HORAS DIARIAS"
        ]
        st.dataframe(df_usr_semana[cols_mostrar], use_container_width=True)
else:
    st.info("👈 Por favor, sube tu archivo `conteo.xlsx` en el panel lateral izquierdo para ver el reporte.")