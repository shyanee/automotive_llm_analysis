import pytest
import pandas as pd
from datetime import date

# --- Fixtures ---

@pytest.fixture(scope="module")
def data_validator():
    """Fixture to instantiate the DataValidator class."""
    from src.data_validator import DataValidator
    return DataValidator()

@pytest.fixture
def sample_data():
    """Fixture to provide a clean sample dataframe for base testing."""
    data = {
        'model': ['7 Series', '5 Series', '3 Series', '7 Series', '5 Series', '3 Series'],
        'year': [2010, 1995, 2020, 1980, 2022, 1989],
        'region': ['North America', 'Europe', 'Asia', 'North America', 'Europe', 'Asia'], 
        'fuel_type': ['Petrol', 'Diesel', 'Petrol', 'Diesel', 'Petrol', 'Diesel'], 
        'mileage_km': [50000, 100000, 150000, 200000, 300000, 250000], 
        'price_usd': [50000, 10000, 20000, 35000, 100000, 80000], 
        'sales_volume': [100, 50, 500, 600, 1500, 200] 
    }
    # data = pd.read_csv(DATA_PATH)
    return pd.DataFrame(data)

# --- Validation Tests (validate_dataframe) ---

def test_validate_success_on_clean_data(data_validator, sample_data):
    """Test that a clean DataFrame passes validation without errors or warnings."""
    # Act
    report = data_validator.validate_dataframe(sample_data, {})
    
    # Assert
    assert report['passed'] is True
    assert len(report['errors']) == 0
    assert len(report['warnings']) == 0
    assert report['stats']['total_rows'] == len(sample_data)

def test_validate_reports_warning_for_duplicate_rows(data_validator, sample_data):
    """Test that duplicate rows are correctly identified as a warning."""
    # Arrange: Add one duplicate row
    duplicated_data = pd.concat([sample_data, sample_data.iloc[0:1]], ignore_index=True)
    
    # Act
    report = data_validator.validate_dataframe(duplicated_data, {})
    
    # Assert
    assert 'Found 1 duplicate rows' in report['warnings']
    assert report['passed'] is True # Duplicates are warnings, so 'passed' is still True
    assert report['stats']['duplicate_rows'] == 1

def test_validate_reports_error_for_negative_numeric_values(data_validator, sample_data):
    """Test that negative values in protected columns (price, sales, mileage) cause errors."""
    # Arrange: Create data with specific negative values
    invalid_data = sample_data.copy()
    invalid_data.loc[0, 'price_usd'] = -1000
    invalid_data.loc[1, 'sales_volume'] = -5
    invalid_data.loc[2, 'mileage_km'] = -1
    
    # Act
    report = data_validator.validate_dataframe(invalid_data, {})
    
    # Assert: Check for specific errors and that overall validation failed
    assert 'price_usd has 1 negative values' in report['errors']
    assert 'sales_volume has 1 negative values' in report['errors']
    assert 'mileage_km has 1 negative values' in report['errors']
    assert len(report['errors']) == 3
    assert report['passed'] is False

def test_validate_reports_warning_for_unrealistic_year(data_validator, sample_data):
    """Test that years outside the 1900-2030 range trigger a warning."""
    # Arrange: Introduce an unrealistic year (e.g., in the future 2035)
    invalid_year_data = sample_data.copy()
    invalid_year_data.loc[0, 'year'] = 2035
    
    # Act
    report = data_validator.validate_dataframe(invalid_year_data, {})
    
    # Assert
    assert 'Found 1 rows with unrealistic years' in report['warnings']
    assert report['passed'] is True

def test_validate_reports_warning_for_price_outliers(data_validator, sample_data):
    """Test that price outliers (< $10k or > $800k) trigger a warning."""
    # Arrange: Introduce price outliers
    outlier_data = sample_data.copy()
    outlier_data.loc[0, 'price_usd'] = 500 # Too low
    outlier_data.loc[1, 'price_usd'] = 950000 # Too high (Original code had 800k check)
    
    # Act
    report = data_validator.validate_dataframe(outlier_data, {})
    
    # Assert
    assert 'Found 2 rows with unusual prices (< $10k or > $500k)' in report['warnings']
    assert report['passed'] is True

def test_validate_reports_warning_for_high_missing_percentage(data_validator):
    """Test that a column with >50% missing values triggers a warning."""
    # Arrange: Create a DataFrame where one column is 60% missing (3/5)
    data_with_high_missing = pd.DataFrame({
        'price_usd': [10000, 20000, None, 40000, 50000],
        'critical_col': [1, 2, None, None, None], # 3/5 = 60% missing
    })
    
    # Act
    report = data_validator.validate_dataframe(data_with_high_missing, {})
    
    # Assert
    assert 'Columns with >50% missing' in report['warnings'][0]
    # NOTE: The actual output string will contain the dictionary. Check for the column name.
    assert 'critical_col' in report['warnings'][0]
    assert report['passed'] is True

def test_validate_reports_warning_for_high_cardinality(data_validator):
    """Test that a categorical column with too many unique values (high cardinality) triggers a warning."""
    # Arrange: Create a DataFrame with 10 rows, where one column has 7 unique values (70% > 50%)
    
    # IDs 0, 1, 2, 3, 4, 5, 6 (7 unique values).
    # The remaining 3 rows repeat existing IDs but must have a unique identifier in another column.
    high_cardinality_data = pd.DataFrame({
        'unique_id': [f'ID_{i}' for i in range(7)] + ['ID_0', 'ID_1', 'ID_2'],
        'row_sequence': list(range(10)),
        'category': ['X'] * 10
    })
    
    # ACT
    report = data_validator.validate_dataframe(high_cardinality_data, {})
    
    # ASSERT
    # 1. Check that the only warning is the high cardinality one.
    # The 'row_sequence' ensures the rows are unique, so len(warnings) should now be 1.
    assert len(report['warnings']) == 1
    
    # 2. Check for the correct warning message and unique count (7 unique values)
    expected_substring = 'unique_id has high cardinality (7 unique values)'
    
    # This assertion now checks the content of the single expected warning
    assert expected_substring in report['warnings'][0] 
    assert report['passed'] is True

# --- Business Rule Enforcement Tests (enforce_business_rules) ---

def test_enforce_rules_removes_negative_prices(data_validator, sample_data):
    """Test that enforce_business_rules removes rows where price_usd is not positive."""
    # Arrange: Add a row with a negative price (violates > 0)
    df_with_invalid_prices = sample_data.copy()
    df_with_invalid_prices.loc[len(df_with_invalid_prices)] = {
        'price_usd': -500, 'sales_volume': 300, 'mileage_km': 100000, 'year': 2020, 'model': 'Z',
        'region': 'NA', 'fuel_type': 'Gas'
    }
    original_len = len(df_with_invalid_prices)
    
    # Act
    cleaned_df = data_validator.enforce_business_rules(df_with_invalid_prices)
    
    # Assert
    assert len(cleaned_df) == original_len - 1
    assert cleaned_df['price_usd'].min() > 0 # Should now be strictly greater than 0

def test_enforce_rules_removes_negative_sales_volume(data_validator, sample_data):
    """Test that enforce_business_rules removes rows where sales_volume is negative."""
    # Arrange: Add a row with a negative sales_volume (violates >= 0)
    df_with_invalid_sales = sample_data.copy()
    df_with_invalid_sales.loc[len(df_with_invalid_sales)] = {
        'price_usd': 50000, 'sales_volume': -10, 'mileage_km': 100000, 'year': 2020, 'model': 'Z',
        'region': 'NA', 'fuel_type': 'Gas'
    }
    original_len = len(df_with_invalid_sales)
    
    # Act
    cleaned_df = data_validator.enforce_business_rules(df_with_invalid_sales)
    
    # Assert
    assert len(cleaned_df) == original_len - 1
    assert cleaned_df['sales_volume'].min() >= 0

def test_enforce_rules_removes_unrealistic_years(data_validator, sample_data):
    """Test that enforce_business_rules removes years outside the 1980-Today range."""
    
    # Arrange: Add a year too old (1979) and a year too new (today_year + 1)
    future_year = date.today().year + 1
    
    df_with_invalid_year = sample_data.copy()
    df_with_invalid_year.loc[len(df_with_invalid_year)] = {
        'price_usd': 30000, 'sales_volume': 200, 'mileage_km': 100000, 'year': 1979, 'model': 'Z1',
        'region': 'NA', 'fuel_type': 'Gas'
    }
    df_with_invalid_year.loc[len(df_with_invalid_year)] = {
        'price_usd': 30000, 'sales_volume': 200, 'mileage_km': 100000, 'year': future_year, 'model': 'Z2',
        'region': 'NA', 'fuel_type': 'Gas'
    }
    original_len = len(df_with_invalid_year)
    
    # Act
    cleaned_df = data_validator.enforce_business_rules(df_with_invalid_year)
    
    # Assert: Should remove the 2 invalid rows
    assert len(cleaned_df) == original_len - 2
    assert cleaned_df['year'].max() <= date.today().year
    assert cleaned_df['year'].min() >= 1980