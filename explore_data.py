import mysql.connector
import pandas as pd
from datetime import datetime

def explore_nifty_cash_data():
    """
    Explore the nifty_cash table to see what data is available
    """
    # Database connection parameters
    host = "106.51.63.60"
    user = "mahesh"
    password = "mahesh_123"
    database = "historicaldb"
    
    try:
        # Connect to database
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        print("🔍 Exploring nifty_cash table...")
        print("="*50)
        
        # 1. Check table structure
        print("1. Table Structure:")
        cursor.execute("DESCRIBE nifty_cash")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[0]} - {col[1]}")
        print()
        
        # 2. Get total number of records
        print("2. Total Records:")
        cursor.execute("SELECT COUNT(*) FROM nifty_cash")
        total_records = cursor.fetchone()[0]
        print(f"   Total records: {total_records:,}")
        print()
        
        # 3. Get date range
        print("3. Date Range:")
        cursor.execute("SELECT MIN(date), MAX(date) FROM nifty_cash")
        date_range = cursor.fetchone()
        print(f"   From: {date_range[0]}")
        print(f"   To: {date_range[1]}")
        print()
        
        # 4. Get sample of available dates
        print("4. Sample Available Dates:")
        cursor.execute("SELECT DISTINCT date FROM nifty_cash ORDER BY date LIMIT 10")
        sample_dates = cursor.fetchall()
        for date in sample_dates:
            print(f"   {date[0]}")
        print()
        
        # 5. Get sample of available times for a specific date
        if sample_dates:
            sample_date = sample_dates[0][0]
            print(f"5. Sample Times for {sample_date}:")
            cursor.execute("SELECT DISTINCT time FROM nifty_cash WHERE date = %s ORDER BY time LIMIT 10", (sample_date,))
            sample_times = cursor.fetchall()
            for time in sample_times:
                print(f"   {time[0]}")
            print()
        
        # 6. Get sample data
        print("6. Sample Data (first 5 records):")
        cursor.execute("SELECT * FROM nifty_cash ORDER BY date, time LIMIT 5")
        sample_data = cursor.fetchall()
        
        # Get column names
        cursor.execute("SELECT * FROM nifty_cash LIMIT 0")
        columns = [desc[0] for desc in cursor.description]
        
        # Create DataFrame for better display
        df = pd.DataFrame(sample_data, columns=columns)
        print(df.to_string(index=False))
        print()
        
        # 7. Check for data on specific date (2018-01-01)
        print("7. Checking for data on 2018-01-01:")
        cursor.execute("SELECT COUNT(*) FROM nifty_cash WHERE date = '2018-01-01'")
        count_2018_01_01 = cursor.fetchone()[0]
        print(f"   Records for 2018-01-01: {count_2018_01_01}")
        
        if count_2018_01_01 > 0:
            cursor.execute("SELECT DISTINCT time FROM nifty_cash WHERE date = '2018-01-01' ORDER BY time LIMIT 10")
            times_2018_01_01 = cursor.fetchall()
            print("   Available times:")
            for time in times_2018_01_01:
                print(f"     {time[0]}")
        print()
        
        # 8. Get recent data
        print("8. Most Recent Data:")
        cursor.execute("SELECT * FROM nifty_cash ORDER BY date DESC, time DESC LIMIT 3")
        recent_data = cursor.fetchall()
        df_recent = pd.DataFrame(recent_data, columns=columns)
        print(df_recent.to_string(index=False))
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

def find_available_dates():
    """
    Find dates with data in the database
    """
    host = "106.51.63.60"
    user = "mahesh"
    password = "mahesh_123"
    database = "historicaldb"
    
    try:
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        print("📅 Available Dates with Data:")
        print("="*30)
        
        # Get all dates with data
        cursor.execute("SELECT DISTINCT date FROM nifty_cash ORDER BY date")
        dates = cursor.fetchall()
        
        for i, date in enumerate(dates, 1):
            print(f"{i:3d}. {date[0]}")
            
            if i % 20 == 0:  # Show 20 dates at a time
                input("Press Enter to continue...")
        
        print(f"\nTotal dates with data: {len(dates)}")
        
    except mysql.connector.Error as err:
        print(f"❌ Error: {err}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    print("Choose an option:")
    print("1. Explore table structure and sample data")
    print("2. List all available dates")
    
    choice = input("Enter your choice (1 or 2): ").strip()
    
    if choice == "1":
        explore_nifty_cash_data()
    elif choice == "2":
        find_available_dates()
    else:
        print("Invalid choice. Running exploration...")
        explore_nifty_cash_data() 