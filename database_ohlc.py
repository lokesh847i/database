import mysql.connector
import pandas as pd
from datetime import datetime, timedelta
import sys

def convert_date_to_db_format(date_str):
    """
    Convert YYYY-MM-DD format to YYMMDD format for database
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%y%m%d')
    except ValueError:
        return None

def convert_time_to_db_format(time_str):
    """
    Convert HH:MM:SS format to seconds since midnight for database
    """
    try:
        time_obj = datetime.strptime(time_str, '%H:%M:%S')
        return time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
    except ValueError:
        return None

def convert_db_time_to_readable(seconds):
    """
    Convert seconds since midnight to HH:MM:SS format
    """
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    secs = seconds % 60
    return f"{hours:02d}:{minutes:02d}:{secs:02d}"

def convert_db_date_to_readable(date_int):
    """
    Convert YYMMDD format to YYYY-MM-DD format
    """
    try:
        date_str = str(date_int)
        if len(date_str) == 6:
            year = "20" + date_str[:2]
            month = date_str[2:4]
            day = date_str[4:6]
            return f"{year}-{month}-{day}"
        return str(date_int)
    except:
        return str(date_int)

class DatabaseOHLC:
    def __init__(self, host, user, password, database):
        """
        Initialize database connection parameters
        """
        self.host = host
        self.user = user
        self.password = password
        self.database = database
        self.connection = None
        self.cursor = None
    
    def connect(self):
        """
        Establish connection to MySQL database
        """
        try:
            self.connection = mysql.connector.connect(
                host=self.host,
                user=self.user,
                password=self.password,
                database=self.database
            )
            self.cursor = self.connection.cursor()
            print("✅ Successfully connected to the database!")
            return True
        except mysql.connector.Error as err:
            print(f"❌ Error connecting to database: {err}")
            return False
    
    def disconnect(self):
        """
        Close database connection
        """
        if self.cursor:
            self.cursor.close()
        if self.connection:
            self.connection.close()
        print("🔌 Database connection closed.")
    
    def get_ohlc_data(self, date, time=None):
        """
        Retrieve OHLC data for a specific date and time from nifty_cash table
        
        Args:
            date (str): Date in 'YYYY-MM-DD' format
            time (str): Time in 'HH:MM:SS' format (optional)
        """
        try:
            # Convert input formats to database formats
            db_date = convert_date_to_db_format(date)
            if db_date is None:
                print(f"❌ Invalid date format: {date}. Please use YYYY-MM-DD format.")
                return None
            
            if time:
                db_time = convert_time_to_db_format(time)
                if db_time is None:
                    print(f"❌ Invalid time format: {time}. Please use HH:MM:SS format.")
                    return None
                
                # Query for specific date and time
                query = """
                SELECT * FROM nifty_cash 
                WHERE date = %s AND time = %s
                ORDER BY date, time
                """
                self.cursor.execute(query, (db_date, db_time))
            else:
                # Query for entire date
                query = """
                SELECT * FROM nifty_cash 
                WHERE date = %s
                ORDER BY date, time
                """
                self.cursor.execute(query, (db_date,))
            
            # Fetch all results
            results = self.cursor.fetchall()
            
            if not results:
                print(f"❌ No data found for date: {date}" + (f" and time: {time}" if time else ""))
                return None
            
            # Get column names
            columns = [desc[0] for desc in self.cursor.description]
            
            # Create DataFrame
            df = pd.DataFrame(results, columns=columns)
            
            # Convert database formats back to readable formats for display
            if 'date' in df.columns:
                df['date_readable'] = df['date'].apply(convert_db_date_to_readable)
            if 'time' in df.columns:
                df['time_readable'] = df['time'].apply(convert_db_time_to_readable)
            
            print(f"✅ Found {len(df)} records for date: {date}" + (f" and time: {time}" if time else ""))
            return df
            
        except mysql.connector.Error as err:
            print(f"❌ Error executing query: {err}")
            return None
    
    def get_ohlc_summary(self, date, time=None):
        """
        Get OHLC summary for a specific date and time
        """
        try:
            # Convert input formats to database formats
            db_date = convert_date_to_db_format(date)
            if db_date is None:
                print(f"❌ Invalid date format: {date}. Please use YYYY-MM-DD format.")
                return None
            
            if time:
                db_time = convert_time_to_db_format(time)
                if db_time is None:
                    print(f"❌ Invalid time format: {time}. Please use HH:MM:SS format.")
                    return None
                
                # Query for specific date and time with OHLC calculation
                query = """
                SELECT 
                    date,
                    time,
                    MIN(open) as open,
                    MAX(high) as high,
                    MIN(low) as low,
                    MAX(close) as close
                FROM nifty_cash 
                WHERE date = %s AND time = %s
                GROUP BY date, time
                """
                self.cursor.execute(query, (db_date, db_time))
            else:
                # Query for entire date with OHLC calculation
                query = """
                SELECT 
                    date,
                    MIN(open) as open,
                    MAX(high) as high,
                    MIN(low) as low,
                    MAX(close) as close
                FROM nifty_cash 
                WHERE date = %s
                GROUP BY date
                """
                self.cursor.execute(query, (db_date,))
            
            results = self.cursor.fetchall()
            
            if not results:
                print(f"❌ No OHLC data found for date: {date}" + (f" and time: {time}" if time else ""))
                return None
            
            # Get column names
            columns = [desc[0] for desc in self.cursor.description]
            
            # Create DataFrame
            df = pd.DataFrame(results, columns=columns)
            
            # Convert database formats back to readable formats for display
            if 'date' in df.columns:
                df['date_readable'] = df['date'].apply(convert_db_date_to_readable)
            if 'time' in df.columns:
                df['time_readable'] = df['time'].apply(convert_db_time_to_readable)
            
            print(f"✅ OHLC Summary for date: {date}" + (f" and time: {time}" if time else ""))
            return df
            
        except mysql.connector.Error as err:
            print(f"❌ Error executing OHLC query: {err}")
            return None

def main():
    """
    Main function to run the OHLC data retrieval
    """
    # Database connection parameters
    host = "106.51.63.60"
    user = "mahesh"
    password = "mahesh_123"
    database = "historicaldb"
    
    # Create database connection
    db = DatabaseOHLC(host, user, password, database)
    
    if not db.connect():
        print("❌ Failed to connect to database. Exiting...")
        sys.exit(1)
    
    try:
        while True:
            print("\n" + "="*50)
            print("📊 NIFTY CASH OHLC DATA RETRIEVAL")
            print("="*50)
            
            # Get user input
            date_input = input("Enter date (YYYY-MM-DD) or 'quit' to exit: ").strip()
            
            if date_input.lower() == 'quit':
                break
            
            # Validate date format
            try:
                datetime.strptime(date_input, '%Y-%m-%d')
            except ValueError:
                print("❌ Invalid date format. Please use YYYY-MM-DD format.")
                continue
            
            # Ask for time (optional)
            time_input = input("Enter time (HH:MM:SS) or press Enter for entire day: ").strip()
            
            if time_input:
                try:
                    datetime.strptime(time_input, '%H:%M:%S')
                except ValueError:
                    print("❌ Invalid time format. Please use HH:MM:SS format.")
                    continue
            
            print(f"\n🔍 Fetching data for date: {date_input}" + (f" and time: {time_input}" if time_input else ""))
            
            # Get OHLC data
            ohlc_data = db.get_ohlc_data(date_input, time_input if time_input else None)
            
            if ohlc_data is not None:
                print("\n📋 Raw Data:")
                print(ohlc_data.head(10))  # Show first 10 rows
                
                if len(ohlc_data) > 10:
                    print(f"... and {len(ohlc_data) - 10} more records")
                
                # Get OHLC summary
                ohlc_summary = db.get_ohlc_summary(date_input, time_input if time_input else None)
                
                if ohlc_summary is not None:
                    print("\n📊 OHLC Summary:")
                    print(ohlc_summary)
                
                # Save to CSV option
                save_csv = input("\n💾 Save data to CSV? (y/n): ").strip().lower()
                if save_csv == 'y':
                    filename = f"nifty_cash_{date_input}"
                    if time_input:
                        filename += f"_{time_input.replace(':', '-')}"
                    filename += ".csv"
                    
                    ohlc_data.to_csv(filename, index=False)
                    print(f"✅ Data saved to {filename}")
            
            print("\n" + "-"*50)
    
    except KeyboardInterrupt:
        print("\n\n👋 Goodbye!")
    finally:
        db.disconnect()

if __name__ == "__main__":
    main() 