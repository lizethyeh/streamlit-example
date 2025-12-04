import streamlit as st
import pandas as pd
import geopandas as gpd
import pydeck as pdk
import zipfile
import numpy as np

st.title("Mapa Choropleth de Incidentes en Yucatán (2015–2025)")

# =========================
# RUTAS DE TUS ARCHIVOS
# =========================
CSV_ZIP_PATH = "data/dataframe_limpio_2015_2025.zip"
GEOJSON_PATH = "data/Yucatan.geojson"

# =========================
# CARGA DEL CSV DESDE ZIP
# =========================
st.write("Cargando base de datos...")

with zipfile.ZipFile(CSV_ZIP_PATH, 'r') as z:
    z.extractall("data/tmp")
    extracted_files = z.namelist()

# Identifica automáticamente el CSV dentro del ZIP
csv_inside_zip = [f for f in extracted_files if f.endswith(".csv")][0]

# Carga del CSV
df = pd.read_csv(f"data/tmp/{csv_inside_zip}", encoding="utf-8")

st.write("Datos cargados:", df.head())

# =========================
# CARGA DEL GEOJSON
# =========================
gdf = gpd.read_file(GEOJSON_PATH)

# Asegurar nombres de columnas iguales
df["Municipio"] = df["Municipio"].str.upper()
gdf["name"] = gdf["name"].str.upper()

# =========================
# SUMA DE INCIDENTES POR MES
# =========================
meses = [
    "Enero","Febrero","Marzo","Abril","Mayo","Junio",
    "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"
]

df["TotalIncidentes"] = df[meses].sum(axis=1)

# =========================
# AGRUPAR INCIDENTES POR MUNICIPIO
# =========================
df_grouped = df.groupby("Municipio")["TotalIncidentes"].sum().reset_index()

# =========================
# HACER MERGE GEOESPACIAL
# =========================
merged_gdf = gdf.merge(df_grouped, left_on="name", right_on="Municipio", how="left")

# Rellenar NaN con 0
merged_gdf["TotalIncidentes"] = merged_gdf["TotalIncidentes"].fillna(0)

# =========================
# ESCALA LOGARÍTMICA
# =========================
merged_gdf["log_incidentes"] = np.log1p(merged_gdf["TotalIncidentes"])

# =========================
# PREPARAR GEOJSON PARA PYDECK
# =========================
geojson_dict = merged_gdf.__geo_interface__

# =========================
# CONFIGURAR MAPA PYDECK
# =========================
layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_dict,
    opacity=0.7,
    stroked=True,
    filled=True,
    get_fill_color="[(log_incidentes * 40), 0, 150, 180]",
    get_line_color=[255, 255, 255],
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=20.97,  # centro Yucatán
    longitude=-89.62,
    zoom=7
)

r = pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={
        "text": "Municipio: {name}\nIncidentes: {TotalIncidentes}"
    }
)

st.pydeck_chart(r)

st.success("Mapa generado correctamente")
