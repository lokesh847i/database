from flask import Flask, render_template, request, jsonify
import mysql.connector
import pandas as pd
import plotly.graph_objects as go
import plotly.utils
import json
from datetime import datetime
import os

app = Flask(__name__)

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
            return None, "Invalid date format. Please use YYYY-MM-DD format."
        
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
            return None, f"No data found for date: {date}"
        
        # Get column names
        columns = [desc[0] for desc in cursor.description]
        
        # Create DataFrame
        df = pd.DataFrame(results, columns=columns)
        
        # Convert database formats back to readable formats
        if 'date' in df.columns:
            df['date_readable'] = df['date'].apply(convert_db_date_to_readable)
        if 'time' in df.columns:
            df['time_readable'] = df['time'].apply(convert_db_time_to_readable)
        
        # Create datetime column for plotting
        df['datetime'] = pd.to_datetime(df['date_readable'] + ' ' + df['time_readable'])
        
        return df, f"Found {len(df)} records for date: {date}"
        
    except mysql.connector.Error as err:
        return None, f"Database error: {err}"
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

def create_interactive_candlestick_chart(df, date):
    """
    Create an interactive candlestick chart using Plotly
    """
    if df is None or len(df) == 0:
        return None
    
    # Create the candlestick chart
    fig = go.Figure(data=[go.Candlestick(
        x=df['datetime'],
        open=df['open'],
        high=df['high'],
        low=df['low'],
        close=df['close'],
        name='NIFTY CASH'
    )])
    
    # Update layout for better appearance
    fig.update_layout(
        title=f'NIFTY CASH - Interactive OHLC Candlestick Chart ({date})',
        yaxis_title='Price',
        xaxis_title='Time',
        template='plotly_white',
        height=600,
        showlegend=True,
        # Enable all interactive features
        dragmode='zoom',
        hovermode='x unified',
        # Add range slider
        xaxis=dict(
            rangeslider=dict(visible=True),
            type='date',
            rangeselector=dict(
                buttons=list([
                    dict(count=1, label="1H", step="hour", stepmode="backward"),
                    dict(count=3, label="3H", step="hour", stepmode="backward"),
                    dict(count=6, label="6H", step="hour", stepmode="backward"),
                    dict(count=1, label="1D", step="day", stepmode="backward"),
                    dict(step="all", label="All")
                ])
            )
        ),
        # Add price statistics as annotations
        annotations=[
            dict(
                x=0.02, y=0.98, xref='paper', yref='paper',
                text=f"Open: {df['open'].iloc[0]:,.0f}<br>High: {df['high'].max():,.0f}<br>Low: {df['low'].min():,.0f}<br>Close: {df['close'].iloc[-1]:,.0f}",
                showarrow=False,
                bgcolor='rgba(255, 255, 255, 0.8)',
                bordercolor='black',
                borderwidth=1
            )
        ]
    )
    
    # Add price change information
    price_change = df['close'].iloc[-1] - df['open'].iloc[0]
    price_change_pct = (price_change / df['open'].iloc[0]) * 100
    change_color = 'green' if price_change >= 0 else 'red'
    
    fig.add_annotation(
        x=0.98, y=0.98, xref='paper', yref='paper',
        text=f"Change: {price_change:+,.0f} ({price_change_pct:+.2f}%)",
        showarrow=False,
        bgcolor=change_color,
        bordercolor='black',
        borderwidth=1,
        font=dict(color='white', size=12)
    )
    
    return fig

@app.route('/')
def index():
    """Main page with date input form"""
    return render_template('index.html')

@app.route('/chart', methods=['POST'])
def get_chart():
    """Generate chart for the given date"""
    date = request.form.get('date')
    
    if not date:
        return jsonify({'error': 'Please provide a date'})
    
    # Get data from database
    df, message = get_ohlc_data_for_date(date)
    
    if df is None:
        return jsonify({'error': message})
    
    # Create interactive chart
    fig = create_interactive_candlestick_chart(df, date)
    
    if fig is None:
        return jsonify({'error': 'Failed to create chart'})
    
    # Convert to JSON for JavaScript
    chart_json = json.dumps(fig, cls=plotly.utils.PlotlyJSONEncoder)
    
    return jsonify({
        'chart': chart_json,
        'message': message,
        'data_points': len(df),
        'date': date
    })

@app.route('/api/data/<date>')
def get_data_api(date):
    """API endpoint to get raw data for a date"""
    df, message = get_ohlc_data_for_date(date)
    
    if df is None:
        return jsonify({'error': message})
    
    # Convert DataFrame to JSON
    data = df.to_dict('records')
    
    return jsonify({
        'data': data,
        'message': message,
        'count': len(df)
    })

@app.route('/api/dates')
def get_available_dates():
    """API endpoint to get available dates"""
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
        
        # Get distinct dates
        query = """
        SELECT DISTINCT date FROM nifty_cash 
        ORDER BY date DESC 
        LIMIT 20
        """
        cursor.execute(query)
        dates = cursor.fetchall()
        
        # Convert to readable format
        readable_dates = []
        for date in dates:
            readable_date = convert_db_date_to_readable(date[0])
            readable_dates.append(readable_date)
        
        return jsonify({
            'dates': readable_dates,
            'count': len(readable_dates)
        })
        
    except mysql.connector.Error as err:
        return jsonify({'error': f"Database error: {err}"})
    finally:
        if 'connection' in locals():
            cursor.close()
            connection.close()

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000) 