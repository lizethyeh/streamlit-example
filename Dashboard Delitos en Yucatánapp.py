# app.py
import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import plotly.express as px
import json
import numpy as np
import unicodedata
import zipfile
from io import BytesIO

# -------------------------
# Utilidades
# -------------------------
def normalize_municipio_name(name):
    name = str(name).lower()
    name = name.strip()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    # elimina tildes, etc. y espacios extremos
    return name

@st.cache_data(show_spinner=False)
def load_and_preprocess_data(geojson_path='Yucatan.geojson', zip_path='dataframe limpio 2015 - 2025.zip'):
    """
    Lee el geojson y el zip con csv (busca el primer csv dentro del zip).
    Devuelve un GeoDataFrame unido con las columnas de datos y columnas calculadas:
      - TotalAnual: suma de los 12 meses por registro
      - TotalIncidentes (agregado por Municipio y Año)
    """
    # --- leer geojson ---
    gdf = gpd.read_file(geojson_path)
    # Asegurarse de tener una columna con el nombre del municipio; aquí asumimos NOMGEO (como en tu código original)
    if 'NOMGEO' in gdf.columns:
        gdf['Municipio'] = gdf['NOMGEO']
    elif 'municipio' in gdf.columns:
        gdf['Municipio'] = gdf['municipio']
    # Normalizar nombres en geo
    gdf['Municipio_norm'] = gdf['Municipio'].apply(normalize_municipio_name)

    # --- leer zip y extraer CSV (primer CSV encontrado) ---
    with zipfile.ZipFile(zip_path, 'r') as z:
        # buscar primer archivo .csv
        csv_names = [n for n in z.namelist() if n.lower().endswith('.csv')]
        if len(csv_names) == 0:
            raise FileNotFoundError("No se encontró ningún archivo .csv dentro del zip especificado.")
        csv_name = csv_names[0]
        with z.open(csv_name) as f:
            # intentar leer con latin1 y utf-8 por seguridad
            try:
                df = pd.read_csv(f, encoding='latin1')
            except Exception:
                f.seek(0)
                df = pd.read_csv(f, encoding='utf-8')

    # --- normalizar y limpiar df ---
    # Asegurarse de que exista la columna 'Entidad' y filtrar Yucatán
    if 'Entidad' in df.columns:
        df = df[df['Entidad'].str.strip().str.lower() == 'yucatán'.lower()]
    # Normalizar columna Municipio (varios nombres posibles: 'Municipio' o 'municipio')
    municipio_col = None
    for c in df.columns:
        if c.lower() == 'municipio':
            municipio_col = c
            break
    if municipio_col is None:
        raise KeyError("No se encontró columna 'Municipio' en el CSV dentro del zip.")
    df['Municipio_norm'] = df[municipio_col].apply(normalize_municipio_name)

    # Definir columnas de meses (acepta tanto con mayúsculas como variantes)
    meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
    month_cols = [c for c in df.columns if c in meses]
    # Si no están exactamente con esos nombres, buscar columnas similares (por ejemplo 'enero', 'ENERO')
    if len(month_cols) == 0:
        for m in meses:
            for c in df.columns:
                if c.lower() == m.lower():
                    month_cols.append(c)
                    break

    # Si aún no encuentra meses, no los convierte, pero se intentará sumar cualquier columna que parezca ser mensual
    # Asegurar que las columnas de meses existan y sean numéricas
    for col in month_cols:
        df[col] = pd.to_numeric(df[col].fillna(0), errors='coerce').fillna(0).astype(int)

    # Calcular TotalAnual sumando meses (si month_cols está vacío, crear TotalAnual a partir de columna 'Total' si existe)
    if len(month_cols) > 0:
        df['TotalAnual'] = df[month_cols].sum(axis=1).astype(int)
    elif 'Total' in df.columns:
        df['TotalAnual'] = pd.to_numeric(df['Total'].fillna(0), errors='coerce').fillna(0).astype(int)
    else:
        # si no hay cómo calcular, crear columna con ceros
        df['TotalAnual'] = 0

    # Asegurarse de que exista columna 'Año' o 'Año' variante
    year_col = None
    for c in df.columns:
        if c.lower() in ['año','ano','aÑo','año']:
            year_col = c
            break
    # si no hay, intentar 'Año' exacto o 'Year'
    if year_col is None:
        for c in df.columns:
            if c.lower() == 'año' or c.lower() == 'year':
                year_col = c
                break
    if year_col is None:
        # si no existe, intentar inferir por columna 'Año' en otra codificación
        if 'Año' in df.columns:
            year_col = 'Año'
        else:
            raise KeyError("No se encontró una columna de año ('Año' / 'Year') en el CSV.")

    df = df.rename(columns={year_col: 'Año'})

    # Mantener columnas relevantes (para prevenir duplicados masivos)
    # columnas que solemos necesitar: Año, Municipio_norm, Bien jurídico afectado, Tipo de delito, Subtipo de delito, Modalidad, TotalAnual, meses...
    posibles = ['Bien jurídico afectado','Tipo de delito','Subtipo de delito','Modalidad']
    cols_present = [c for c in posibles if c in df.columns]
    keep_cols = ['Año','Municipio_norm','TotalAnual'] + cols_present + month_cols
    df = df[ [c for c in keep_cols if c in df.columns] + [] ]  # preserva orden

    # Renombrar para unir (usa 'Municipio_norm')
    df = df.rename(columns={'Municipio_norm':'Municipio'})

    # --- agregar por Municipio + Año (sumar TotalAnual) ---
    agg = df.groupby(['Año','Municipio'] + cols_present, dropna=False, as_index=False)['TotalAnual'].sum()
    # Si hay múltiples filas para el mismo Año-Municipio sin distinguir por Bien jurídico etc, agrupación anterior los mantiene separados.
    # Para total por municipio-año general (sin distinguir por Bien jurídico), creamos otro agregado:
    total_por_mun_anyo = df.groupby(['Año','Municipio'], as_index=False)['TotalAnual'].sum().rename(columns={'TotalAnual':'TotalIncidentes'})

    # --- Unir geometría con totales por municipio-año ---
    # Primera, agrupar geometría (una fila por municipio) desde gdf
    geo_unique = gdf.drop_duplicates(subset=['Municipio_norm']).set_index('Municipio_norm')
    geo_unique = geo_unique[['geometry']].rename_axis('Municipio').reset_index()
    geo_unique['Municipio'] = geo_unique['Municipio'].apply(normalize_municipio_name)

    # Merge: crear un GeoDataFrame para cada año (facilitará filtros) -> haremos un merge cruzado por año
    # Obtener lista de años
    years = sorted(total_por_mun_anyo['Año'].unique().tolist())

    # Merge geometría con totales
    merged_list = []
    for y in years:
        tmp = total_por_mun_anyo[total_por_mun_anyo['Año'] == y].copy()
        tmp['Municipio'] = tmp['Municipio'].apply(normalize_municipio_name)
        mg = geo_unique.merge(tmp, left_on='Municipio', right_on='Municipio', how='left')
        mg['Año'] = y
        mg['TotalIncidentes'] = mg['TotalIncidentes'].fillna(0).astype(int)
        merged_list.append(mg)

    merged_gdf = pd.concat(merged_list, ignore_index=True)
    # Convertir a GeoDataFrame (geometry existe)
    merged_gdf = gpd.GeoDataFrame(merged_gdf, geometry='geometry', crs=gdf.crs)

    # También hacemos una versión "long" del detalle (agg) unido con geometría por municipio (sin sumar por año)
    # normalizar nombres en agg
    if 'Municipio' in agg.columns:
        agg['Municipio'] = agg['Municipio'].apply(normalize_municipio_name)

    # Devolver: merged_gdf (por año y municipio), df_original_agg (detalle si se necesita), years list
    return merged_gdf, agg, years

# -------------------------
# Funciones auxiliares para colores y gráficos
# -------------------------
def get_incident_color(incidents, min_incidents, max_incidents):
    alpha = 200
    if incidents == 0 or max_incidents == 0:
        return [240, 240, 240, alpha]
    # Escala log para distribuir colores
    log_inc = np.log1p(incidents)
    min_log = np.log1p(max(min_incidents, 0))
    max_log = np.log1p(max_incidents)
    if max_log == min_log:
        normalized = 0.5
    else:
        normalized = (log_inc - min_log) / (max_log - min_log)
    r = int(255 * normalized)
    g = int(max(0, 255 * (1 - normalized) - 50))
    b = int(max(0, 255 * (1 - normalized) - 50))
    return [r, g, b, alpha]

# -------------------------
# Streamlit App
# -------------------------
def main():
    st.set_page_config(layout='wide', page_title='Dashboard Incidentes Yucatán')
    st.title("Dashboard — Incidentes en Yucatán (2015-2025)")
    st.write("Carga: `Yucatan.geojson`  +  `dataframe limpio 2015 - 2025.zip`")

    try:
        merged_gdf, detail_df, years = load_and_preprocess_data()
    except Exception as e:
        st.error(f"Error al cargar datos: {e}")
        return

    # Sidebar filtros
    st.sidebar.header("Filtros")
    year_options = ['Todos los años'] + years
    selected_year = st.sidebar.selectbox("Seleccionar Año", year_options)

    # Lista municipios a seleccionar (desde merged_gdf)
    municipios = sorted(merged_gdf['Municipio'].unique().tolist())
    selected_municipios = st.sidebar.multiselect("Seleccionar municipios", municipios, default=municipios)

    # Filtro por Bien jurídico / Tipo de delito (si existen en detail_df)
    filter_col = None
    filter_val = None
    posibles = ['Bien jurídico afectado','Tipo de delito','Subtipo de delito']
    presente = [c for c in posibles if c in detail_df.columns]
    if len(presente) > 0:
        filter_col = st.sidebar.selectbox("Filtrar detalle por", ['Ninguno'] + presente)
        if filter_col and filter_col != 'Ninguno':
            valores = sorted(detail_df[filter_col].dropna().unique().tolist())
            if valores:
                filter_val = st.sidebar.selectbox(f"Seleccionar {filter_col}", valores)

    st.sidebar.markdown("---")
    if st.sidebar.checkbox("Mostrar tabla de datos (merged)", value=False):
        st.subheader("Tabla unida (por municipio y año)")
        st.dataframe(merged_gdf)

    # Filtrar merged_gdf por año y municipios
    if selected_year != 'Todos los años':
        df_map = merged_gdf[merged_gdf['Año'] == selected_year].copy()
    else:
        # si todos los años: sumar TotalIncidentes por municipio en todo el periodo
        df_map = merged_gdf.groupby('Municipio', as_index=False).agg({'geometry':'first','TotalIncidentes':'sum'}).rename(columns={'TotalIncidentes':'TotalIncidentes'})
        # añadir columna 'Año' para consistencia
        df_map['Año'] = 'Todos'

    if selected_municipios:
        df_map = df_map[df_map['Municipio'].isin(selected_municipios)]

    if df_map.empty:
        st.warning("No hay datos con los filtros seleccionados.")
        return

    # Calcular colores
    min_inc = int(df_map['TotalIncidentes'].min())
    max_inc = int(df_map['TotalIncidentes'].max())
    df_map['color'] = df_map['TotalIncidentes'].apply(lambda x: get_incident_color(int(x), min_inc, max_inc))

    # Convertir a GeoJSON para pydeck
    geojson_data = json.loads(df_map.to_json())

    # PyDeck layer
    geojson_layer = pdk.Layer(
        'GeoJsonLayer',
        geojson_data,
        get_fill_color='properties.color',
        get_line_color=[0, 0, 0, 100],
        pickable=True,
        auto_highlight=True
    )

    # vista inicial centrada en Yucatán (aprox)
    view_state = pdk.ViewState(latitude=20.97537, longitude=-89.61696, zoom=7.3, pitch=30)

    tooltip = {"html": "<b>Municipio:</b> {properties.Municipio} <br/> <b>Total Incidentes:</b> {properties.TotalIncidentes}"}

    st.subheader("Mapa — Incidentes por Municipio")
    r = pdk.Deck(layers=[geojson_layer], initial_view_state=view_state, tooltip=tooltip, map_style='mapbox://styles/mapbox/light-v9')
    st.pydeck_chart(r)

    # Gráficas: tendencia por municipio (line) y barras por Bien jurídico (si existe)
    st.subheader("Tendencias y desagregaciones")

    # Preparar dataframe de detalle (detail_df) para gráficos
    df_detail = detail_df.copy()
    # Normalizar municipio en detail_df
    if 'Municipio' in df_detail.columns:
        df_detail['Municipio'] = df_detail['Municipio'].apply(normalize_municipio_name)
    # aplicar filtro por municipio si se seleccionaron
    if selected_municipios:
        df_detail = df_detail[df_detail['Municipio'].isin(selected_municipios)]

    # Aplicar filtro por columna si existe
    if filter_col and filter_col != 'Ninguno' and filter_val:
        df_detail = df_detail[df_detail[filter_col] == filter_val]

    # Line chart: si hay columna 'Año' y 'TotalAnual' en detail_df
    if 'Año' in df_detail.columns and 'TotalAnual' in df_detail.columns:
        yearly = df_detail.groupby(['Año','Municipio'], as_index=False)['TotalAnual'].sum()
        fig_line = px.line(yearly, x='Año', y='TotalAnual', color='Municipio', title='Tendencia anual por Municipio',
                           labels={'TotalAnual':'Número de incidentes','Año':'Año'})
        st.plotly_chart(fig_line, use_container_width=True)
    else:
        st.info("No hay datos de detalle para mostrar la tendencia por municipio.")

    # Bar chart por Bien jurídico afectado (si existe)
    if 'Bien jurídico afectado' in df_detail.columns:
        bar_df = df_detail.groupby('Bien jurídico afectado', as_index=False)['TotalAnual'].sum().sort_values('TotalAnual', ascending=False)
        fig_bar = px.bar(bar_df, x='Bien jurídico afectado', y='TotalAnual', title='Incidentes por Bien Jurídico Afectado (Total periodo)',
                         labels={'TotalAnual':'Número de incidentes','Bien jurídico afectado':'Bien jurídico afectado'})
        st.plotly_chart(fig_bar, use_container_width=True)
    else:
        st.info("No hay la columna 'Bien jurídico afectado' en los datos para la gráfica de barras.")

    st.markdown("---")
    st.caption("Archivo geojson usado: `Yucatan.geojson` — Zip leído: `dataframe limpio 2015 - 2025.zip` (primer CSV dentro del zip).")

if __name__ == "__main__":
    main()
