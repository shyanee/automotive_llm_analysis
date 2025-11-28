import pytest
import os
import pandas as pd

@pytest.fixture
def sample_data():
    """Fixture to create a simple DataFrame for testing."""
    data = {
        'year': [2021, 2021, 2022, 2022],
        'region': ['North America', 'North America', 'North America', 'Asia'],
        'sales_volume': [100, 150, 120, 170],
        'model': ['7 Series', '7 Series', '7 Series', '3 Series'],
        'fuel_type': ['Gas', 'Diesel', 'Gas', 'Diesel'],
        'price_usd': [20000, 25000, 22000, 26000],
        'engine_size_l': [2.0, 2.5, 2.0, 2.5],
        'engine_size': [2.0, 2.0, 4.0, 1.0],
        'transmission': ['Automatic', 'Manual', 'Automatic', 'Manual']
    }
    return pd.DataFrame(data)

@pytest.fixture
def visualizer(sample_data):
    """Fixture to initialize the Visualizer with mock data."""
    from src.visualiser import Visualizer
    return Visualizer(sample_data)

def test_generate_plots(visualizer):
    """Test that the generate_plots method generates all expected plot files."""
    
    # Call generate_plots method
    plots = visualizer.generate_plots()
    
    # Assert that the plots dictionary contains all the required keys
    expected_plot_keys = [
        'combined_trend_plot',
        'top_models_plot',
        'price_elasticity_plot',
        'engine_price_box'
    ]
    for plot_key in expected_plot_keys:
        assert plot_key in plots, f"Missing plot: {plot_key}"
    
    # Assert that the output directory exists
    assert os.path.isdir(visualizer.output_dir), f"Output directory does not exist: {visualizer.output_dir}"
    
    # Check that HTML files were created for each plot
    for plot_key in expected_plot_keys:
        html_file_path = os.path.join(visualizer.output_dir, f'{plot_key}.html')
        assert os.path.isfile(html_file_path), f"HTML file for {plot_key} was not created: {html_file_path}"

