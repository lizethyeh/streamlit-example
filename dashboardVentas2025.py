import streamlit as st
import pandas as pd
import plotly.express as px
import textwrap

st.title('Product Sales and Profit Analysis')

# Leer archivo Excel
excel_file_path = 'Order Central Limpio ENTREGABLE.xlsx'
df_order_central = pd.read_excel(excel_file_path)

# --- GRÁFICA DE VENTAS ---
# Calcular ventas totales por producto
total_sales_per_product = df_order_central.groupby('Product Name')['Sales'].sum()
sorted_products_by_sales = total_sales_per_product.sort_values(ascending=False)
top_5_products = sorted_products_by_sales.head(5)

# Dividir los nombres cada 15 caracteres en 2-3 líneas
wrapped_sales_product_names = ["<br>".join(textwrap.wrap(name, 15)) for name in top_5_products.index]

# Crear gráfica de barras de ventas
fig_sales = px.bar(
    x=wrapped_sales_product_names,
    y=top_5_products.values,
    title='Top 5 Selling Products by Sales',
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
# Calcular utilidad total por producto
total_profit_per_product = df_order_central.groupby('Product Name')['Profit'].sum()
sorted_products_by_profit = total_profit_per_product.sort_values(ascending=False)
top_5_products_by_profit = sorted_products_by_profit.head(5)

# Dividir los nombres cada 15 caracteres
wrapped_profit_product_names = ["<br>".join(textwrap.wrap(name, 15)) for name in top_5_products_by_profit.index]

# Crear gráfica de barras de utilidades
fig_profit = px.bar(
    x=wrapped_profit_product_names,
    y=top_5_products_by_profit.values,
    title='Top 5 Most Profitable Products',
    labels={'x': 'Product Name', 'y': 'Total Profit'}
)

# Ajustar estilo igual
fig_profit.update_layout(
    xaxis_tickangle=0,
    margin=dict(b=150),
    xaxis_tickfont=dict(size=11)
)

st.plotly_chart(fig_profit, use_container_width=True)
