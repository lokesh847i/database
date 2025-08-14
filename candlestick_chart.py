import mysql.connector
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import datetime, timedelta
import numpy as np

def convert_date_to_db_format(date_str):
    """
    Convert YYYY-MM-DD format to YYMMDD format for database
    """
    try:
        date_obj = datetime.strptime(date_str, '%Y-%m-%d')
        return date_obj.strftime('%y%m%d')
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

def get_ohlc_data_for_date(date):
    """
    Get OHLC data for a specific date
    """
    host = "106.51.63.60"
    user = "mahesh"
    password = "mahesh_123"
    database = "historicaldb"
    
    try:
        db_date = convert_date_to_db_format(date)
        if db_date is None:
            print(f"Invalid date format: {date}. Please use YYYY-MM-DD format.")
            return None
        
        connection = mysql.connector.connect(
            host=host,
            user=user,
            password=password,
            database=database
        )
        
        cursor = connection.cursor()
        
        # Get all data for the date
        query = """
        SELECT * FROM nifty_cash 
        WHERE date = %s
        ORDER BY time
        """
        cursor.execute(query, (db_date,))
        results = cursor.fetchall()
        
        if not results:
            print(f"❌ No data found for date: {date}")
            return None
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Create DataFrame
        df = pd.DataFrame(results, columns=columns)
        
        # Convert database formats back to readable formats
        if 'date' in df.columns:
            df['date_readable'] = df['date'].apply(convert_db_date_to_readable)
        if 'time' in df.columns:
            df['time_readable'] = df['time'].apply(convert_db_time_to_readable)
        
        print(f"✅ Found {len(df)} records for date: {date}")
        return df
        
    except mysql.connector.Error as err:
        print(f"❌ Database error: {err}")
        return None
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

def create_candlestick_chart(df, date, save_plot=True):
    """
    Create a candlestick chart from OHLC data
    """
    if df is None or len(df) == 0:
        print("❌ No data to plot")
        return
    
    # Create datetime index for proper time series plotting
    df['datetime'] = pd.to_datetime(df['date_readable'] + ' ' + df['time_readable'])
    df.set_index('datetime', inplace=True)
    
    # Set up the plot
    fig, ax = plt.subplots(figsize=(15, 8))
    
    # Define colors for candlesticks
    colors = ['green' if close >= open else 'red' for open, close in zip(df['open'], df['close'])]
    
    # Plot candlesticks
    for i, (idx, row) in enumerate(df.iterrows()):
        # Calculate candlestick dimensions
        open_price = row['open']
        close_price = row['close']
        high_price = row['high']
        low_price = row['low']
        
        # Determine color
        color = 'green' if close_price >= open_price else 'red'
        edge_color = 'darkgreen' if close_price >= open_price else 'darkred'
        
        # Plot the body (rectangle)
        body_height = abs(close_price - open_price)
        body_bottom = min(open_price, close_price)
        
        # Plot the wick (line)
        ax.plot([i, i], [low_price, high_price], color=edge_color, linewidth=1)
        
        # Plot the body
        if body_height > 0:
            ax.bar(i, body_height, bottom=body_bottom, color=color, 
                   edgecolor=edge_color, linewidth=1, width=0.8)
        else:
            # Doji (open = close)
            ax.plot([i-0.4, i+0.4], [open_price, open_price], color=edge_color, linewidth=2)
    
    # Customize the plot
    ax.set_title(f'NIFTY CASH - OHLC Candlestick Chart ({date})', fontsize=16, fontweight='bold')
    ax.set_xlabel('Time', fontsize=12)
    ax.set_ylabel('Price', fontsize=12)
    ax.grid(True, alpha=0.3)
    
    # Set x-axis labels (show every nth time point to avoid crowding)
    n_points = len(df)
    if n_points > 20:
        step = max(1, n_points // 20)
        x_ticks = range(0, n_points, step)
        x_labels = [df.index[i].strftime('%H:%M') for i in x_ticks]
    else:
        x_ticks = range(n_points)
        x_labels = [df.index[i].strftime('%H:%M') for i in x_ticks]
    
    ax.set_xticks(x_ticks)
    ax.set_xticklabels(x_labels, rotation=45)
    
    # Add price statistics
    stats_text = f"""
    Open: {df['open'].iloc[0]:,.0f}
    High: {df['high'].max():,.0f}
    Low: {df['low'].min():,.0f}
    Close: {df['close'].iloc[-1]:,.0f}
    Volume: {len(df)} intervals
    """
    
    # Position the stats text
    ax.text(0.02, 0.98, stats_text, transform=ax.transAxes, 
            verticalalignment='top', bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    # Adjust layout
    plt.tight_layout()
    
    # Save the plot
    if save_plot:
        filename = f"nifty_candlestick_{date.replace('-', '_')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Chart saved as: {filename}")
    
    # Show the plot
    plt.show()

def create_summary_chart(df, date, save_plot=True):
    """
    Create a summary chart showing OHLC for the entire day
    """
    if df is None or len(df) == 0:
        print("❌ No data to plot")
        return
    
    # Calculate daily OHLC
    daily_open = df['open'].iloc[0]
    daily_high = df['high'].max()
    daily_low = df['low'].min()
    daily_close = df['close'].iloc[-1]
    
    # Create the plot
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 10))
    
    # Plot 1: Price movement throughout the day
    df['datetime'] = pd.to_datetime(df['date_readable'] + ' ' + df['time_readable'])
    df.set_index('datetime', inplace=True)
    
    ax1.plot(df.index, df['close'], label='Close Price', linewidth=2, color='blue')
    ax1.fill_between(df.index, df['low'], df['high'], alpha=0.3, color='lightblue', label='High-Low Range')
    ax1.axhline(y=daily_open, color='green', linestyle='--', label=f'Open: {daily_open:,.0f}')
    ax1.axhline(y=daily_close, color='red', linestyle='--', label=f'Close: {daily_close:,.0f}')
    
    ax1.set_title(f'NIFTY CASH - Daily Price Movement ({date})', fontsize=14, fontweight='bold')
    ax1.set_ylabel('Price', fontsize=12)
    ax1.legend()
    ax1.grid(True, alpha=0.3)
    
    # Format x-axis
    ax1.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax1.xaxis.set_major_locator(mdates.MinuteLocator(interval=30))
    plt.setp(ax1.xaxis.get_majorticklabels(), rotation=45)
    
    # Plot 2: OHLC Bar Chart
    categories = ['Open', 'High', 'Low', 'Close']
    values = [daily_open, daily_high, daily_low, daily_close]
    colors = ['green', 'blue', 'orange', 'red']
    
    bars = ax2.bar(categories, values, color=colors, alpha=0.7)
    ax2.set_title('Daily OHLC Summary', fontsize=14, fontweight='bold')
    ax2.set_ylabel('Price', fontsize=12)
    ax2.grid(True, alpha=0.3)
    
    # Add value labels on bars
    for bar, value in zip(bars, values):
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height + height*0.01,
                f'{value:,.0f}', ha='center', va='bottom', fontweight='bold')
    
    # Add price change information
    price_change = daily_close - daily_open
    price_change_pct = (price_change / daily_open) * 100
    change_color = 'green' if price_change >= 0 else 'red'
    
    change_text = f"Change: {price_change:+,.0f} ({price_change_pct:+.2f}%)"
    ax2.text(0.5, 0.95, change_text, transform=ax2.transAxes, 
             ha='center', va='top', fontsize=12, fontweight='bold',
             bbox=dict(boxstyle='round', facecolor=change_color, alpha=0.3))
    
    plt.tight_layout()
    
    # Save the plot
    if save_plot:
        filename = f"nifty_summary_{date.replace('-', '_')}.png"
        plt.savefig(filename, dpi=300, bbox_inches='tight')
        print(f"📊 Summary chart saved as: {filename}")
    
    # Show the plot
    plt.show()

def main():
    """
    Main function to run the candlestick chart generation
    """
    print("📊 NIFTY CASH CANDLESTICK CHART GENERATOR")
    print("="*50)
    
    while True:
        print("\nOptions:")
        print("1. Generate candlestick chart for a date")
        print("2. Generate summary chart for a date")
        print("3. Show available dates")
        print("4. Exit")
        
        choice = input("\nEnter your choice (1-4): ").strip()
        
        if choice == "1":
            date = input("Enter date (YYYY-MM-DD): ").strip()
            print(f"\n🔍 Fetching data for {date}...")
            
            df = get_ohlc_data_for_date(date)
            if df is not None:
                print(f"\n📈 Generating candlestick chart...")
                create_candlestick_chart(df, date)
        
        elif choice == "2":
            date = input("Enter date (YYYY-MM-DD): ").strip()
            print(f"\n🔍 Fetching data for {date}...")
            
            df = get_ohlc_data_for_date(date)
            if df is not None:
                print(f"\n📈 Generating summary chart...")
                create_summary_chart(df, date)
        
        elif choice == "3":
            # Show some sample dates
            sample_dates = ["2018-01-01", "2018-01-02", "2018-01-03"]
            print("\n📅 Sample dates with data:")
            for sample_date in sample_dates:
                df = get_ohlc_data_for_date(sample_date)
                if df is not None:
                    print(f"   ✅ {sample_date} - {len(df)} records")
                else:
                    print(f"   ❌ {sample_date} - No data")
        
        elif choice == "4":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice. Please try again.")

if __name__ == "__main__":
    main() 