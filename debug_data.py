import mysql.connector
import pandas as pd
from datetime import datetime

def debug_database_data():
    """
    Debug script to understand the exact data formats and find available data
    """
    host = "106.51.63.60"
    user = "mahesh"
    password = "mahesh_123"
    database = "historicaldb"
    
    try:
        print("🔍 Debugging nifty_cash table data...")
        print("="*60)
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # 1. Check table structure
        print("1. Table Structure:")
        cursor.execute("DESCRIBE nifty_cash")
        columns = cursor.fetchall()
        for col in columns:
            print(f"   {col[0]} - {col[1]}")
        print()
        
        # 2. Get sample data to understand formats
        print("2. Sample Data (first 10 records):")
        cursor.execute("SELECT * FROM nifty_cash ORDER BY date, time LIMIT 10")
        sample_data = cursor.fetchall()
        
        # Get column names
        cursor.execute("SELECT * FROM nifty_cash LIMIT 0")
        column_names = [desc[0] for desc in cursor.description]
        
        df = pd.DataFrame(sample_data, columns=column_names)
        print(df.to_string(index=False))
        print()
        
        # 3. Check specific date formats
        print("3. Date Format Analysis:")
        cursor.execute("SELECT DISTINCT date FROM nifty_cash ORDER BY date LIMIT 5")
        dates = cursor.fetchall()
        for date in dates:
            date_val = date[0]
            print(f"   Database date: {date_val} (type: {type(date_val)})")
            
            # Try to convert to readable format
            try:
                if isinstance(date_val, int):
                    date_str = str(date_val)
                    if len(date_str) == 6:
                        year = "20" + date_str[:2]
                        month = date_str[2:4]
                        day = date_str[4:6]
                        readable = f"{year}-{month}-{day}"
                        print(f"   Converted to: {readable}")
                    else:
                        print(f"   Could not convert: {date_str}")
                else:
                    print(f"   String format: {date_val}")
            except Exception as e:
                print(f"   Error converting: {e}")
        print()
        
        # 4. Check specific time formats
        print("4. Time Format Analysis:")
        cursor.execute("SELECT DISTINCT time FROM nifty_cash ORDER BY time LIMIT 5")
        times = cursor.fetchall()
        for time in times:
            time_val = time[0]
            print(f"   Database time: {time_val} (type: {type(time_val)})")
            
            # Try to convert to readable format
            try:
                if isinstance(time_val, int):
                    hours = time_val // 3600
                    minutes = (time_val % 3600) // 60
                    secs = time_val % 60
                    readable = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                    print(f"   Converted to: {readable}")
                else:
                    print(f"   String format: {time_val}")
            except Exception as e:
                print(f"   Error converting: {e}")
        print()
        
        # 5. Test specific date conversion
        print("5. Testing 2018-01-01 conversion:")
        test_date = "2018-01-01"
        try:
            date_obj = datetime.strptime(test_date, '%Y-%m-%d')
            db_format = date_obj.strftime('%y%m%d')
            print(f"   Input: {test_date}")
            print(f"   Converted to: {db_format}")
            
            # Check if this date exists
            cursor.execute("SELECT COUNT(*) FROM nifty_cash WHERE date = %s", (db_format,))
            count = cursor.fetchone()[0]
            print(f"   Records found: {count}")
            
            if count > 0:
                cursor.execute("SELECT DISTINCT time FROM nifty_cash WHERE date = %s ORDER BY time LIMIT 10", (db_format,))
                times = cursor.fetchall()
                print("   Available times:")
                for time in times:
                    time_val = time[0]
                    if isinstance(time_val, int):
                        hours = time_val // 3600
                        minutes = (time_val % 3600) // 60
                        secs = time_val % 60
                        readable = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                        print(f"     {time_val} -> {readable}")
                    else:
                        print(f"     {time_val}")
        except Exception as e:
            print(f"   Error: {e}")
        print()
        
        # 6. Test specific time conversion
        print("6. Testing 09:25:59 conversion:")
        test_time = "09:25:59"
        try:
            time_obj = datetime.strptime(test_time, '%H:%M:%S')
            db_format = time_obj.hour * 3600 + time_obj.minute * 60 + time_obj.second
            print(f"   Input: {test_time}")
            print(f"   Converted to: {db_format}")
            
            # Check if this time exists for 2018-01-01
            db_date = "180101"
            cursor.execute("SELECT COUNT(*) FROM nifty_cash WHERE date = %s AND time = %s", (db_date, db_format))
            count = cursor.fetchone()[0]
            print(f"   Records found for {test_date} at {test_time}: {count}")
            
        except Exception as e:
            print(f"   Error: {e}")
        print()
        
        # 7. Find closest available times
        print("7. Finding closest available times for 2018-01-01:")
        db_date = "180101"
        target_time = 9 * 3600 + 25 * 60 + 59  # 09:25:59 in seconds
        
        cursor.execute("SELECT time FROM nifty_cash WHERE date = %s ORDER BY ABS(time - %s) LIMIT 5", (db_date, target_time))
        closest_times = cursor.fetchall()
        
        if closest_times:
            print("   Closest available times:")
            for time in closest_times:
                time_val = time[0]
                if isinstance(time_val, int):
                    hours = time_val // 3600
                    minutes = (time_val % 3600) // 60
                    secs = time_val % 60
                    readable = f"{hours:02d}:{minutes:02d}:{secs:02d}"
                    diff = abs(time_val - target_time)
                    print(f"     {time_val} -> {readable} (diff: {diff} seconds)")
        else:
            print("   No data found for 2018-01-01")
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
    except Exception as e:
        print(f"❌ Error: {e}")
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == "__main__":
    debug_database_data() 