import streamlit as st
import pandas as pd
import pydeck as pdk
import requests
import zipfile
import io
import json

# ----------------------------
# CONFIGURACIÓN
# ----------------------------

GEOJSON_URL = "https://github.com/lizethyeh/streamlit-example/blob/master/Yucatan.geojson"
ZIP_URL = "https://raw.githubusercontent.com/lizethyeh/streamlit-example/master/dataframe%20limpio%202015%20-%202025.zip"
"
CSV_NAME_INSIDE_ZIP = "dataframe_limpio_2015_2025.csv"   # <-- cambia si tu CSV tiene otro nombre

st.title("Mapa de Incidentes Yucatán 2015–2025")


# ----------------------------
# 1. CARGAR ZIP DESDE GITHUB
# ----------------------------
@st.cache_data
def load_zip_csv(zip_url, csv_filename):
    response = requests.get(zip_url)
    if response.status_code != 200:
        st.error("Error al descargar ZIP desde GitHub")
        return None
    
    zip_bytes = io.BytesIO(response.content)
    with zipfile.ZipFile(zip_bytes) as z:
        with z.open(csv_filename) as f:
            df = pd.read_csv(f)
    
    return df


# ----------------------------
# 2. CARGAR GEOJSON DESDE GITHUB
# ----------------------------
@st.cache_data
def load_geojson(url):
    response = requests.get(url)
    if response.status_code != 200:
        st.error("No se pudo descargar el GeoJSON desde GitHub")
        return None
    
    return json.loads(response.text)


df = load_zip_csv(ZIP_URL, CSV_NAME_INSIDE_ZIP)
geojson_data = load_geojson(GEOJSON_URL)

if df is None or geojson_data is None:
    st.stop()


# ----------------------------
# 3. PROCESAMIENTO
# ----------------------------
st.subheader("Vista previa de datos")
st.dataframe(df.head())

# Crear columna total de incidentes (suma de meses)
month_cols = ["Enero","Febrero","Marzo","Abril","Mayo","Junio","Julio",
              "Agosto","Septiembre","Octubre","Noviembre","Diciembre"]

df["TotalIncidentes"] = df[month_cols].sum(axis=1)


# ----------------------------
# 4. MAPA EN PYDECK
# ----------------------------

layer = pdk.Layer(
    "GeoJsonLayer",
    geojson_data,
    opacity=0.6,
    get_fill_color="[255 * (properties.TotalIncidentes / maxTotal), 0, 0]",
    pickable=True
)

view_state = pdk.ViewState(
    latitude=20.97,
    longitude=-89.62,
    zoom=7
)

# Agregar variable global: maxTotal
max_total = df["TotalIncidentes"].max()
geojson_data["maxTotal"] = max_total

st.pydeck_chart(pdk.Deck(
    layers=[layer],
    initial_view_state=view_state,
    tooltip={"html": "<b>{Municipio}</b><br>Total: {TotalIncidentes}"}
))
