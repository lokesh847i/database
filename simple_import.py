import pandas as pd
import mysql.connector
import csv
import os
from datetime import datetime
import re

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

class DateParser:
    def __init__(self):
        self.month_map = {
            'JAN': 1, 'FEB': 2, 'MAR': 3, 'APR': 4, 'MAY': 5, 'JUN': 6,
            'JUL': 7, 'AUG': 8, 'SEP': 9, 'OCT': 10, 'NOV': 11, 'DEC': 12
        }
    
    def parse_expiry(self, expiry_str):
        """Parse expiry in various formats and convert to YYMMDD integer"""
        try:
            if not expiry_str or str(expiry_str).strip() == '':
                return 0
            
            expiry_str = str(expiry_str).strip().upper()
            
            # Handle DDMMMYY format (27MAR25)
            if len(expiry_str) == 7 and expiry_str[:2].isdigit() and expiry_str[5:].isdigit():
                day = expiry_str[:2]
                month_str = expiry_str[2:5]
                year = expiry_str[5:]
                
                if month_str in self.month_map:
                    month = self.month_map[month_str]
                    return int(year) * 10000 + month * 100 + int(day)
            
            # If it's already a 6-digit number (YYMMDD format), return as integer
            if expiry_str.isdigit() and len(expiry_str) == 6:
                return int(expiry_str)
                
            # If it's an 8-digit number (YYYYMMDD format), convert to YYMMDD
            if expiry_str.isdigit() and len(expiry_str) == 8:
                year = int(expiry_str[:4]) % 100
                month = int(expiry_str[4:6])
                day = int(expiry_str[6:8])
                return year * 10000 + month * 100 + day
            
            # Handle DD-MM-YYYY or YYYY-MM-DD format
            if '-' in expiry_str:
                parts = expiry_str.split('-')
                if len(parts) == 3:
                    if len(parts[2]) == 4:  # DD-MM-YYYY
                        day, month, year = parts
                        year_short = int(year) % 100
                        return year_short * 10000 + int(month) * 100 + int(day)
                    elif len(parts[0]) == 4:  # YYYY-MM-DD
                        year, month, day = parts
                        year_short = int(year) % 100
                        return year_short * 10000 + int(month) * 100 + int(day)
                    else:  # DD-MMM-YY or similar
                        day, month_str, year = parts
                        month_str = month_str.upper()
                        
                        if month_str in self.month_map:
                            month = self.month_map[month_str]
                            year_short = int(year) % 100 if len(year) == 4 or int(year) > 99 else int(year)
                            return year_short * 10000 + month * 100 + int(day)
            
            # Try to convert directly to integer as last resort
            try:
                return int(float(expiry_str))
            except (ValueError, TypeError):
                pass
                
        except Exception as e:
            print(f"Error parsing expiry {expiry_str}: {e}")
        return 0

class CSVImporter:
    def __init__(self):
        self.date_parser = DateParser()
        self.connection = None
        self.cursor = None
        
    def connect_database(self):
        """Connect to MySQL database"""
        try:
            self.connection = mysql.connector.connect(**DB_CONFIG)
            self.cursor = self.connection.cursor()
            print("✓ Connected to database successfully!")
            return True
        except mysql.connector.Error as e:
            print(f"✗ Database connection failed: {e}")
            return False
    
    def disconnect_database(self):
        """Disconnect from database"""
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("✓ Disconnected from database")
    
    def parse_date(self, date_str):
        """Parse date from various formats and convert to YYMMDD integer"""
        try:
            if not date_str or str(date_str).strip() == '':
                return 0
            
            date_str = str(date_str).strip()
            
            # Handle DD-MM-YYYY format (03-03-2025)
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

    def parse_time(self, time_str):
        """Convert time from HH:MM:SS to seconds"""
        try:
            if not time_str or time_str.strip() == '':
                return 0
                
            time_str = str(time_str).strip()
            
            # Handle HH:MM:SS format
            if ':' in time_str:
                parts = time_str.split(':')
                if len(parts) >= 2:
                    hours = int(parts[0])
                    minutes = int(parts[1])
                    seconds = int(parts[2]) if len(parts) == 3 else 0
                    return hours * 3600 + minutes * 60 + seconds
            
            # Handle HHMMSS format (6 digits)
            if time_str.isdigit() and len(time_str) == 6:
                hours = int(time_str[:2])
                minutes = int(time_str[2:4])
                seconds = int(time_str[4:6])
                return hours * 3600 + minutes * 60 + seconds
                
            # Handle already converted seconds
            if time_str.isdigit():
                return int(time_str)
                
        except Exception as e:
            print(f"Error parsing time {time_str}: {e}")
            return 0
        return 0

    def parse_csv_row(self, row, fieldnames):
        """Parse a CSV row and return data dictionary with only existing columns"""
        data_dict = {}
        
        # Field mapping for different CSV formats - only include columns that exist in DB
        field_mappings = {
            'date': ['date', 'Date', 'DATE', 'trade_date', 'trading_date'],
            'time': ['time', 'Time', 'TIME', 'trade_time', 'trading_time'],
            'symbol': ['symbol', 'Symbol', 'SYMBOL', 'instrument', 'scrip'],
            'open': ['open', 'Open', 'OPEN', 'open_price'],
            'high': ['high', 'High', 'HIGH', 'high_price'],
            'low': ['low', 'Low', 'LOW', 'low_price'],
            'close': ['close', 'Close', 'CLOSE', 'close_price', 'ltp']
            # Removed volume, oi, coi, strike, expiry since they don't exist in current DB structure
        }
        
        # Map CSV fields to database fields
        for db_field, csv_variants in field_mappings.items():
            value = None
            for variant in csv_variants:
                if variant in row:
                    value = row[variant]
                    break
            
            if value is not None and str(value).strip():
                if db_field == 'date':
                    data_dict[db_field] = self.parse_date(value)
                elif db_field == 'time':
                    data_dict[db_field] = self.parse_time(value)
                elif db_field == 'symbol':
                    data_dict[db_field] = str(value).strip()
                elif db_field in ['open', 'high', 'low', 'close']:
                    data_dict[db_field] = float(value or 0)
            else:
                # Set default values for missing fields
                if db_field in ['date', 'time']:
                    data_dict[db_field] = 0
                elif db_field in ['open', 'high', 'low', 'close']:
                    data_dict[db_field] = 0.0
                elif db_field == 'symbol':
                    data_dict[db_field] = ''
        
        return data_dict

    def table_exists(self, table_name):
        """Check if a table exists in the database"""
        try:
            self.cursor.execute(f"SHOW TABLES LIKE '{table_name}'")
            result = self.cursor.fetchone()
            return result is not None
        except Exception as e:
            print(f"Error checking table existence: {e}")
            return False

    def create_table_name_from_filename(self, filename):
        """Create table name from CSV filename"""
        base_name = os.path.splitext(os.path.basename(filename))[0]
        
        # Remove '_cash' suffix if present
        if base_name.endswith('_cash'):
            base_name = base_name[:-5]  # Remove '_cash'
        
        # Clean up the name - keep only alphanumeric characters
        clean_name = ''.join(c if c.isalnum() else '_' for c in base_name)
        clean_name = '_'.join(filter(None, clean_name.split('_')))
        
        # Create table name with _cash suffix
        table_name = f"{clean_name}_cash"
        
        return table_name

    def create_cash_table(self, table_name):
        """Create cash table with appropriate schema"""
        create_table_query = f"""
        CREATE TABLE IF NOT EXISTS {table_name} (
            date INT NOT NULL,
            time INT NOT NULL,
            symbol VARCHAR(50) NOT NULL,
            open DECIMAL(10,2) NOT NULL,
            high DECIMAL(10,2) NOT NULL,
            low DECIMAL(10,2) NOT NULL,
            close DECIMAL(10,2) NOT NULL,
            INDEX idx_date (date),
            INDEX idx_symbol (symbol)
        )
        """
        self.cursor.execute(create_table_query)
        self.connection.commit()
        print(f"✓ Table '{table_name}' created/verified")

    def import_csv_file(self, csv_file):
        """Import a single CSV file into its corresponding cash table if it exists"""
        if not os.path.exists(csv_file):
            print(f"✗ CSV file not found: {csv_file}")
            return False
        
        # Create table name from filename
        table_name = self.create_table_name_from_filename(csv_file)
        
        print(f"\n=== Processing: {csv_file} ===")
        print(f"Looking for table: {table_name}")
        
        # Check if table exists
        if not self.table_exists(table_name):
            print(f"⏭️ Skipping {os.path.basename(csv_file)} - table '{table_name}' does not exist")
            return False
        
        print(f"✓ Found table '{table_name}', importing data...")
        
        # Process CSV file
        processed_rows = 0
        skipped_rows = 0
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                csv_reader = csv.DictReader(file)
                fieldnames = csv_reader.fieldnames
                
                print(f"CSV columns: {list(fieldnames)}")
                
                for row_num, row in enumerate(csv_reader, 1):
                    try:
                        # Skip empty rows
                        if not any(row.values()):
                            skipped_rows += 1
                            continue
                        
                        # Parse data
                        data_dict = self.parse_csv_row(row, fieldnames)
                        
                        if not data_dict or not data_dict.get('symbol'):
                            skipped_rows += 1
                            continue
                        
                        # Insert data into the specific cash table
                        columns = ', '.join(data_dict.keys())
                        placeholders = ', '.join(['%s'] * len(data_dict))
                        insert_query = f"""
                        INSERT INTO {table_name} ({columns})
                        VALUES ({placeholders})
                        """
                        
                        self.cursor.execute(insert_query, list(data_dict.values()))
                        processed_rows += 1
                        
                        # Commit every 1000 rows for better performance
                        if processed_rows % 1000 == 0:
                            self.connection.commit()
                            print(f"  Processed {processed_rows} rows...")
                    
                    except Exception as e:
                        print(f"  Error in row {row_num}: {e}")
                        skipped_rows += 1
                        continue
            
            # Final commit
            self.connection.commit()
            
            print(f"✓ Import completed!")
            print(f"  Processed rows: {processed_rows}")
            print(f"  Skipped rows: {skipped_rows}")
            
            return True
            
        except Exception as e:
            print(f"✗ Import failed: {e}")
            self.connection.rollback()
            return False

    def import_multiple_csv_files(self, csv_files):
        """Import multiple CSV files into their corresponding cash tables if they exist"""
        total_files = len(csv_files)
        successful_imports = 0
        skipped_files = 0
        
        print(f"=== Starting import of {total_files} CSV files ===")
        
        for i, csv_file in enumerate(csv_files, 1):
            print(f"\n[{i}/{total_files}] Processing: {os.path.basename(csv_file)}")
            
            if self.import_csv_file(csv_file):
                successful_imports += 1
            else:
                skipped_files += 1
        
        print(f"\n=== Import Summary ===")
        print(f"Successful imports: {successful_imports}")
        print(f"Skipped files: {skipped_files}")
        print(f"Total files processed: {total_files}")
        
        return successful_imports > 0

def main():
    # ========================================
    # CONFIGURE YOUR CSV FILES HERE
    # ========================================
    
    # Import all CSV files from a directory
    directory_path = r"D:\stocks_march\FinalOutput_update\cash\March"
    
    # ========================================
    # CHOOSE YOUR IMPORT METHOD
    # ========================================
    
    importer = CSVImporter()
    
    # Connect to database
    if not importer.connect_database():
        print("Failed to connect to database. Please check your MySQL connection.")
        return
    
    try:
        # Import all CSV files from directory
        if os.path.exists(directory_path):
            all_csv_files = []
            for file in os.listdir(directory_path):
                if file.lower().endswith('.csv'):
                    all_csv_files.append(os.path.join(directory_path, file))
            
            print(f"Found {len(all_csv_files)} CSV files in directory")
            importer.import_multiple_csv_files(all_csv_files)
        else:
            print(f"Directory not found: {directory_path}")
    
    finally:
        importer.disconnect_database()

if __name__ == "__main__":
    main() 