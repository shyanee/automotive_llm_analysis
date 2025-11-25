import pandas as pd
import numpy as np
from typing import Tuple, Dict, List, Any
from src.utils import logger_util

class DataPreprocessor:
    def __init__(self, filepath: str, expected_columns: list):
        self.logger = logger_util.setup_logger(__name__)
        self.filepath = filepath
        self.expected_cols = expected_columns

    def get_clean_df(self) -> pd.DataFrame:
        """
        Phase 1: Load and Clean Data.
        Returns a DataFrame ready for plotting.
        """
        self.logger.info(f"Loading data from {self.filepath}")
        try:
            df = self._read_file(self.filepath)
            self.logger.info(f"Loaded {len(df)} rows, {len(df.columns)} columns")
            
            df.columns = [c.lower().replace(' ', '_') for c in df.columns]
            
            # Validation: Check if all config columns exist
            missing = [col for col in self.expected_cols if col not in df.columns]
            if missing:
                raise ValueError(f"Input CSV is missing columns defined in config: {missing}")

            # Data Type Enforcement
            numeric_cols = df.select_dtypes(include='number').columns.tolist()
            
            grouping_cols = ['model', 'year', 'engine_size_l', 'mileage_km', 'transmission']
            grouping_cols = [col for col in grouping_cols if col in df.columns]
            
            for col in numeric_cols:
                df[col] = pd.to_numeric(df[col], errors='coerce')
            
            if grouping_cols:
                # imputation_dict = df.groupby(grouping_cols)[numeric_cols].median()
                for col in numeric_cols:
                    df[col] = df[col].fillna(
                        df.groupby(grouping_cols)[col].transform('median')
                    )
            
            for col in numeric_cols:
                df[col] = df[col].fillna(df[col].median()).fillna(0)
            
            # Process engine type
            df['engine_size'] = df['engine_size_l'].astype(int)
            
            # Bin mileage
            bins = [0, 50000, 100000, 150000, 200000]
            labels = ['0-50k', '50k-100k', '100k-150k', '150k-200k']
            df['mileage_bin'] = pd.cut(df['mileage_km'], bins=bins, labels=labels)

            if 'year' in df.columns:
                df['year'] = df['year'].astype(int)
        
            # print(df.head(5))
            return df
        
        except Exception as e:
            self.logger.error(f"Data loading failed: {e}", exc_info=True)
            raise

    def _read_file(self, filepath: str) -> pd.DataFrame:
        file_extension = filepath.rsplit('.', 1)[-1].lower()
        try:
            if file_extension == 'csv':
                df = pd.read_csv(self.filepath)
            elif file_extension in ['xlsx', 'xls']:
                df = pd.read_excel(self.filepath)
            return df
        except Exception as e:
            raise RuntimeError(f"Unable to read file: {e}")

    def extract_llm_context(self, df: pd.DataFrame) -> str:
        """
        Phase 2: Extract comprehensive data context for the LLM prompt.
        Convert raw data into detailed narrative statistics for LLM
        """
        
        # Helper functions (copied from original code for self-containment)
        def _top_n_performers(df: pd.DataFrame, col: str, metric: str, n: int = 3):
            return df.groupby(col)[metric].sum().nlargest(n)
            
        def _get_column_stats(df: pd.DataFrame, column_name: str, groupby_cols: List[str] = None) -> Dict[str, Any]:
            """
            Calculates descriptive statistics for a column, optionally grouped by other columns.
            Returns a dictionary of statistics.
            """
            if column_name not in df.columns:
                return {'error': f"Column '{column_name}' does not exist in the DataFrame."}
            
            if not pd.api.types.is_numeric_dtype(df[column_name]):
                return {'error': f"Column '{column_name}' is not numeric. Cannot calculate descriptive stats."}

            if groupby_cols and all(col in df.columns for col in groupby_cols):
                # Groupby and apply aggregation
                grouped = df.groupby(groupby_cols)[column_name]
                stats = grouped.agg(['mean', 'median', 'std', 'min', 'max', 'count']).to_dict('index')
                return stats
            else:
                # Calculate stats on the entire column
                stats = {
                    'mean': df[column_name].mean(),
                    'median': df[column_name].median(),
                    'std': df[column_name].std(),
                    'min': df[column_name].min(),
                    'max': df[column_name].max(),
                    '25%': df[column_name].quantile(0.25),
                    '50%': df[column_name].quantile(0.5),
                    '75%': df[column_name].quantile(0.75),
                    'count': df[column_name].count(),
                    'missing': df[column_name].isnull().sum()
                }
                # Format the numbers for better readability
                stats = {k: (f"{v:,.2f}" if isinstance(v, (float, int)) else v) for k, v in stats.items()}
                return stats

        def _get_time_series_trends(df: pd.DataFrame, group_col: str, n_top: int = 3) -> Dict[str, Dict[str, Any]]:
            """
            Calculates year-over-year sales volume and price trends for the top N items in a category.
            """
            # 1. Identify top N performers in the category across all years
            top_items = df.groupby(group_col)['sales_volume'].sum().nlargest(n_top).index.tolist()
            
            results = {}
            for item in top_items:
                item_df = df[df[group_col] == item]
                
                # Group by year for the selected item
                yearly_data = item_df.groupby('year').agg(
                    sales_volume=('sales_volume', 'sum'),
                    avg_price=('price_usd', 'mean')
                ).sort_index()
                
                if yearly_data.empty:
                    continue

                yearly_data_str = " | ".join([
                    f"Y{year}: S{sales:,.0f}/P${price:,.0f}"
                    for year, (sales, price) in yearly_data.iterrows()
                ])
                
                # Calculate the growth rate for the whole period for the item
                growth_rate = 0
                if len(yearly_data) > 1 and yearly_data['sales_volume'].iloc[0] > 0:
                     growth_rate = (yearly_data['sales_volume'].iloc[-1] / yearly_data['sales_volume'].iloc[0]) - 1
                
                results[item] = {
                    'trend_summary': f"Growth: {growth_rate:+.2%} | Start_Year_Price: ${yearly_data['avg_price'].iloc[0]:,.0f} | End_Year_Price: ${yearly_data['avg_price'].iloc[-1]:,.0f}",
                    'yearly_breakdown': yearly_data_str
                }
            return results

        # ----------------------------------------------------
        # 1. Overall Metrics & Trend Analysis (No Change)
        # ----------------------------------------------------
        total_revenue = (df['sales_volume'] * df['price_usd']).sum()
        total_sales = df['sales_volume'].sum()
        
        yearly_sales = df.groupby('year')['sales_volume'].sum().sort_index()
        yearly_sales_str = ", ".join([f"{y}: {s:,}" for y, s in yearly_sales.items()])
        
        growth_trend = "stable"
        cagr = 0
        if len(yearly_sales) > 1:
            start_val = yearly_sales.iloc[0]
            end_val = yearly_sales.iloc[-1]
            periods = len(yearly_sales) - 1
            cagr = ((end_val / start_val) ** (1 / periods) - 1) if start_val != 0 and start_val > 0 else 0
            growth_trend = "increasing" if cagr > 0.05 else "decreasing" if cagr < -0.05 else "stable"
        
        top_regions = _top_n_performers(df, 'region', 'sales_volume', 3)
        top_models = _top_n_performers(df, 'model', 'sales_volume', 3)
        top_engine_sizes = _top_n_performers(df, 'engine_size_l', 'sales_volume', 3)
        top_fuel_types = _top_n_performers(df, 'fuel_type', 'sales_volume', 3)
        top_colors = _top_n_performers(df, 'color', 'sales_volume', 3)
        
        correlation_price_sales = df['price_usd'].corr(df['sales_volume'])
        corr_price_sales_desc = "negative" if correlation_price_sales < -0.4 else "positive" if correlation_price_sales > 0.4 else "neutral"
        
        correlation_mileage_price = df['mileage_km'].corr(df['price_usd'])
        corr_mileage_price_desc = "strong negative" if correlation_mileage_price < -0.6 else "negative" if correlation_mileage_price < -0.2 else "neutral"

        # ----------------------------------------------------
        # 2. Regional Insights (No Change)
        # ----------------------------------------------------
        region_sales = df.groupby('region')['sales_volume'].sum().sort_values(ascending=False)
        region_trends = {}
        for region in region_sales.index:
            region_df = df[df['region'] == region]
            
            region_trends[region] = {
                'total_sales': region_sales[region],
                'avg_price': region_df['price_usd'].mean(),
                'top_model': _top_n_performers(region_df, 'model', 'sales_volume', 1).index[0] if not region_df.empty else 'N/A',
                'top_fuel': _top_n_performers(region_df, 'fuel_type', 'sales_volume', 1).index[0] if not region_df.empty else 'N/A',
                'top_trans': _top_n_performers(region_df, 'transmission', 'sales_volume', 1).index[0] if not region_df.empty else 'N/A',
                'avg_mileage': region_df['mileage_km'].mean()
            }
        
        regional_price_stats = _get_column_stats(df, 'price_usd', ['region'])


        # ----------------------------------------------------
        # 3. Numerical Variable Statistics (No Change)
        # ----------------------------------------------------
        price_stats = _get_column_stats(df, 'price_usd')
        mileage_stats = _get_column_stats(df, 'mileage_km')
        engine_stats = _get_column_stats(df, 'engine_size_l')

        # ----------------------------------------------------
        # 4. Temporal and Categorical Insights (ENHANCED)
        # ----------------------------------------------------
        model_trends = _get_time_series_trends(df, 'model', n_top=3)
        fuel_trends = _get_time_series_trends(df, 'fuel_type', n_top=4)
        transmission_trends = _get_time_series_trends(df, 'transmission', n_top=2)
        
        # NEW: Temporal trend for BINNED Engine Size
        engine_size_trends = _get_time_series_trends(df, 'engine_size', n_top=3) 

        # NEW: Categorical Price/Sales Stats
        model_price_sales = _get_column_stats(df, 'price_usd', ['model'])
        model_sales_volume = _get_column_stats(df, 'sales_volume', ['model'])
        
        transmission_price_sales = _get_column_stats(df, 'price_usd', ['transmission'])
        fuel_price_sales = _get_column_stats(df, 'price_usd', ['fuel_type'])
        
        mileage_bin_price_sales = _get_column_stats(df, 'price_usd', ['mileage_bin'])
        
        # Helper to format grouped stats
        def format_grouped_stats(stats_dict: Dict[str, Dict[str, Any]], groupby_col: str, metric: str, price_format: bool = False) -> str:
            if isinstance(stats_dict, dict) and 'error' not in stats_dict:
                output = ""
                for group, stats in stats_dict.items():
                    mean_val = stats.get('mean', 0.0)
                    min_val = stats.get('min', 0.0)
                    max_val = stats.get('max', 0.0)
                    
                    mean_str = f"${mean_val:,.0f}" if price_format else f"{mean_val:,.0f}"
                    min_str = f"${min_val:,.0f}" if price_format else f"{min_val:,.0f}"
                    max_str = f"${max_val:,.0f}" if price_format else f"{max_val:,.0f}"
                    
                    output += f"* **{group}**: Mean {metric}: {mean_str} | Range: {min_str} - {max_str} | Count: {stats.get('count', 0)}\n"
                return output
            return f"* *Error or data not available for {groupby_col} {metric} statistics.*"
            

        # ----------------------------------------------------
        # 5. Construct Final Context String (ENHANCED)
        # ----------------------------------------------------
        context_str = (
            f"***COMPREHENSIVE VEHICLE SALES DATA CONTEXT***\n\n"
            
            f"## 📊 Global Performance Summary\n"
            f"--- \n"
            f"* **Total Revenue:** ${total_revenue:,.2f}\n"
            f"* **Total Sales Volume:** {total_sales:,} units\n"
            f"* **Time Period:** Data spans from year **{df['year'].min()}** to **{df['year'].max()}**.\n"
            f"* **Sales Trend:** The overall sales trend is **{growth_trend.upper()}** (CAGR: {cagr:.2%}).\n"
            f"    * *Yearly Sales Breakdown (Units):* {yearly_sales_str}\n"
            
            f"### Top Performers (By Sales Volume)\n"
            f"* **Top 3 Regions:** {', '.join([f'{r} ({s:,})' for r, s in top_regions.items()])}\n"
            f"* **Top 3 Models:** {', '.join([f'{m} ({s:,})' for m, s in top_models.items()])}\n"
            f"* **Top 3 Engine Sizes (L):** {', '.join([f'{e}L ({s:,})' for e, s in top_engine_sizes.items()])}\n"
            f"* **Top 3 Fuel Types:** {', '.join([f'{f} ({s:,})' for f, s in top_fuel_types.items()])}\n"
            f"* **Top 3 Colors:** {', '.join([f'{c} ({s:,})' for c, s in top_colors.items()])}\n"
            
            f"--- \n"
            f"## 💰 Price & Mileage Dynamics\n"
            f"--- \n"
            f"### Overall Numerical Variable Statistics\n"
            f"* **Price (USD) Stats:** Mean: ${price_stats.get('mean', 'N/A')}, Median: ${price_stats.get('median', 'N/A')}, Min: ${price_stats.get('min', 'N/A')}, Max: ${price_stats.get('max', 'N/A')}, IQR: ${price_stats.get('25%', 'N/A')} - ${price_stats.get('75%', 'N/A')}\n"
            f"* **Mileage (KM) Stats:** Mean: {mileage_stats.get('mean', 'N/A')}km, Median: {mileage_stats.get('median', 'N/A')}km, Max: {mileage_stats.get('max', 'N/A')}km.\n"
            f"* **Engine Size (L) Stats:** Mean: {engine_stats.get('mean', 'N/A')}L, Median: {engine_stats.get('median', 'N/A')}L.\n"
            
            f"### Correlation Insights\n"
            f"* **Price vs. Sales Volume:** A **{corr_price_sales_desc.upper()}** correlation ({correlation_price_sales:.2f}) suggests that **price sensitivity** is a factor. Lower prices may moderately drive higher sales, or high-volume models are aggressively priced.\n"
            f"* **Mileage vs. Price:** A **{corr_mileage_price_desc.upper()}** correlation ({correlation_mileage_price:.2f}) is observed. This confirms that **higher mileage generally corresponds to lower prices**, which is typical for vehicle depreciation.\n"
            
            f"--- \n"
            f"## 🌍 Regional Demand & Pricing Profile\n"
            f"--- \n"
        )

        # Regional-specific insights
        for region, data in region_trends.items():
            context_str += (
                f"* **Region: {region}**\n"
                f"    * Total Sales: **{data['total_sales']:,} units**\n"
                f"    * Average Price: **${data['avg_price']:.2f}**\n"
                f"    * Average Mileage: **{data['avg_mileage']:.0f}km**\n"
                f"    * Most Popular Model: **{data['top_model']}**\n"
                f"    * Preferred Fuel Type: **{data['top_fuel']}**\n"
                f"    * Preferred Transmission: **{data['top_trans']}**\n"
            )
        
        # Add grouping stats for regional pricing variations
        context_str += (
            f"### Detailed Regional Price Variation (Mean Price USD)\n"
        )
        if isinstance(regional_price_stats, dict) and 'error' not in regional_price_stats:
            for region, stats in regional_price_stats.items():
                context_str += f"* {region}: Mean: ${stats['mean']:.2f}, Max: ${stats['max']:.2f}, Min: ${stats['min']:.2f}\n"

        # --- NEW SECTION: CATEGORICAL_ANALYSIS ---
        context_str += "\nSECTION: CATEGORICAL_ANALYSIS\n---\n"
        
        context_str += "### Model Pricing and Sales Volume Summary\n"
        context_str += format_grouped_stats(model_price_sales, 'model', 'Price', price_format=True)
        context_str += format_grouped_stats(model_sales_volume, 'model', 'Sales Volume', price_format=False)
        
        context_str += "\n### Transmission Price Summary\n"
        context_str += format_grouped_stats(transmission_price_sales, 'transmission', 'Price', price_format=True)
        
        context_str += "\n### Fuel Type Price Summary\n"
        context_str += format_grouped_stats(fuel_price_sales, 'fuel_type', 'Price', price_format=True)
        
        context_str += "\n### Mileage Bin Price Summary (Depreciation Profile)\n"
        context_str += format_grouped_stats(mileage_bin_price_sales, 'mileage_bin', 'Price', price_format=True)

        # --- SECTION: TEMPORAL_MODEL_TRENDS ---
        context_str += "\nSECTION: TEMPORAL_MODEL_TRENDS\n---\n"
        for model, data in model_trends.items():
            context_str += f"MODEL: {model} | SUMMARY: {data['trend_summary']}\n"
            context_str += f"BREAKDOWN_{model}: {data['yearly_breakdown']}\n"

        # --- SECTION: TEMPORAL_FUEL_TRENDS ---
        context_str += "\nSECTION: TEMPORAL_FUEL_TRENDS\n---\n"
        for fuel, data in fuel_trends.items():
            context_str += f"FUEL_TYPE: {fuel} | SUMMARY: {data['trend_summary']}\n"
            context_str += f"BREAKDOWN_{fuel}: {data['yearly_breakdown']}\n"
        
        # --- SECTION: TEMPORAL_TRANSMISSION_TRENDS ---
        context_str += "\nSECTION: TEMPORAL_TRANSMISSION_TRENDS\n---\n"
        for trans, data in transmission_trends.items():
            context_str += f"TRANSMISSION: {trans} | SUMMARY: {data['trend_summary']}\n"
            context_str += f"BREAKDOWN_{trans}: {data['yearly_breakdown']}\n"
            
        # --- NEW SECTION: TEMPORAL_ENGINE_SIZE_TRENDS ---
        context_str += "\nSECTION: TEMPORAL_ENGINE_SIZE_TRENDS\n---\n"
        for size, data in engine_size_trends.items():
            context_str += f"ENGINE_SIZE: {size} | SUMMARY: {data['trend_summary']}\n"
            context_str += f"BREAKDOWN_{size}: {data['yearly_breakdown']}\n"
        
        # print(context_str)
        return context_str
