import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import os
from src.utils import utils

CONFIG_PATH=os.path.join('config', 'config.yml')
DATA_PATH=os.path.join('tests', 'mock_data', 'test_sales_data.csv')

# Mock data for testing
mock_data = {
    'model': ['7 Series', '7 Series', '3 Series'],
    'year': [2015, 2016, 2017],
    'engine_size_l': [1.5, 2.0, 1.8],
    'mileage_km': [30000, 50000, 70000],
    'transmission': ['Manual', 'Automatic', 'Automatic'],
    'sales_volume': [100, 150, 200],
    'price_usd': [15000, 20000, 25000],
    'region': ['North America', 'North America', 'Asia'],
    'fuel_type': ['Gas', 'Diesel', 'Electric'],
    'color': ['Red', 'Blue', 'Black']
}
sample_data = pd.DataFrame(mock_data)
# sample_data = pd.read_csv(DATA_PATH)

# --- Fixtures ---

@pytest.fixture
def config_columns():
    config = utils.load_config(CONFIG_PATH)
    config_columns = config.get('data', {}).get('columns', [])
    return config_columns

@pytest.fixture
def preprocessor(config_columns):
    # Fixture to create a DataPreprocessor instance
    from src.preprocessor import DataPreprocessor
    # data_preprocessor = DataPreprocessor(filepath=DATA_PATH, expected_columns=[
    #     'model', 'year', 'engine_size_l', 'mileage_km', 'transmission', 'sales_volume', 'price_usd', 'region', 'fuel_type', 'color'
    # ])
    data_preprocessor = DataPreprocessor(filepath=DATA_PATH, expected_columns=config_columns)
    return data_preprocessor


# --- Tests ---

# Test for the _read_file method
def test_read_csv_file(preprocessor):
    # Fixture: Mocking pd.read_csv to return the mock dataframe
    with patch('pandas.read_csv', return_value=sample_data) as mock_read_csv:
        # Act: Call the _read_file method
        df = preprocessor._read_file(DATA_PATH)
        
        # Assert: Check if the read file matches the mock dataframe and the correct method was called
        mock_read_csv.assert_called_once_with(DATA_PATH)
        assert df.equals(sample_data)


def test_read_excel_file(preprocessor):
    # Fixture: Mocking pd.read_excel to return the mock dataframe
    with patch('pandas.read_excel', return_value=sample_data) as mock_read_excel:
        # Act: Call the _read_file method with an Excel file
        preprocessor.filepath = 'tests/mock_data/test_sales_data.xlsx'
        df = preprocessor._read_file('tests/mock_data/test_sales_data.xlsx')
        
        # Assert: Check if the read file matches the mock dataframe and the correct method was called
        mock_read_excel.assert_called_once_with('tests/mock_data/test_sales_data.xlsx')
        assert df.equals(sample_data)


# Test for the get_clean_df method
def test_get_clean_df(preprocessor):
    # Fixture: Mock the logger to avoid actual log printing during tests
    with patch.object(preprocessor, 'logger', MagicMock()):
        # Fixture: Mock _read_file method to return mock data
        with patch.object(preprocessor, '_read_file', return_value=sample_data):
            # Act: Call the get_clean_df method to clean the data
            df = preprocessor.get_clean_df()

            # Assert: Validate that the dataframe is cleaned correctly
            assert df.shape == (3, 12)  # Updated expected shape (3 rows, 12 columns)
            assert 'mileage_bin' in df.columns  # Check if 'mileage_bin' column is added
            assert df['mileage_bin'].iloc[0] == '0-50k'  # Check if mileage binning works correctly


# Test for the extract_llm_context method
def test_extract_llm_context(preprocessor):
    # Fixture: Mock the get_clean_df method to return mock data
    with patch.object(preprocessor, 'get_clean_df', return_value=sample_data):
        # Act: Call the extract_llm_context method
        context = preprocessor.extract_llm_context(sample_data)
        
        # Assert: Check if the context string is returned
        assert isinstance(context, str)
        assert "COMPREHENSIVE VEHICLE SALES DATA CONTEXT" in context  # Verify that context starts with the expected heading


# Test for ValueError when missing columns are detected
def test_get_clean_df_missing_columns(preprocessor):
    # Fixture: Simulate missing columns by removing a column
    incomplete_data = mock_data.copy()
    del incomplete_data['region']  # Remove a required column 'region'
    incomplete_df = pd.DataFrame(incomplete_data)

    # Fixture: Mock _read_file to return the incomplete dataframe
    with patch.object(preprocessor, '_read_file', return_value=incomplete_df):
        # Act & Assert: Verify that the method raises ValueError for missing columns
        with pytest.raises(ValueError) as excinfo:
            preprocessor.get_clean_df()
        assert "Input CSV is missing columns defined in config" in str(excinfo.value)


# Test for handling of file reading errors (e.g., file not found)
def test_read_file_error(preprocessor):
    # Fixture: Mock _read_file to raise an error (simulate a file reading error)
    with patch.object(preprocessor, '_read_file', side_effect=RuntimeError("File not found")):
        # Act & Assert: Verify that RuntimeError is raised during file reading
        with pytest.raises(RuntimeError) as excinfo:
            preprocessor.get_clean_df()
        assert "File not found" in str(excinfo.value)  # Check for the actual error message


# Test for logger calls
def test_logger_calls(preprocessor):
    # Fixture: Mock the logger
    with patch.object(preprocessor, 'logger', MagicMock()) as mock_logger:
        # Fixture: Mock _read_file method to return mock data
        with patch.object(preprocessor, '_read_file', return_value=sample_data):
            # Act: Call the get_clean_df method to trigger logger calls
            preprocessor.get_clean_df()
            
            # Assert: Check if info and error messages are logged
            mock_logger.info.assert_called()
            mock_logger.error.assert_not_called()  # In this case, error should not be called


@pytest.mark.parametrize(
    "column, expected_type",
    [
        ('sales_volume', np.int64),
        ('price_usd', np.int64), 
        ('year', np.int64),
    ]
)
def test_column_data_types(preprocessor, column, expected_type):
    with patch.object(preprocessor, '_read_file', return_value=sample_data):
        df = preprocessor.get_clean_df()
        assert df[column].dtype == expected_type
