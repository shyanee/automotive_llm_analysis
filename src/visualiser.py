import os
import plotly.express as px
import pandas as pd
import plotly.io as pio

class Visualizer:
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self.output_dir = os.path.join('output', 'plots')
        os.makedirs(self.output_dir, exist_ok=True) 

    def generate_plots(self) -> dict:
        """
        Generates interactive Plotly figures and returns them as HTML strings
        to be embedded in the report, focusing on regional demand, pricing,
        and key sales drivers.
        """
        plots = {}

        # 1. Global Sales Trend over Time (Original, but useful for overall performance)
        # Goal: Identify and describe sales performance trend over time
        regional_yearly = self.df.groupby(['year', 'region'])['sales_volume'].sum().reset_index()

        # Calculate Global Sales Trend
        global_yearly = self.df.groupby('year')['sales_volume'].sum().reset_index()
        # Assign a unique identifier for the global line
        global_yearly['region'] = 'Global'
        global_yearly = global_yearly.rename(columns={'sales_volume': 'sales_volume'})

        # Combine the two datasets
        combined_yearly = pd.concat([regional_yearly, global_yearly], ignore_index=True)

        # Define custom order and style for the plot
        # Ensure 'Global' appears last in the legend (and potentially has a distinct color)
        region_order = combined_yearly['region'].unique().tolist()
        if 'Global' in region_order:
            region_order.remove('Global')
            region_order.append('Global')

        # Define a color map to make the 'Global' line stand out (e.g., black)
        num_regions = len(region_order) - 1
        color_sequence = px.colors.qualitative.Plotly[:num_regions] + ['#000000'] # Default colors + Black for Global
        color_map = dict(zip(region_order, color_sequence))

        fig1 = px.line(
            combined_yearly, 
            x='year', 
            y='sales_volume', 
            color='region', 
            title='Sales Trends: Regional Performance Overlaid with Global Trend (Units)', 
            markers=True,
            labels={'sales_volume': 'Sales Volume'},
            category_orders={'region': region_order},
            color_discrete_map=color_map
        )

        # Customize the 'Global' line to make it more distinct (e.g., thicker and dashed)
        for trace in fig1.data:
            if trace.name == 'Global':
                # Find the trace for the 'Global' trend
                trace.update(line=dict(width=3, dash='dash'))

        plots['combined_trend_plot'] = pio.to_html(fig1, full_html=False, include_plotlyjs='cdn')
        self._write_html(fig1, 'combined_trend_plot')

        # 2. Top Models Sales Breakdown (New: Model Performance)
        # Goal: Highlight top-performing and underperforming models
        # 1. Identify Top 10 Models
        top_10_models = self.df.groupby('model')['sales_volume'].sum().nlargest(10).index.tolist()
        df_top_10 = self.df[self.df['model'].isin(top_10_models)]
        model_fuel_sales_yearly = df_top_10.groupby(['year', 'model', 'fuel_type'])['sales_volume'].sum().reset_index()
        model_order = self.df.groupby('model')['sales_volume'].sum().nlargest(10).index.tolist()
        fig2 = px.bar(
            model_fuel_sales_yearly, 
            x='model', 
            y='sales_volume', 
            color='fuel_type',
            facet_col='year',
            title='Top 10 Models: Sales Volume Composition by Fuel Type', 
            labels={'sales_volume': 'Total Sales Volume (Units)', 'fuel_type': 'Fuel Type'},
            category_orders={"model": model_order}, # Apply the sales-based order
            hover_data=['fuel_type', 'sales_volume']
        )
        fig2.update_layout(barmode='stack', xaxis={'categoryorder':'array', 'categoryarray':model_order})
        plots['top_models_plot'] = pio.to_html(fig2, full_html=False, include_plotlyjs=False)
        self._write_html(fig2, 'top_models_plot')
        
        # 3. Price Elasticity / Sales Driver (Scatter Plot, Modified for Clarity)
        # Goal: Explore key drivers of sales (price, market segment)
        # Use mileage bin as an interesting categorical variable
        group_cols = ['transmission', 'fuel_type'] # model
        df_agg = self.df.groupby(group_cols).agg(
            avg_price_usd=('price_usd', 'mean'),  # X-axis: Average price
            total_sales_volume=('sales_volume', 'sum'),  # Y-axis: Total sales (volume)
            avg_engine_size=('engine_size_l', 'mean')  # Size: Average engine size
        ).reset_index().dropna()
        fig3 = px.scatter(
            df_agg, 
            x='avg_price_usd', 
            y='total_sales_volume', 
            color='transmission',            # Color by transmission
            facet_col='fuel_type',           # Split into columns by fuel type
            size='total_sales_volume',       # Size now reflects sales volume (or use avg_engine_size)
            size_max=45,                     # Adjust max size slightly for clarity
            hover_data=['avg_engine_size'], # Show model and engine size on hover # model
            title='Price vs. Sales Volume: Model Market Position (Aggregated by Fuel/Trans)',
            labels={
                'avg_price_usd': 'Average Price (USD)', 
                'total_sales_volume': 'Total Sales Volume (Units)',
                'transmission': 'Transmission',
                'fuel_type': 'Fuel Type'
            }
        )
        fig3.update_layout(height=450, showlegend=True)
        fig3.for_each_annotation(lambda a: a.update(text=a.text.replace('fuel_type=', '')))
        plots['price_elasticity_plot'] = pio.to_html(fig3, full_html=False, include_plotlyjs=False)
        self._write_html(fig3, 'price_elasticity_plot')

        # 4. Engine Size vs. Price by Fuel Type (New: Creative Insight - Premiumization/Market Segment)
        # Goal: Include 1-2 additional insights (Engine Size/Fuel as proxy for performance/premium segment)
        df_clean_eng = self.df.dropna(subset=['engine_size_l', 'price_usd', 'fuel_type'])
        fig4 = px.box(
            df_clean_eng, x='engine_size', y='price_usd', 
            color='fuel_type', 
            title='Price Distribution by Binned Engine Size and Fuel Type',
            labels={'engine_size': 'Engine Size (L, Binned)', 'price_usd': 'Price (USD)'},
            category_orders={'engine_size': sorted(df_clean_eng['engine_size'].unique().tolist())}
        )
        plots['engine_price_box'] = pio.to_html(fig4, full_html=False, include_plotlyjs=False)
        self._write_html(fig4, 'engine_price_box')

        return plots
    
    def _write_html(self, fig, filename: str):
        """Helper function to write Plotly figure to HTML file."""
        pio.write_html(fig, os.path.join(self.output_dir, f'{filename}.html'), include_plotlyjs='cdn')