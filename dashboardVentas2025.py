import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap

st.title('Product Sales and Profit Analysis by Region and State')

# Leer archivo Excel
excel_file_path = 'Order Central Limpio ENTREGABLE.xlsx'
df_order_central = pd.read_excel(excel_file_path)

# Convert date columns to datetime
df_order_central['Order Date'] = pd.to_datetime(df_order_central['Order Date'], errors='coerce')
df_order_central['Ship Date'] = pd.to_datetime(df_order_central['Ship Date'], errors='coerce')


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

# Filter data based on selected state
if selected_state == 'Todos':
    filtered_df = filtered_df_region
else:
    filtered_df = filtered_df_region[filtered_df_region['State'] == selected_state]

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
