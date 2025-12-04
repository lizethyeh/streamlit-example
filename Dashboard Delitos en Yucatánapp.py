import streamlit as st
import pandas as pd
import pydeck as pdk
import json
import requests

# URL del GeoJSON de Yucatán
url_geojson = "https://raw.githubusercontent.com/lizethyeh/streamlit-example/master/Yucatan.geojson"

# Cargar GeoJSON
geojson = requests.get(url_geojson).json()

# Cargar tu dataframe de delitos
df = pd.read_excel("delitos.xlsx")

# Asegura la columna con total:
df["Total"] = df[["Enero","Febrero","Marzo","Abril","Mayo","Junio",
                  "Julio","Agosto","Septiembre","Octubre","Noviembre","Diciembre"]].sum(axis=1)

# Unir por municipio
df_mapa = df.groupby("Municipio")["Total"].sum().reset_index()

# Agregar valores al GeoJSON
for feature in geojson["features"]:
    muni = feature["properties"]["NOMGEO"].upper()
    row = df_mapa[df_mapa["Municipio"].str.upper() == muni]
    if len(row) > 0:
        feature["properties"]["valor"] = int(row["Total"].values[0])
    else:
        feature["properties"]["valor"] = 0

# Crear capa choropleth
layer = pdk.Layer(
    "GeoJsonLayer",
    geojson,
    opacity=0.8,
    stroked=False,
    get_fill_color="[valor * 5, 50, 150]",  # escala simple
)

# Mapa
view = pdk.ViewState(latitude=20.97, longitude=-89.62, zoom=7)

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view,
    tooltip={"text": "{NOMGEO}: {valor}"}
))
