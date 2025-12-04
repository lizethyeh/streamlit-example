import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import zipfile
import requests

st.title("Mapa Choropleth Yucatán • Delitos 2015–2025")

# --- 1) Leer ZIP ---

zip_path = "dataframe limpio 2015 - 2025.zip"

with zipfile.ZipFile(zip_path, 'r') as z:
    # Toma el primer archivo Excel dentro del ZIP (o cámbialo por el nombre exacto)
    excel_files = [f for f in z.namelist() if f.endswith(".xlsx")]
    if len(excel_files) == 0:
        st.error("No se encontró ningún archivo Excel dentro del ZIP.")
        st.stop()

    df = pd.read_excel(z.open(excel_files[0]))

st.success("ZIP leído correctamente.")

# --- 2) Calcular total de incidentes por año (suma de meses) ---

columnas_meses = ["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                  "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

df["Total"] = df[columnas_meses].sum(axis=1)

# Agrupar por municipio
df_mapa = df.groupby("Municipio")["Total"].sum().reset_index()

# --- 3) Cargar GeoJSON desde GitHub ---

url_geojson = "https://raw.githubusercontent.com/lizethyeh/streamlit-example/master/Yucatan.geojson"
geojson = requests.get(url_geojson).json()

# --- 4) Insertar valores al GeoJSON ---

for feature in geojson["features"]:
    muni = feature["properties"]["NOMGEO"].upper()
    row = df_mapa[df_mapa["Municipio"].str.upper() == muni]

    if len(row) > 0:
        feature["properties"]["valor"] = int(row["Total"].values[0])
    else:
        feature["properties"]["valor"] = 0

# --- 5) Crear mapa Choropleth con PyDeck ---

layer = pdk.Layer(
    "GeoJsonLayer",
    geojson,
    opacity=0.85,
    stroked=False,
    get_fill_color="[valor * 4, 40, 120]",   # escala de color
    pickable=True,
)

view_state = pdk.ViewState(
    latitude=20.97, 
    longitude=-89.62, 
    zoom=7
)

st.pydeck_chart(
    pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "{NOMGEO}\nIncidentes: {valor}"}
    )
)
