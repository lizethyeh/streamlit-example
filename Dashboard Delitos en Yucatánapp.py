import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import pydeck as pdk
import json
import unicodedata

# --- 1. Load Data and Define Helper Functions ---

# Load delitos_final DataFrame
# In a real Streamlit app, you might load this from a persistent storage
# For this example, we'll assume it's already generated as 'delitos_final.csv'
# and load it from the Colab Drive path.
# If running locally, ensure 'delitos_final.csv' is in the same directory or provide full path.
try:
    delitos_final = pd.read_csv('delitos_final.csv')
    # Ensure 'Año' is int for filtering
    delitos_final['Año'] = delitos_final['Año'].astype(int)
except FileNotFoundError:
    st.error("Error: 'delitos_final.csv' not found. Please ensure the file is in the correct path.")
    st.stop()


# Load Coordenadas_Json (GeoJSON for map)
try:
    with open('/content/drive/MyDrive/Herramientas Datos/Yucatan.geojson', 'r', encoding='utf-8') as f:
        Coordenadas_Json = json.load(f)
except FileNotFoundError:
    st.error("Error: 'Yucatan.geojson' not found. Please ensure the file is in the correct path.")
    st.stop()

# Helper function to normalize strings for matching (used in both charts and map)
def normalize_string_for_match(s):
    if not isinstance(s, str):
        return s
    nfkd_form = unicodedata.normalize('NFKD', s)
    stripped_accent_string = ''.join([c for c in nfkd_form if not unicodedata.combining(c)])
    return stripped_accent_string.upper().strip()

# Helper function for map color scaling (red/orange/pink tones with white for zero)
def get_log_color(d, log_min_val, log_max_val):
    if d == 0:
        return [255, 255, 255, 180]  # White fill for zero incidents

    if log_max_val == log_min_val:
        normalized = 0
    else:
        log_d = np.log1p(d)
        normalized = (log_d - log_min_val) / (log_max_val - log_min_val)

    if normalized < 0.5:
        # Interpolate from light peach/pinkish orange to strong orange
        t = normalized * 2
        r = int(255)
        g = int(200 - (100 * t))
        b = int(180 - (180 * t))
    else:
        # Interpolate from strong orange to pure red
        t = (normalized - 0.5) * 2
        r = int(255)
        g = int(100 - (100 * t))
        b = int(0)

    return [r, g, b, 180]

# Helper function for creating incidents bar chart (v2 from notebook)
def create_incidents_bar_chart_v2(
    df: pd.DataFrame,
    min_year: int,
    max_year: int,
    municipio_filter_list: list = None
):
    filtered_df = df[(df['Año'] >= min_year) & (df['Año'] <= max_year)].copy()

    if municipio_filter_list:
        normalized_municipios = [normalize_string_for_match(m) for m in municipio_filter_list]
        filtered_df['Municipio_x_cleaned'] = filtered_df['Municipio_x'].apply(normalize_string_for_match)
        filtered_df = filtered_df[filtered_df['Municipio_x_cleaned'].isin(normalized_municipios)]
        filtered_df = filtered_df.drop(columns=['Municipio_x_cleaned'])

    aggregated_data = filtered_df.groupby('Bien jurídico afectado')['Total de Incidentes'].sum().reset_index()
    aggregated_data = aggregated_data.sort_values(by='Total de Incidentes', ascending=False)

    def wrap_label_text(label):
        words = label.split()
        wrapped_label = []
        current_line = []
        for word in words:
            current_line.append(word)
            if len(' '.join(current_line)) > 15 and len(words) > 1:
                wrapped_label.append(' '.join(current_line))
                current_line = []
        if current_line:
            wrapped_label.append(' '.join(current_line))
        return '<br>'.join(wrapped_label[:3])

    aggregated_data['Bien jurídico afectado'] = aggregated_data['Bien jurídico afectado'].apply(wrap_label_text)

    chart_title = f'Total de Incidentes por Bien Jurídico Afectado ({min_year}-{max_year})'
    if municipio_filter_list and len(municipio_filter_list) == 1:
        chart_title += f" en {municipio_filter_list[0]}"
    elif municipio_filter_list and len(municipio_filter_list) > 1:
        chart_title += f" en {', '.join(municipio_filter_list)}"

    fig = px.bar(
        aggregated_data,
        x='Bien jurídico afectado',
        y='Total de Incidentes',
        title=chart_title,
        labels={'Bien jurídico afectado': 'Bien Jurídico Afectado', 'Total de Incidentes': 'Cantidad de Incidentes'},
        hover_data=['Total de Incidentes']
    )

    fig.update_layout(
        xaxis_title="Bien Jurídico Afectado",
        yaxis_title="Cantidad de Incidentes",
        xaxis={'categoryorder':'total descending', 'tickangle': 0},
        height=800,
        showlegend=False
    )

    fig.update_traces(
        marker_color='darkorange',
        texttemplate='%{y}',
        textposition='outside'
    )
    fig.update_xaxes(automargin=True)
    return fig

# Helper function for creating incidents trend chart
def create_incidents_trend_chart(
    df: pd.DataFrame,
    min_year: int,
    max_year: int,
    municipios_filter_list: list = None
):
    filtered_df = df[(df['Año'] >= min_year) & (df['Año'] <= max_year)].copy()

    if municipios_filter_list:
        normalized_municipalities = [normalize_string_for_match(m) for m in municipios_filter_list]
        filtered_df['Municipio_x_cleaned'] = filtered_df['Municipio_x'].apply(normalize_string_for_match)
        filtered_df = filtered_df[filtered_df['Municipio_x_cleaned'].isin(normalized_municipalities)]
        filtered_df = filtered_df.drop(columns=['Municipio_x_cleaned'])

    if filtered_df.empty:
        st.warning(f"No hay datos para crear una tendencia anual para los años {min_year}-{max_year} con los municipios seleccionados.")
        return None

    # Handle case where only one year is selected for trend chart
    if min_year == max_year:
        st.info(f"Solo se ha seleccionado un año ({min_year}). No hay suficientes datos para crear una tendencia anual.")
        # You can return an empty plot or a message
        return px.scatter(title=f"Datos insuficientes para crear una tendencia anual ({min_year})")


    # Aggregate incidents by Year and by Municipality (if multiple selected) or as a total trend
    if municipios_filter_list and len(municipios_filter_list) > 1:
        aggregated_data = filtered_df.groupby(['Año', 'Municipio_x'])['Total de Incidentes'].sum().reset_index()
        color_col = 'Municipio_x'
        title_suffix = f" en {', '.join(municipios_filter_list)}"
        fig = px.line(
            aggregated_data,
            x='Año',
            y='Total de Incidentes',
            color=color_col,
            title=f'Tendencia de Incidentes ({min_year}-{max_year}){title_suffix}',
            labels={'Año': 'Año', 'Total de Incidentes': 'Cantidad de Incidentes'},
            markers=True,
            color_discrete_sequence=px.colors.sequential.Oranges_r
        )
    else:
        aggregated_data = filtered_df.groupby('Año')['Total de Incidentes'].sum().reset_index()
        if municipios_filter_list:
            title_suffix = f" en {municipios_filter_list[0]}"
        else:
            title_suffix = " en todos los municipios"

        fig = px.line(
            aggregated_data,
            x='Año',
            y='Total de Incidentes',
            title=f'Tendencia de Incidentes ({min_year}-{max_year}){title_suffix}',
            labels={'Año': 'Año', 'Total de Incidentes': 'Cantidad de Incidentes'},
            markers=True
        )
        fig.update_traces(line_color='darkorange')

    fig.update_layout(
        xaxis_title="Año",
        yaxis_title="Cantidad de Incidentes",
        hovermode="x unified"
    )
    fig.update_xaxes(tickmode='linear', dtick=1) # Ensure all years are shown as ticks
    return fig

# --- 2. Streamlit Application Structure ---

st.set_page_config(layout="wide", page_title="Dashboard Delitos en Yucatán")

st.title("DASHBOARD DELITOS EN YUCATÁN (2015 A 2025)")

# Get unique years and municipalities for filters
all_years = sorted(delitos_final['Año'].unique().tolist())
all_municipalities = sorted(delitos_final['Municipio_x'].unique().tolist())

# Sidebar for user inputs
st.sidebar.header("Filtros de Datos")

# Year Filtering
st.sidebar.subheader("Filtrar por Año")
year_filter_type = st.sidebar.radio(
    "Seleccione el tipo de filtro de año:",
    ('Todos los años', 'Año específico', 'Rango de años'),
    key='year_filter_type'
)

min_selected_year = min(all_years)
max_selected_year = max(all_years)

if year_filter_type == 'Año específico':
    selected_year = st.sidebar.selectbox(
        "Seleccione un año:",
        options=all_years,
        index=len(all_years) - 1, # Default to latest year
        key='single_year_select'
    )
    min_selected_year = selected_year
    max_selected_year = selected_year
elif year_filter_type == 'Rango de años':
    selected_year_range = st.sidebar.slider(
        "Seleccione un rango de años:",
        min_value=min(all_years),
        max_value=max(all_years),
        value=(min(all_years), max(all_years)),
        key='year_range_slider'
    )
    min_selected_year = selected_year_range[0]
    max_selected_year = selected_year_range[1]
# If 'Todos los años', min_selected_year and max_selected_year remain default to all years

# Municipality Filtering
st.sidebar.subheader("Filtrar por Municipio")
municipio_filter_type = st.sidebar.radio(
    "Seleccione el tipo de filtro de municipio:",
    ('Todos los municipios', 'Seleccionar municipios'),
    key='municipio_filter_type'
)

selected_municipalities = []
if municipio_filter_type == 'Seleccionar municipios':
    selected_municipalities = st.sidebar.multiselect(
        "Seleccione uno o varios municipios:",
        options=all_municipalities,
        default=[],
        key='multi_municipio_select'
    )

# --- 3. Filter Data Based on User Selections ---

filtered_df = delitos_final[
    (delitos_final['Año'] >= min_selected_year) & (delitos_final['Año'] <= max_selected_year)
].copy()

if selected_municipalities:
    normalized_selected_mun = [normalize_string_for_match(m) for m in selected_municipalities]
    filtered_df['Municipio_x_cleaned'] = filtered_df['Municipio_x'].apply(normalize_string_for_match)
    filtered_df = filtered_df[filtered_df['Municipio_x_cleaned'].isin(normalized_selected_mun)]
    filtered_df = filtered_df.drop(columns=['Municipio_x_cleaned'])

if filtered_df.empty:
    st.warning("No hay datos disponibles para los filtros seleccionados.")
else:
    st.write(f"Datos filtrados para el rango de años **{min_selected_year}-{max_selected_year}**")
    if selected_municipalities:
        st.write(f"Municipios seleccionados: **{', '.join(selected_municipalities)}**")
    else:
        st.write("Municipios seleccionados: **Todos**")

    # --- 4. Map Visualization Integration ---
    st.subheader("Mapa de Incidentes por Municipio")

    # Aggregate data for map
    df_map_agg = filtered_df.groupby(['Municipio_x', 'Latitud', 'Longitud'])['Total de Incidentes'].sum().reset_index()
    df_map_agg = df_map_agg.rename(columns={'Municipio_x': 'Name', 'Latitud': 'latitude', 'Longitud': 'longitude'})

    # Prepare data for PyDeck GeoJsonLayer
    if not df_map_agg.empty:
        min_incidents = df_map_agg['Total de Incidentes'].min()
        max_incidents = df_map_agg['Total de Incidentes'].max()
        log_min_val = np.log1p(min_incidents)
        log_max_val = np.log1p(max_incidents)

        df_map_agg["color_rgba"] = df_map_agg["Total de Incidentes"].apply(
            lambda d: get_log_color(d, log_min_val, log_max_val)
        )

        incident_color_map_for_geojson = df_map_agg.copy()
        incident_color_map_for_geojson["Name_cleaned"] = incident_color_map_for_geojson["Name"].apply(normalize_string_for_match)
        incident_color_map_for_geojson = incident_color_map_for_geojson.set_index("Name_cleaned")[["Total de Incidentes", "color_rgba"]]

        geojson_with_data_for_pydeck = json.loads(json.dumps(Coordenadas_Json))

        for feature in geojson_with_data_for_pydeck["features"]:
            name_clean = normalize_string_for_match(feature["properties"]["NOMGEO"])

            if name_clean in incident_color_map_for_geojson.index:
                feature["properties"]["Total_Incidentes"] = float(
                    incident_color_map_for_geojson.loc[name_clean, "Total de Incidentes"]
                )
                feature["properties"]["color_rgba"] = incident_color_map_for_geojson.loc[name_clean, "color_rgba"]
            else:
                feature["properties"]["Total_Incidentes"] = 0.0
                feature["properties"]["color_rgba"] = [255, 255, 255, 180] # White fill for unmatched/zero incidents

        # Center of map
        center_lat = df_map_agg['latitude'].mean() if not df_map_agg.empty else 20.8
        center_lon = df_map_agg['longitude'].mean() if not df_map_agg.empty else -89.0

        view_state = pdk.ViewState(
            latitude=center_lat,
            longitude=center_lon,
            zoom=7.2,
            pitch=45
        )

        geojson_layer = pdk.Layer(
            "GeoJsonLayer",
            geojson_with_data_for_pydeck,
            filled=True,
            stroked=True,
            get_fill_color="properties.color_rgba",
            get_line_color=[0, 0, 0, 200],
            get_line_width=50,
            pickable=True,
            auto_highlight=True
            # Tooltip is now handled at the Deck level
        )

        st.pydeck_chart(pdk.Deck(
            map_style="mapbox://styles/mapbox/light-v9",
            initial_view_state=view_state,
            layers=[geojson_layer],
            tooltip={"html": "<b>Municipio:</b> {properties.NOMGEO}<br/><b>Total de Incidentes:</b> {properties.Total_Incidentes}"}
        ))
    else:
        st.info("No hay datos para mostrar en el mapa con los filtros seleccionados.")

    # --- 5. Bar Chart Visualization Integration ---
    st.subheader("Total de Incidentes por Bien Jurídico Afectado")
    bar_chart_fig = create_incidents_bar_chart_v2(
        df=delitos_final, # Use original delitos_final and pass filters to function
        min_year=min_selected_year,
        max_year=max_selected_year,
        municipio_filter_list=selected_municipalities
    )
    st.plotly_chart(bar_chart_fig, use_container_width=True)

    # --- 6. Trend Chart Visualization Integration ---
    st.subheader("Tendencia Anual de Incidentes")
    trend_chart_fig = create_incidents_trend_chart(
        df=delitos_final, # Use original delitos_final and pass filters to function
        min_year=min_selected_year,
        max_year=max_selected_year,
        municipios_filter_list=selected_municipalities
    )
    if trend_chart_fig:
        st.plotly_chart(trend_chart_fig, use_container_width=True)
    else:
        st.info("No se puede generar la gráfica de tendencia con los filtros seleccionados.")


    # --- 7. Display Filtered Data Table ---
    st.subheader("Datos Filtrados")
    st.dataframe(filtered_df.drop(columns=['Latitud', 'Longitud'])) # Exclude coords from table for cleaner view
