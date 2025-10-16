import streamlit as st
import pandas as pd
import plotly.express as px

st.title('Product Sales and Profit Analysis')

# Read the data
excel_file_path = 'Order Central Limpio ENTREGABLE.xlsx'
df_order_central = pd.read_excel(excel_file_path)

# Calculate total sales per product
total_sales_per_product = df_order_central.groupby('Product Name')['Sales'].sum()
sorted_products_by_sales = total_sales_per_product.sort_values(ascending=False)
top_5_products = sorted_products_by_sales.head(5)

# Manually wrap product names for sales chart
wrapped_sales_product_names = top_5_products.index.str.wrap(20)

# Create sales bar chart
fig_sales = px.bar(top_5_products,
                   x=wrapped_sales_product_names,
                   y=top_5_products.values,
                   title='Top 5 Selling Products by Sales',
                   labels={'x': 'Product Name', 'y': 'Total Sales'})
fig_sales.update_layout(xaxis_tickangle=-45)

st.plotly_chart(fig_sales)

# Calculate total profit per product
total_profit_per_product = df_order_central.groupby('Product Name')['Profit'].sum()
sorted_products_by_profit = total_profit_per_product.sort_values(ascending=False)
top_5_products_by_profit = sorted_products_by_profit.head(5)

# Manually wrap product names for profit chart
wrapped_profit_product_names = top_5_products_by_profit.index.str.wrap(20)


# Create profit bar chart
fig_profit = px.bar(top_5_products_by_profit,
                    x=wrapped_profit_product_names, # Use wrapped names here
                    y=top_5_products_by_profit.values,
                    title='Top 5 Most Profitable Products',
                    labels={'x': 'Product Name', 'y': 'Total Profit'})

fig_profit.update_layout(xaxis_tickangle=-45) # No need for xaxis_tickformat with manual wrapping

st.plotly_chart(fig_profit)
