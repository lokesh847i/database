# NIFTY CASH OHLC Data Retrieval

This project provides Python scripts to connect to your MySQL database and retrieve OHLC (Open, High, Low, Close) data from the `nifty_cash` table for specific dates and times.

## Database Configuration

- **Host**: 106.51.63.60
- **User**: mahesh
- **Password**: mahesh_123
- **Database**: historicaldb
- **Table**: nifty_cash

## Installation

1. Install the required dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Option 1: Interactive Script (`database_ohlc.py`)

Run the interactive script that prompts for date and time inputs:

```bash
python database_ohlc.py
```

This script will:
- Connect to your database
- Ask for a date (YYYY-MM-DD format)
- Ask for a time (HH:MM:SS format, optional)
- Display the OHLC data
- Provide an option to save data to CSV

### Option 2: Simple Script (`simple_ohlc.py`)

Use the simple script for quick data retrieval:

```python
from simple_ohlc import get_ohlc_data

# Get data for entire day
data = get_ohlc_data("2024-01-15")

# Get data for specific time
data = get_ohlc_data("2024-01-15", "09:15:00")
```

## Features

- **Date and Time Filtering**: Retrieve data for specific dates and times
- **OHLC Summary**: Get aggregated OHLC data
- **CSV Export**: Save retrieved data to CSV files
- **Error Handling**: Comprehensive error handling for database connections
- **Data Validation**: Input validation for date and time formats

## Example Output

```
✅ Successfully connected to the database!

==================================================
📊 NIFTY CASH OHLC DATA RETRIEVAL
==================================================
Enter date (YYYY-MM-DD) or 'quit' to exit: 2024-01-15
Enter time (HH:MM:SS) or press Enter for entire day: 09:15:00

🔍 Fetching data for date: 2024-01-15 and time: 09:15:00
✅ Found 5 records for date: 2024-01-15 and time: 09:15:00

📋 Raw Data:
   id  timestamp    open    high     low   close  volume
0   1  2024-01-15  18500   18550  18480  18520    1000
1   2  2024-01-15  18520   18580  18510  18560    1200
...

📊 OHLC Summary:
         date     time   open   high    low  close  volume
0  2024-01-15  09:15:00  18500  18580  18480  18560    2200

💾 Save data to CSV? (y/n): y
✅ Data saved to nifty_cash_2024-01-15_09-15-00.csv
```

## Troubleshooting

1. **Connection Error**: Make sure your database server is running and accessible
2. **Authentication Error**: Verify your username and password
3. **Table Not Found**: Ensure the `nifty_cash` table exists in your database
4. **No Data Found**: Check if data exists for the specified date/time

## File Structure

```
database_chart/
├── database_ohlc.py      # Interactive OHLC data retrieval
├── simple_ohlc.py        # Simple function for data retrieval
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Dependencies

- `mysql-connector-python`: MySQL database connection
- `pandas`: Data manipulation and analysis
- `python-dotenv`: Environment variable management (optional) 