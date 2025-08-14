# NIFTY CASH - Interactive Web Application

A modern web application for viewing interactive candlestick charts of NIFTY CASH OHLC data with advanced features like zooming, panning, and time range selection.

## 🚀 Features

### Interactive Chart Features
- ✅ **Zoom in/out** with mouse wheel
- ✅ **Pan** by dragging the chart
- ✅ **Hover** for detailed price information
- ✅ **Range slider** for time selection
- ✅ **Time range selector** (1H, 3H, 6H, 1D, All)
- ✅ **Reset to full view**
- ✅ **Download chart** as PNG
- ✅ **Real-time price statistics**

### Web Interface Features
- ✅ **Modern responsive design**
- ✅ **Date picker** for easy date selection
- ✅ **Quick date buttons** for recent dates
- ✅ **Loading animations**
- ✅ **Error handling** and success messages
- ✅ **Mobile-friendly** interface

## 📋 Requirements

Install the required dependencies:

```bash
pip install -r requirements.txt
```

## 🏃‍♂️ How to Run

### 1. Start the Web Server

```bash
python app.py
```

### 2. Access the Application

Open your web browser and go to:
```
http://localhost:5000
```

### 3. Use the Application

1. **Select a date** using the date picker
2. **Click "Generate Chart"** or press Enter
3. **Interact with the chart**:
   - Zoom with mouse wheel
   - Pan by dragging
   - Use range slider
   - Hover for details
   - Download chart

## 🎯 Usage Examples

### Basic Usage
1. Select date: `2018-01-01`
2. Click "Generate Chart"
3. View interactive candlestick chart

### Advanced Interactions
- **Zoom**: Use mouse wheel to zoom in/out
- **Pan**: Click and drag to move around
- **Time Range**: Use buttons (1H, 3H, 6H, 1D, All)
- **Range Slider**: Drag the bottom slider to select time range
- **Hover**: Move mouse over candles for detailed info
- **Download**: Click camera icon to save as PNG

## 📊 Chart Features

### Candlestick Display
- **Green candles**: Bullish (close ≥ open)
- **Red candles**: Bearish (close < open)
- **Wicks**: Show high/low range
- **Bodies**: Show open/close range

### Price Statistics
- **Open**: First price of the day
- **High**: Highest price of the day
- **Low**: Lowest price of the day
- **Close**: Last price of the day
- **Change**: Price change and percentage

## 🔧 API Endpoints

### Chart Generation
```
POST /chart
Content-Type: application/x-www-form-urlencoded

date=2018-01-01
```

### Data API
```
GET /api/data/2018-01-01
```

### Available Dates
```
GET /api/dates
```

## 🎨 Customization

### Styling
The application uses:
- **Bootstrap 5** for responsive design
- **Plotly.js** for interactive charts
- **Font Awesome** for icons
- **Custom CSS** for modern styling

### Chart Configuration
You can modify chart settings in `app.py`:
- Chart height and width
- Color schemes
- Interactive features
- Time range options

## 🐛 Troubleshooting

### Common Issues

1. **Port already in use**
   ```bash
   # Change port in app.py
   app.run(debug=True, host='0.0.0.0', port=5001)
   ```

2. **Database connection error**
   - Check database credentials in `app.py`
   - Ensure MySQL server is running
   - Verify network connectivity

3. **No data found**
   - Check if the date exists in your database
   - Verify date format (YYYY-MM-DD)
   - Use the API endpoint `/api/dates` to see available dates

### Debug Mode
The application runs in debug mode by default. For production:
```python
app.run(debug=False, host='0.0.0.0', port=5000)
```

## 📱 Mobile Support

The application is fully responsive and works on:
- Desktop browsers
- Tablets
- Mobile phones

## 🔒 Security Notes

- The application runs on `0.0.0.0` (all interfaces)
- Debug mode is enabled by default
- Database credentials are hardcoded (consider using environment variables for production)

## 🚀 Deployment

### Local Network Access
To access from other devices on your network:
```bash
python app.py
# Access via: http://YOUR_IP_ADDRESS:5000
```

### Production Deployment
For production deployment, consider:
- Using a production WSGI server (Gunicorn, uWSGI)
- Setting up a reverse proxy (Nginx)
- Using environment variables for configuration
- Disabling debug mode
- Setting up SSL/TLS

## 📈 Performance

- Charts are generated server-side using Plotly
- Data is fetched from MySQL database
- Interactive features are handled client-side
- Responsive design adapts to screen size

## 🤝 Contributing

Feel free to enhance the application with:
- Additional chart types
- More technical indicators
- Export functionality
- User authentication
- Real-time data updates 