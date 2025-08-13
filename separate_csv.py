import pandas as pd
import os
import mysql.connector
from datetime import datetime
import csv

# Database configuration
DB_CONFIG = {
    'user': 'root',
    'password': 'Jmd@1976',
    'host': 'localhost',
    'database': 'historicaldb',
    'raise_on_warnings': True,
    'charset': 'utf8mb4',
    'autocommit': False
}

class DatabaseChecker:
    def __init__(self, config):
        """Initialize database connection"""
        self.config = config
        self.connection = None
        self.cursor = None
        self.connect()
    
    def connect(self):
        """Connect to database"""
        try:
            self.connection = mysql.connector.connect(**self.config)
            self.cursor = self.connection.cursor()
            print("✓ Database connected successfully")
        except mysql.connector.Error as e:
            print(f"✗ Database connection failed: {e}")
            raise
    
    def disconnect(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("Database disconnected")
    
    def check_data_exists(self, table_name, symbol, date):
        """
        Check if data exists for a specific symbol and date
        
        Args:
            table_name: Name of the table to check
            symbol: Symbol to check
            date: Date in YYMMDD format
            
        Returns:
            bool: True if data exists, False otherwise
        """
        try:
            # Check if table exists
            self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            if not self.cursor.fetchone():
                print(f"  Table '{table_name}' does not exist")
                return False
            
            # Check if data exists for the symbol and date
            query = f"""
            SELECT COUNT(*) FROM {table_name} 
            WHERE symbol = %s AND date = %s
            """
            self.cursor.execute(query, (symbol, date))
            count = self.cursor.fetchone()[0]
            
            return count > 0
            
        except Exception as e:
            print(f"  Error checking data: {e}")
            return False
    
    def insert_missing_data(self, table_name, data_dict):
        """
        Insert missing data into the database
        
        Args:
            table_name: Name of the table
            data_dict: Dictionary containing the data to insert
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Create table if it doesn't exist
            self.create_table_if_not_exists(table_name)
            
            # Insert data
            columns = ', '.join(data_dict.keys())
            placeholders = ', '.join(['%s'] * len(data_dict))
            insert_query = f"""
            INSERT INTO {table_name} ({columns})
            VALUES ({placeholders})
            """
            
            self.cursor.execute(insert_query, list(data_dict.values()))
            self.connection.commit()
            return True
            
        except Exception as e:
            print(f"  Error inserting data: {e}")
            self.connection.rollback()
            return False
    
    def create_table_if_not_exists(self, table_name):
        """Create table if it doesn't exist"""
        try:
            # Determine table type from name
            table_type = 'cash'  # default
            if '_call' in table_name:
                table_type = 'call'
            elif '_put' in table_name:
                table_type = 'put'
            elif '_future' in table_name:
                table_type = 'future'
            
            # Base schema for all types
            base_schema = """
                date INT NOT NULL,
                time INT NOT NULL,
                symbol VARCHAR(50) NOT NULL,
                open DECIMAL(10,2) NOT NULL,
                high DECIMAL(10,2) NOT NULL,
                low DECIMAL(10,2) NOT NULL,
                close DECIMAL(10,2) NOT NULL,
                volume BIGINT DEFAULT 0,
                oi BIGINT DEFAULT 0,
                coi BIGINT DEFAULT 0,
                INDEX idx_date (date),
                INDEX idx_symbol (symbol)
            """
            
            # Add specific fields based on table type
            if table_type in ['call', 'put']:
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {base_schema.replace('INDEX idx_symbol (symbol)', '')},
                    strike DECIMAL(10,2) NOT NULL DEFAULT 0.0,
                    expiry INT NOT NULL DEFAULT 0,
                    INDEX idx_symbol (symbol),
                    INDEX idx_expiry (expiry),
                    INDEX idx_strike (strike)
                )
                """
            elif table_type == 'future':
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {base_schema.replace('INDEX idx_symbol (symbol)', '')},
                    strike DECIMAL(10,2) DEFAULT 0.0,
                    expiry INT NOT NULL DEFAULT 0,
                    INDEX idx_symbol (symbol),
                    INDEX idx_expiry (expiry)
                )
                """
            else:  # cash
                create_table_query = f"""
                CREATE TABLE IF NOT EXISTS {table_name} (
                    {base_schema.replace('INDEX idx_symbol (symbol)', '')},
                    strike DECIMAL(10,2) DEFAULT 0.0,
                    expiry INT DEFAULT 0,
                    INDEX idx_symbol (symbol)
                )
                """
            
            self.cursor.execute(create_table_query)
            self.connection.commit()
            print(f"  Table '{table_name}' created/verified")
            
        except Exception as e:
            print(f"  Error creating table: {e}")
            raise

def parse_date(date_str):
    """Parse date from DD-MM-YYYY format to YYMMDD integer"""
    try:
        if not date_str or str(date_str).strip() == '':
            return 0
        
        date_str = str(date_str).strip()
        
        # Handle DD-MM-YYYY format (e.g., '02-12-2024')
        if '-' in date_str and len(date_str.split('-')) == 3:
            parts = date_str.split('-')
            if len(parts[2]) == 4:  # DD-MM-YYYY
                day, month, year = parts
                year_short = int(year) % 100
                return year_short * 10000 + int(month) * 100 + int(day)
            elif len(parts[0]) == 4:  # YYYY-MM-DD
                year, month, day = parts
                year_short = int(year) % 100
                return year_short * 10000 + int(month) * 100 + int(day)
        
        # Handle 6-digit format (already YYMMDD)
        if date_str.isdigit() and len(date_str) == 6:
            return int(date_str)
            
        # Handle 8-digit format (YYYYMMDD)
        if date_str.isdigit() and len(date_str) == 8:
            year = int(date_str[:4]) % 100
            month = int(date_str[4:6])
            day = int(date_str[6:8])
            return year * 10000 + month * 100 + day
            
    except Exception as e:
        print(f"Error parsing date {date_str}: {e}")
        return 0
    return 0

def process_csv_file(csv_file, db_checker):
    """
    Process a single CSV file and check/upload missing data
    
    Args:
        csv_file: Path to the CSV file
        db_checker: DatabaseChecker instance
    """
    print(f"\nProcessing: {os.path.basename(csv_file)}")
    
    try:
        # Read CSV file
        df = pd.read_csv(csv_file)
        print(f"  Total rows: {len(df)}")
        
        # Determine table name and type from filename
        base_name = os.path.splitext(os.path.basename(csv_file))[0]
        
        # Create separate dataframes for each category
        call_data = []
        put_data = []
        cash_data = []
        future_data = []
        
        # Process each row
        for index, row in df.iterrows():
            table_name = str(row['table_name'])
            
            if table_name.endswith('_call'):
                call_data.append(row)
            elif table_name.endswith('_put'):
                put_data.append(row)
            elif table_name.endswith('_cash'):
                cash_data.append(row)
            elif table_name.endswith('_future'):
                future_data.append(row)
            else:
                print(f"  Warning: Unknown category for {table_name}")
        
        # Process each category
        total_processed = 0
        total_skipped = 0
        
        for category_name, data_list in [
            ('Call', call_data), 
            ('Put', put_data), 
            ('Cash', cash_data), 
            ('Future', future_data)
        ]:
            if data_list:
                print(f"  Processing {category_name} data: {len(data_list)} rows")
                processed, skipped = process_category_data(data_list, category_name.lower(), db_checker)
                total_processed += processed
                total_skipped += skipped
        
        print(f"  Summary: {total_processed} rows processed, {total_skipped} rows skipped")
        return total_processed, total_skipped
        
    except Exception as e:
        print(f"  Error processing file: {e}")
        return 0, 0

def process_category_data(data_list, category_type, db_checker):
    """
    Process data for a specific category
    
    Args:
        data_list: List of data rows
        category_type: Type of category (call, put, cash, future)
        db_checker: DatabaseChecker instance
        
    Returns:
        tuple: (processed_count, skipped_count)
    """
    processed = 0
    skipped = 0
    
    for row in data_list:
        try:
            # Extract data from row
            table_name = str(row['table_name'])
            date_str = str(row['missing_date'])
            symbol = table_name.replace(f'_{category_type}', '')  # Remove suffix to get base symbol
            
            # Parse date
            date_int = parse_date(date_str)
            if date_int == 0:
                print(f"    Warning: Invalid date format: {date_str}")
                skipped += 1
                continue
            
            # Check if data already exists
            if db_checker.check_data_exists(table_name, symbol, date_int):
                print(f"    ✓ Data exists for {symbol} on {date_str} - skipping")
                skipped += 1
                continue
            
            # Data doesn't exist, prepare for insertion
            print(f"    + Missing data for {symbol} on {date_str} - will insert")
            
            # Create data dictionary for insertion
            data_dict = {
                'date': date_int,
                'time': 0,  # Default time
                'symbol': symbol,
                'open': 0.0,
                'high': 0.0,
                'low': 0.0,
                'close': 0.0,
                'volume': 0,
                'oi': 0,
                'coi': 0
            }
            
            # Add category-specific fields
            if category_type in ['call', 'put']:
                data_dict['strike'] = 0.0
                data_dict['expiry'] = 0
            elif category_type == 'future':
                data_dict['strike'] = 0.0
                data_dict['expiry'] = 0
            
            # Insert the data
            if db_checker.insert_missing_data(table_name, data_dict):
                processed += 1
                print(f"      ✓ Data inserted successfully")
            else:
                skipped += 1
                print(f"      ✗ Failed to insert data")
                
        except Exception as e:
            print(f"    Error processing row: {e}")
            skipped += 1
            continue
    
    return processed, skipped

def separate_csv_by_category(input_file, check_database=False):
    """
    Separate CSV data into different files based on call, put, cash, and future categories
    
    Args:
        input_file: Path to the input CSV file
        check_database: Whether to check database for existing data
    """
    print(f"Reading CSV file: {input_file}")
    
    # Read the CSV file
    df = pd.read_csv(input_file)
    
    print(f"Total rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    
    # Create separate dataframes for each category
    call_data = []
    put_data = []
    cash_data = []
    future_data = []
    
    # Process each row
    for index, row in df.iterrows():
        table_name = str(row['table_name'])
        
        if table_name.endswith('_call'):
            call_data.append(row)
        elif table_name.endswith('_put'):
            put_data.append(row)
        elif table_name.endswith('_cash'):
            cash_data.append(row)
        elif table_name.endswith('_future'):
            future_data.append(row)
        else:
            # If no suffix matches, skip or categorize as needed
            print(f"Warning: Unknown category for {table_name}")
    
    # Create output directory if it doesn't exist
    output_dir = "separated_csvs"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    
    # Save each category to separate CSV files
    if call_data:
        call_df = pd.DataFrame(call_data)
        call_file = os.path.join(output_dir, "call_data.csv")
        call_df.to_csv(call_file, index=False)
        print(f"Call data saved to: {call_file} ({len(call_data)} rows)")
    
    if put_data:
        put_df = pd.DataFrame(put_data)
        put_file = os.path.join(output_dir, "put_data.csv")
        put_df.to_csv(put_file, index=False)
        print(f"Put data saved to: {put_file} ({len(put_data)} rows)")
    
    if cash_data:
        cash_df = pd.DataFrame(cash_data)
        cash_file = os.path.join(output_dir, "cash_data.csv")
        cash_df.to_csv(cash_file, index=False)
        print(f"Cash data saved to: {cash_file} ({len(cash_data)} rows)")
    
    if future_data:
        future_df = pd.DataFrame(future_data)
        future_file = os.path.join(output_dir, "future_data.csv")
        future_df.to_csv(future_file, index=False)
        print(f"Future data saved to: {future_file} ({len(future_data)} rows)")
    
    # Print summary
    print("\n" + "="*50)
    print("SUMMARY:")
    print(f"Call records: {len(call_data)}")
    print(f"Put records: {len(put_data)}")
    print(f"Cash records: {len(cash_data)}")
    print(f"Future records: {len(future_data)}")
    print(f"Total processed: {len(call_data) + len(put_data) + len(cash_data) + len(future_data)}")
    print("="*50)
    
    # If database checking is enabled, process the separated files
    if check_database:
        print("\n" + "="*50)
        print("DATABASE CHECKING AND UPLOADING")
        print("="*50)
        
        try:
            # Initialize database checker
            db_checker = DatabaseChecker(DB_CONFIG)
            
            # Process each separated CSV file
            total_files_processed = 0
            total_rows_processed = 0
            total_rows_skipped = 0
            
            for csv_file in [call_file, put_file, cash_file, future_file]:
                if os.path.exists(csv_file):
                    processed, skipped = process_csv_file(csv_file, db_checker)
                    total_rows_processed += processed
                    total_rows_skipped += skipped
                    total_files_processed += 1
            
            # Final summary
            print("\n" + "="*50)
            print("DATABASE PROCESSING SUMMARY:")
            print(f"Files processed: {total_files_processed}")
            print(f"Total rows inserted: {total_rows_processed}")
            print(f"Total rows skipped: {total_rows_skipped}")
            print("="*50)
            
            # Disconnect from database
            db_checker.disconnect()
            
        except Exception as e:
            print(f"Database processing failed: {e}")

def process_directory(directory_path, check_database=False):
    """
    Process all CSV files in a directory
    
    Args:
        directory_path: Path to directory containing CSV files
        check_database: Whether to check database for existing data
    """
    print(f"Processing directory: {directory_path}")
    
    if not os.path.exists(directory_path):
        print(f"Error: Directory {directory_path} does not exist!")
        return
    
    # Find all CSV files in directory
    csv_files = []
    for file in os.listdir(directory_path):
        if file.lower().endswith('.csv'):
            csv_files.append(os.path.join(directory_path, file))
    
    if not csv_files:
        print("No CSV files found in directory!")
        return
    
    print(f"Found {len(csv_files)} CSV files")
    
    # Process each CSV file
    total_files_processed = 0
    total_rows_processed = 0
    total_rows_skipped = 0
    
    for csv_file in csv_files:
        try:
            processed, skipped = process_csv_file(csv_file, check_database)
            total_rows_processed += processed
            total_rows_skipped += skipped
            total_files_processed += 1
        except Exception as e:
            print(f"Error processing {csv_file}: {e}")
            continue
    
    # Final summary
    print("\n" + "="*50)
    print("DIRECTORY PROCESSING SUMMARY:")
    print(f"Files processed: {total_files_processed}/{len(csv_files)}")
    print(f"Total rows inserted: {total_rows_processed}")
    print(f"Total rows skipped: {total_rows_skipped}")
    print("="*50)

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # Check if directory path is provided
        if os.path.isdir(sys.argv[1]):
            # Process directory
            check_db = len(sys.argv) > 2 and sys.argv[2].lower() == '--check-db'
            process_directory(sys.argv[1], check_db)
        else:
            # Process single file
            input_file = sys.argv[1]
            check_db = len(sys.argv) > 2 and sys.argv[2].lower() == '--check-db'
            
            if os.path.exists(input_file):
                separate_csv_by_category(input_file, check_db)
            else:
                print(f"Error: File {input_file} not found!")
                print("Please make sure the CSV file is in the same directory as this script.")
    else:
        # Default behavior - process the original file
        input_file = "missing_dates_report_filter.csv"
        
        if os.path.exists(input_file):
            print("Usage options:")
            print("1. python separate_csv.py                                    # Process default file")
            print("2. python separate_csv.py <csv_file>                        # Process specific CSV file")
            print("3. python separate_csv.py <directory>                       # Process all CSV files in directory")
            print("4. python separate_csv.py <csv_file> --check-db             # Process file with database checking")
            print("5. python separate_csv.py <directory> --check-db            # Process directory with database checking")
            print("\nProcessing default file...")
            separate_csv_by_category(input_file)
        else:
            print(f"Error: File {input_file} not found!")
            print("Please make sure the CSV file is in the same directory as this script.")
            print("\nUsage: python separate_csv.py <csv_file_or_directory> [--check-db]") 