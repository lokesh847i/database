# =============================================================================
# Configuration File for Data Processing Tool
# =============================================================================
# Update these values according to your requirements

# Database Configuration
DB_CONFIG = {
    "host": "106.51.63.60",
    "user": "mahesh",
    "password": "mahesh_123",
    "database": "historicaldb"
}

# Date Range Configuration
DATE_CONFIG = {
    "start_date": "2024-10-01",
    "end_date": "2025-07-31"
}

# Folder Configuration
FOLDER_CONFIG = {
    "csv_folder_path": "C:\maruth\checker_schema\abcapital",      # Folder containing existing CSV files
    "output_folder": "C:\maruth\checker_schema\abcapital"         # Folder to save processed CSV files
}

# Database Table Names
TABLE_CONFIG = {
    "call_table": "abcapital_call",      # Call options table name
    "put_table": "abcapital_put",        # Put options table name
    "cash_table": "abcapital_cash",      # Cash/spot table name
    "future_table": "abcapital_future"   # Future table name
}

# Index Configuration
INDEX_CONFIG = {
    "index_name": "abcapital",           # Index name for the data
    "strike_increment": 100               # Strike price increment
}

# Greeks Calculation Configuration
GREEKS_CONFIG = {
    "risk_free_rate": 0.1,               # Risk-free interest rate
    "iv_lower_bound": 0.0001,            # Implied volatility lower bound
    "iv_upper_bound": 10.0               # Implied volatility upper bound
}

# Time Zone Configuration
TIME_ZONE_CONFIG = {
    "open_time": 1030,                   # Market open time (HHMM)
    "mid_morning": 1200,                 # Mid-morning time (HHMM)
    "lunch_time": 1330,                  # Lunch time (HHMM)
    "afternoon": 1500,                   # Afternoon time (HHMM)
    "close_time": 1500                   # Market close time (HHMM)
}

# Expiry Bucket Configuration
EXPIRY_CONFIG = {
    "current_month": 30,                 # Days to expiry for current month
    # "next_month": 60,                  # Days to expiry for next month (uncomment if needed)
}

# Output File Configuration
OUTPUT_CONFIG = {
    "file_prefix": "abcapital",         # Prefix for output CSV files
    "file_suffix": "processed.csv"       # Suffix for output CSV files
}

# Processing Configuration
PROCESSING_CONFIG = {
    "price_divisor": 100,                # Divisor for price normalization
    "time_format": "%02d:%02d"           # Time format for conversion
}

# =============================================================================
# Quick Configuration Switches
# =============================================================================

# Set to True to enable future data processing
ENABLE_FUTURE_DATA = True

# Set to True to enable Greeks calculation
ENABLE_GREEKS_CALCULATION = True

# Set to True to enable time zone classification
ENABLE_TIME_ZONE_CLASSIFICATION = True

# Set to True to enable expiry bucket classification
ENABLE_EXPIRY_BUCKET_CLASSIFICATION = True

# =============================================================================
# Advanced Configuration
# =============================================================================

# Column mappings for different table structures
COLUMN_MAPPINGS = {
    "call_columns": {
        "symbol": "ce_symbol",
        "open": "ce_open",
        "high": "ce_high",
        "low": "ce_low",
        "close": "ce_close",
        "volume": "ce_volume",
        "oi": "ce_oi",
        "coi": "ce_coi"
    },
    "put_columns": {
        "symbol": "pe_symbol",
        "open": "pe_open",
        "high": "pe_high",
        "low": "pe_low",
        "close": "pe_close",
        "volume": "pe_volume",
        "oi": "pe_oi",
        "coi": "pe_coi"
    },
    "future_columns": {
        "open": "future_open",
        "high": "future_high",
        "low": "future_low",
        "close": "future_close",
        "volume": "future_volume",
        "oi": "future_oi",
        "coi": "future_coi"
    }
}

# Output column order
OUTPUT_COLUMNS = [
    'trade_date', 'trade_time', 'expiry_date', 'index_name', 'spot', 'atm_strike',
    'strike', 'dte', 'expiry_bucket', 'zone_id', 'zone_name', 'call_strike_type',
    'put_strike_type', 'ce_symbol', 'ce_open', 'ce_high', 'ce_low', 'ce_close',
    'ce_volume', 'ce_oi', 'ce_coi', 'ce_iv', 'ce_delta', 'ce_gamma', 'ce_theta',
    'ce_vega', 'ce_rho', 'pe_symbol', 'pe_open', 'pe_high', 'pe_low', 'pe_close',
    'pe_volume', 'pe_oi', 'pe_coi', 'pe_iv', 'pe_delta', 'pe_gamma', 'pe_theta',
    'pe_vega', 'pe_rho'
]

# =============================================================================
# Logging Configuration
# =============================================================================
LOGGING_CONFIG = {
    "enable_console_logging": True,
    "enable_file_logging": False,
    "log_file_path": "processing.log",
    "log_level": "INFO"
} 