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

# Create sales bar chart
fig_sales = px.bar(top_5_products,
                   x=top_5_products.index,
                   y=top_5_products.values,
                   title='Top 5 Selling Products by Sales',
                   labels={'x': 'Product Name', 'y': 'Total Sales'})
fig_sales.update_layout(xaxis = dict(tickangle = -45,
                                tickfont = dict(size=10),
                                automargin=True),
                  xaxis_tickformat = '<br>'.join(['%s' % i for i in top_5_products.index.str.wrap(20)])) # Apply wrapping to sales chart

st.plotly_chart(fig_sales)

# Calculate total profit per product
total_profit_per_product = df_order_central.groupby('Product Name')['Profit'].sum()
sorted_products_by_profit = total_profit_per_product.sort_values(ascending=False)
top_5_products_by_profit = sorted_products_by_profit.head(5)

# Create profit bar chart
fig_profit = px.bar(top_5_products_by_profit,
                    x=top_5_products_by_5_products_by_profit.index,
                    y=top_5_products_by_profit.values,
                    title='Top 5 Most Profitable Products',
                    labels={'x': 'Product Name', 'y': 'Total Profit'})

fig_profit.update_layout(xaxis = dict(tickangle = -45,
                                tickfont = dict(size=10),
                                automargin=True),
                  xaxis_tickformat = '<br>'.join(['%s' % i for i in top_5_products_by_profit.index.str.wrap(20)])) # Apply wrapping to profit chart

st.plotly_chart(fig_profit)
