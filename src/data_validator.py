import pandas as pd
from typing import List, Dict
import logging
from datetime import date

class DataValidator:
    """Validates data quality and business logic constraints."""
    
    def __init__(self, logger=None):
        self.logger = logger or logging.getLogger(__name__)
        self.validation_report = {}
    
    def validate_dataframe(self, df: pd.DataFrame, config: dict) -> Dict[str, any]:
        """
        Comprehensive data validation with reporting.
        
        Returns:
            dict: Validation report with issues and statistics
        """
        report = {
            'passed': True,
            'warnings': [],
            'errors': [],
            'stats': {}
        }
        
        # 1. Check for duplicate rows
        duplicates = df.duplicated().sum()
        if duplicates > 0:
            report['warnings'].append(f"Found {duplicates} duplicate rows")
            self.logger.warning(f"Found {duplicates} duplicate rows")
        
        # 2. Check for negative values in numeric columns
        numeric_cols = df.select_dtypes(include='number').columns
        for col in numeric_cols:
            if col in ['price_usd', 'sales_volume', 'mileage_km']:
                negative_count = (df[col] < 0).sum()
                if negative_count > 0:
                    report['errors'].append(f"{col} has {negative_count} negative values")
                    report['passed'] = False
        
        # 3. Check for unrealistic values
        if 'year' in df.columns:
            invalid_years = df[(df['year'] < 1900) | (df['year'] > 2030)]
            if len(invalid_years) > 0:
                report['warnings'].append(f"Found {len(invalid_years)} rows with unrealistic years")
        
        if 'price_usd' in df.columns:
            outliers = df[(df['price_usd'] < 10000) | (df['price_usd'] > 800000)]
            if len(outliers) > 0:
                report['warnings'].append(
                    f"Found {len(outliers)} rows with unusual prices (< $10k or > $500k)"
                )
        
        # 4. Missing value analysis
        missing_pct = (df.isnull().sum() / len(df) * 100).to_dict()
        high_missing = {k: v for k, v in missing_pct.items() if v > 50}
        if high_missing:
            report['warnings'].append(
                f"Columns with >50% missing: {high_missing}"
            )
        
        # 5. Cardinality checks (detect potential data entry errors)
        categorical_cols = df.select_dtypes(include='object').columns
        for col in categorical_cols:
            unique_count = df[col].nunique()
            # If a categorical column has too many unique values, might indicate dirty data
            if unique_count > len(df) * 0.5:
                report['warnings'].append(
                    f"{col} has high cardinality ({unique_count} unique values) - check for typos"
                )
        
        # 6. Generate statistics
        report['stats'] = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'missing_values': df.isnull().sum().sum(),
            'duplicate_rows': duplicates,
            'memory_usage_mb': df.memory_usage(deep=True).sum() / 1024**2
        }
        
        # Log summary
        self.logger.info(f"Validation complete: {len(report['errors'])} errors, "
                        f"{len(report['warnings'])} warnings")
        
        return report
    
    def enforce_business_rules(self, df: pd.DataFrame) -> pd.DataFrame:
        """Apply business logic constraints and filters."""
        original_len = len(df)
        
        # Remove invalid records
        if 'price_usd' in df.columns:
            df = df[df['price_usd'] > 0]
        
        if 'sales_volume' in df.columns:
            df = df[df['sales_volume'] >= 0]
        
        today_year = date.today().year
        if 'year' in df.columns:
            df = df[(df['year'] >= 1980) & (df['year'] <= today_year)]
        
        removed = original_len - len(df)
        if removed > 0:
            self.logger.info(f"Removed {removed} invalid records after business rule enforcement")
        
        return df