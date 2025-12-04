import streamlit as st
import pandas as pd
import pydeck as pdk
import plotly.express as px
import zipfile
import json
import numpy as np
import unicodedata
import io

# ----------------------------
# Normalizar nombres
# ----------------------------
def normalize_municipio_name(name):
    name = str(name).lower().strip()
    name = unicodedata.normalize('NFKD', name).encode('ascii', 'ignore').decode('utf-8')
    return name


# ----------------------------
# Cargar archivos subidos
# ----------------------------
@st.cache_data
def load_user_data(csv_zip_file, geojson_file):

    # --- 1. Procesar ZIP con CSV ---
    with zipfile.ZipFile(csv_zip_file) as z:
        csv_names = [f for f in z.namelist() if f.endswith(".csv")]
        if len(csv_names) == 0:
            st.error("El ZIP no contiene un archivo CSV.")
            return None
        csv_data = z.read(csv_names[0])
        df = pd.read_csv(io.BytesIO(csv_data), encoding="latin1")

    # --- 2. Procesar GeoJSON ---
    geojson_data = json.load(geojson_file)

    # --- 3. Preprocesar DF ---
    month_columns = ['Enero','Febrero','Marzo','Abril','Mayo','Junio',
                     'Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']

    for col in month_columns:
        if col in df.columns:
            df[col] = df[col].fillna(0).astype(int)

    # Quedarse solo con Yucatán
    df = df[df["Entidad"] == "Yucatán"]

    # Convertir wide → long
    id_vars = [c for c in df.columns if c not in month_columns]

    df = pd.melt(
        df,
        id_vars=id_vars,
        value_vars=month_columns,
        var_name="Month",
        value_name="Incidents"
    )

    # Normalizar municipios
    df["Municipio"] = df["Municipio"].apply(normalize_municipio_name)

    # --- 4. Extraer propiedades del GeoJSON ---
    geo_items = []
    for feature in geojson_data["features"]:
        muni = normalize_municipio_name(feature["properties"]["NOMGEO"])
        geo_items.append({
            "Municipio": muni,
            "geometry": feature["geometry"]
        })

    geo_df = pd.DataFrame(geo_items)

    # --- 5. Merge final ---
    merged = geo_df.merge(df, on="Municipio", how="left")
    merged["Incidents"] = merged["Incidents"].fillna(0).astype(int)

    return merged, geojson_data


# ----------------------------
# Obtener datos agregados
# ----------------------------
def get_aggregated_data(df, year):
    if year is not None:
        df = df[df["Año"] == year]

    agg = df.groupby("Municipio")["Incidents"].sum().reset_index()
    return agg


# ----------------------------
# Colorear incidentes
# ----------------------------
def get_incident_color(value, vmin, vmax):
    alpha = 200
    if value == 0:
        return [240, 240, 240, alpha]

    log_v = np.log1p(value)

    if vmax == vmin:
        return [150, 80, 80, alpha]

    log_min = np.log1p(vmin)
    log_max = np.log1p(vmax)

    norm = (log_v - log_min) / (log_max - log_min)

    r = int(255 * norm)
    g = int(max(0, 255 * (1 - norm) - 40))
    b = int(max(0, 255 * (1 - norm) - 40))

    return [r, g, b, alpha]


# ----------------------------
# APP PRINCIPAL
# ----------------------------
def main():

    st.title("Dashboard de Incidentes en Yucatán (sin GeoPandas)")
    st.write("Sube tu **ZIP con CSV** y tu **GeoJSON**.")

    uploaded_zip = st.file_uploader("Sube ZIP con datos (CSV dentro)", type=["zip"])
    uploaded_geojson = st.file_uploader("Sube GeoJSON con los municipios", type=["geojson"])

    if uploaded_zip and uploaded_geojson:

        st.success("Archivos cargados. Procesando...")

        merged_df, geojson_raw = load_user_data(uploaded_zip, uploaded_geojson)

        # ----- FILTROS -----
        years = ["Todos"] + sorted(merged_df["Año"].dropna().unique().tolist())
        selected_year = st.sidebar.selectbox("Año:", years)

        year_filter = None if selected_year == "Todos" else selected_year

        # ----- MAPA -----
        st.header("Mapa de Incidentes por Municipio")

        agg = get_aggregated_data(merged_df, year_filter)

        vmin, vmax = agg["Incidents"].min(), agg["Incidents"].max()

        # Añadir color al GeoJSON
        muni_to_value = dict(zip(agg["Municipio"], agg["Incidents"]))

        for feature in geojson_raw["features"]:
            muni_norm = normalize_municipio_name(feature["properties"]["NOMGEO"])
            val = muni_to_value.get(muni_norm, 0)
            feature["properties"]["Incidents"] = int(val)
            feature["properties"]["color"] = get_incident_color(val, vmin, vmax)

        geo_layer = pdk.Layer(
            "GeoJsonLayer",
            geojson_raw,
            pickable=True,
            get_fill_color="properties.color",
            get_line_color=[0, 0, 0, 80],
            get_line_width=30,
            auto_highlight=True
        )

        view_state = pdk.ViewState(
            latitude=20.98,
            longitude=-89.62,
            zoom=7,
            pitch=45
        )

        map_deck = pdk.Deck(
            layers=[geo_layer],
            initial_view_state=view_state,
            tooltip={"html": "<b>{properties.NOMGEO}</b><br>Incidentes: {properties.Incidents}"}
        )

        st.pydeck_chart(map_deck)

        # ----- TENDENCIAS -----
        st.header("Tendencias por Municipio")

        trend = merged_df.groupby(["Año", "Municipio"])["Incidents"].sum().reset_index()

        fig = px.line(
            trend,
            x="Año",
            y="Incidents",
            color="Municipio",
            title="Tendencia de incidentes"
        )
        st.plotly_chart(fig)

        # ----- BARRAS POR BIEN JURÍDICO -----
        st.header("Incidentes por Bien Jurídico Afectado")

        bien = merged_df.groupby("Bien jurídico afectado")["Incidents"].sum().reset_index()
        fig2 = px.bar(bien, x="Bien jurídico afectado", y="Incidents")
        st.plotly_chart(fig2)


if __name__ == "__main__":
    main()
