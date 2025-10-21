import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap
import pydeck as pdk

st.title('Product Sales and Profit Analysis by Region and State')

# Leer archivo Excel
excel_file_path = 'Order Central Limpio ENTREGABLE.xlsx'
df_order_central = pd.read_excel(excel_file_path)

# Convert date columns to datetime
# Extract numeric part from the string and convert to float
df_order_central['Order Date'] = df_order_central['Order Date'].astype(str).str.extract('(\d+)').astype(float)
df_order_central['Ship Date'] = df_order_central['Ship Date'].astype(str).str.extract('(\d+)').astype(float)

# Convert the numeric part to Timedelta
df_order_central['Order Date'] = pd.to_timedelta(df_order_central['Order Date'], unit='D', errors='coerce')
df_order_central['Ship Date'] = pd.to_timedelta(df_order_central['Ship Date'], unit='D', errors='coerce')

# Add the Timedelta to the Excel epoch
excel_epoch = pd.Timestamp('1900-01-01')
df_order_central['Order Date'] = excel_epoch + df_order_central['Order Date']
df_order_central['Ship Date'] = excel_epoch + df_order_central['Ship Date']


# Sidebar for filters
st.sidebar.header('Filter by Region and State')

# Region filter
regions = ['Todas'] + list(df_order_central['Region'].unique())
selected_region = st.sidebar.selectbox('Select a Region', regions)

# Filter data based on selected region
if selected_region == 'Todas':
    filtered_df_region = df_order_central
else:
    filtered_df_region = df_order_central[df_order_central['Region'] == selected_region]

# State filter
states = ['Todos'] + list(filtered_df_region['State'].unique())
selected_state = st.sidebar.selectbox('Select a State', states)


# Date range filter
st.sidebar.header('Filter by Order Date Range')
min_date = df_order_central['Order Date'].min().date()
max_date = df_order_central['Order Date'].max().date()
start_date = st.sidebar.date_input('Start Date', value=min_date, min_value=min_date, max_value=max_date)
end_date = st.sidebar.date_input('End Date', value=max_date, min_value=min_date, max_value=max_date)


# Filter data based on selected state
if selected_state == 'Todos':
    filtered_df = filtered_df_region
else:
    filtered_df = filtered_df_region[filtered_df_region['State'] == selected_state]

# Filter data based on selected date range
start_date = pd.Timestamp(start_date)
end_date = pd.Timestamp(end_date)
filtered_df = filtered_df[(filtered_df['Order Date'] >= start_date) & (filtered_df['Order Date'] <= end_date)]


# Checkbox to show/hide DataFrame
show_dataframe = st.sidebar.checkbox('Show Filtered Data')

# Display filtered DataFrame if checkbox is checked
if show_dataframe:
    st.subheader('Filtered Data')
    st.dataframe(filtered_df)


# --- GRÁFICA DE VENTAS ---
# Calcular ventas totales por producto para la región/estado seleccionada
total_sales_per_product = filtered_df.groupby('Product Name')['Sales'].sum()
sorted_products_by_sales = total_sales_per_product.sort_values(ascending=False)
top_5_products = sorted_products_by_sales.head(5)

# Dividir los nombres cada 15 caracteres en 2-3 líneas
wrapped_sales_product_names = ["<br>".join(textwrap.wrap(name, 15)) for name in top_5_products.index]

# Crear gráfica de barras de ventas
fig_sales = px.bar(
    x=wrapped_sales_product_names,
    y=top_5_products.values,
    title=f'Top 5 Selling Products by Sales in {selected_state if selected_state != "Todos" else selected_region}',
    labels={'x': 'Product Name', 'y': 'Total Sales'}
)

# Ajustar para que los nombres se vean horizontales y claros
fig_sales.update_layout(
    xaxis_tickangle=0,
    margin=dict(b=150),
    xaxis_tickfont=dict(size=11)
)

st.plotly_chart(fig_sales, use_container_width=True)

# --- GRÁFICA DE UTILIDADES ---
# Calcular utilidad total por producto para la región/estado seleccionada
total_profit_per_product = filtered_df.groupby('Product Name')['Profit'].sum()
sorted_products_by_profit = total_profit_per_product.sort_values(ascending=False)
top_5_products_by_profit = sorted_products_by_profit.head(5)

# Dividir los nombres cada 15 caracteres
wrapped_profit_product_names = ["<br>".join(textwrap.wrap(name, 15)) for name in top_5_products_by_profit.index]

# Crear gráfica de barras de utilidades
fig_profit = px.bar(
    x=wrapped_profit_product_names,
    y=top_5_products_by_profit.values,
    title=f'Top 5 Most Profitable Products in {selected_state if selected_state != "Todos" else selected_region}',
    labels={'x': 'Product Name', 'y': 'Total Profit'}
)

# Ajustar estilo igual
fig_profit.update_layout(
    xaxis_tickangle=0,
    margin=dict(b=150),
    xaxis_tickfont=dict(size=11)
)

st.plotly_chart(fig_profit, use_container_width=True)

# --- GRÁFICA DE VENTAS POR ESTADO (PYDECK) ---
st.subheader('Total Sales by State')

# Calculate total sales per state for the filtered data
total_sales_by_state = filtered_df.groupby(['State', 'City'])['Sales'].sum().reset_index()

# You would typically need geographical coordinates (latitude and longitude) for each state/city to plot on a map.
# Since the data only has State and City names, we'll need to add coordinates.
# For demonstration purposes, let's assume we have a separate DataFrame with coordinates for each city.
# In a real application, you would merge this with your sales data or use a geocoding service.

# Example: Create a dummy DataFrame with coordinates (replace with actual data)
# This is a placeholder and won't produce an accurate map without real coordinates.
# You would need a dataset mapping states and cities to latitude and longitude.
# For this example, I'll just use a single coordinate for each state's first city for visualization purposes.
# A better approach would be to use a geocoding library or a pre-existing dataset with city/state coordinates.

# Let's try to get some approximate coordinates for the cities in the filtered data
# using a simple approach (this is not ideal for accurate mapping)
# In a real scenario, you would use a proper geocoding method.
# For now, let's use a dummy approach to get the PyDeck chart structure working.

# This part needs actual coordinate data for cities/states.
# Since we don't have it, I'll create a placeholder structure that you would replace.

# Example of how you might prepare data if you had coordinates:
# sales_with_coords = total_sales_by_state.merge(coordinates_df, on='City', how='left')
# sales_with_coords = sales_with_coords.dropna(subset=['latitude', 'longitude']) # Drop rows with missing coords

# For demonstration, let's create a simple layer with dummy data structure
# Replace this with your actual data preparation for PyDeck
if not total_sales_by_state.empty:
    # Assuming you have latitude and longitude columns in total_sales_by_state after merging with coordinates
    # For this example, let's just use a placeholder structure
    # You would replace this with your actual data and coordinate columns
    total_sales_by_state['latitude'] = 0.0 # Replace with actual latitude column
    total_sales_by_state['longitude'] = 0.0 # Replace with actual longitude column

    # Create a ColumnLayer for sales by state
    layer = pdk.Layer(
        'ColumnLayer',
        data=total_sales_by_state,
        get_position='[longitude, latitude]', # Replace with actual coordinate columns
        get_elevation='Sales',
        elevation_scale=10,
        radius=10000,
        get_color='[200, 30, 0, 160]',
        pickable=True,
        extruded=True,
    )

    # Set the view state
    view_state = pdk.ViewState(
        latitude=filtered_df['latitude'].mean() if 'latitude' in filtered_df.columns and not filtered_df['latitude'].empty else 40.7, # Replace with a more appropriate center
        longitude=filtered_df['longitude'].mean() if 'longitude' in filtered_df.columns and not filtered_df['longitude'].empty else -74.0, # Replace with a more appropriate center
        zoom=3,
        pitch=50,
    )

    # Create the PyDeck chart
    r = pdk.Deck(
        layers=[layer],
        initial_view_state=view_state,
        tooltip={"text": "State: {State}\nSales: {Sales}"} # Update tooltip based on your data columns
    )

    # Display the PyDeck chart
    st.pydeck_chart(r)
else:
    st.write("No sales data available for the selected filters to display on the map.")
