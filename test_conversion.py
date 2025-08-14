from datetime import datetime

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

def test_conversions():
    """
    Test the conversion functions
    """
    print("🧪 Testing Conversion Functions")
    print("="*40)
    
    # Test date conversion
    print("1. Date Conversion Tests:")
    test_dates = ["2018-01-01", "2020-12-31", "2019-06-15"]
    for date in test_dates:
        db_format = convert_date_to_db_format(date)
        readable = convert_db_date_to_readable(db_format)
        print(f"   {date} -> {db_format} -> {readable}")
    print()
    
    # Test time conversion
    print("2. Time Conversion Tests:")
    test_times = ["09:15:00", "09:25:59", "15:30:45", "23:59:59"]
    for time in test_times:
        db_format = convert_time_to_db_format(time)
        readable = convert_db_time_to_readable(db_format)
        print(f"   {time} -> {db_format} -> {readable}")
    print()
    
    # Test specific case
    print("3. Specific Test Case (2018-01-01 09:25:59):")
    date = "2018-01-01"
    time = "09:25:59"
    
    db_date = convert_date_to_db_format(date)
    db_time = convert_time_to_db_format(time)
    
    print(f"   Date: {date} -> {db_date}")
    print(f"   Time: {time} -> {db_time}")
    
    # Verify reverse conversion
    readable_date = convert_db_date_to_readable(db_date)
    readable_time = convert_db_time_to_readable(db_time)
    
    print(f"   Reverse Date: {db_date} -> {readable_date}")
    print(f"   Reverse Time: {db_time} -> {readable_time}")
    
    # Check if conversions are correct
    date_correct = date == readable_date
    time_correct = time == readable_time
    
    print(f"   Date conversion correct: {date_correct}")
    print(f"   Time conversion correct: {time_correct}")

if __name__ == "__main__":
    test_conversions() 