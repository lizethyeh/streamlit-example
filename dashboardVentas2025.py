import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Product Sales and Profit Analysis')

# Leer archivo Excel
excel_file_path = 'Order Central Limpio ENTREGABLE.xlsx'
df_order_central = pd.read_excel(excel_file_path)

# --- GRÁFICA DE VENTAS ---
# Calcular ventas totales por producto
total_sales_per_product = df_order_central.groupby('Product Name')['Sales'].sum()
sorted_products_by_sales = total_sales_per_product.sort_values(ascending=False)
top_5_products = sorted_products_by_sales.head(5)

# Insertar salto de línea cada 20 caracteres para que aparezcan en dos líneas
wrapped_sales_product_names = [name.replace(" ", "<br>", 1) if len(name) > 20 else name for name in top_5_products.index]

# Crear gráfica de barras de ventas
fig_sales = px.bar(
    x=wrapped_sales_product_names,
    y=top_5_products.values,
    title='Top 5 Selling Products by Sales',
    labels={'x': 'Product Name', 'y': 'Total Sales'}
)
fig_sales.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_sales)

# --- GRÁFICA DE UTILIDADES ---
# Calcular utilidad total por producto
total_profit_per_product = df_order_central.groupby('Product Name')['Profit'].sum()
sorted_products_by_profit = total_profit_per_product.sort_values(ascending=False)
top_5_products_by_profit = sorted_products_by_profit.head(5)

# Insertar salto de línea cada 20 caracteres
wrapped_profit_product_names = [name.replace(" ", "<br>", 1) if len(name) > 20 else name for name in top_5_products_by_profit.index]

# Crear gráfica de barras de utilidades
fig_profit = px.bar(
    x=wrapped_profit_product_names,
    y=top_5_products_by_profit.values,
    title='Top 5 Most Profitable Products',
    labels={'x': 'Product Name', 'y': 'Total Profit'}
)
fig_profit.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_profit)
