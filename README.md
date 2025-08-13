# MTM Dashboard

## Overview
The MTM (Mark to Market) Dashboard is a real-time monitoring tool designed to track and display financial trading data for multiple users. It provides a comprehensive view of intraday MTM values, allowing traders and managers to monitor performance metrics in real-time.

## Features
- **Real-time MTM Tracking**: Monitors intraday MTM values for multiple users with automatic updates
- **Visual Indicators**: Color-coded display (green for positive, red for negative) for quick status assessment
- **Historical Data**: Tracks maximum and minimum MTM values throughout the session
- **Interactive Charts**: View MTM performance trends through interactive graphs
- **User Filtering**: Group users by IP address for better organization
- **Responsive Design**: Works on both desktop and mobile devices
- **Column Sorting**: Sort data by any column (ascending or descending)
- **Persistent Settings**: User preferences and sorting options are saved between sessions

## Project Structure
The project is organized into multiple modular files for better maintainability:

### Core Files
- `mtm_main.py`: Application entry point
- `mtm_imports.py`: Central import file for dependencies
- `mtm_config.py`: Configuration settings and parameters
- `mtm_server.py`: Web server implementation
- `mtm_cache.py`: Data caching mechanisms
- `mtm_background.py`: Background processing tasks

### API Implementation
- `mtm_api_part1.py` to `mtm_api_part4.py`: API endpoints for MTM data retrieval

### HTML Template Files
- `mtm_html.py`: Combines all HTML template parts
- `mtm_html_part1.py` to `mtm_html_part9.py`: Modularized HTML templates

### Optimized Versions
- `central_dashboard_optimized.py`: Optimized dashboard implementation
- Various `_optimized` and `_fixed` versions for compatibility and performance

### Command Files
- `main.cmd`, `main_optimized.cmd`, etc.: Startup scripts
- `users_MCX.cmd`, `users_NSE.cmd`: Exchange-specific user configurations

## Technical Implementation

### Backend
The backend server is implemented in Python and provides several API endpoints:
- `/MTM`: Returns current MTM values for a specific user
- `/users`: Returns the list of all users being tracked
- `/history`: Returns historical MTM data for charting
- `/config`: Returns configuration settings for the frontend

### Frontend
The frontend is built with HTML, CSS, and vanilla JavaScript:
- Real-time data fetching with JavaScript Fetch API
- ChartJS for MTM performance visualization
- Responsive design for mobile and desktop viewing
- Client-side sorting and filtering capabilities

### Data Flow
1. Server continuously updates MTM values in the background
2. Client periodically polls the server for updated data
3. UI updates in real-time, highlighting changes with visual cues
4. Historical data is aggregated for trend analysis and charting

## Setup and Configuration

### Configuration Files
- `config.ini`: Contains server configuration parameters
- `users.json`: User definitions and access credentials

### User Setup
Users can be added via the user configuration files or through API endpoints.
Each user must have:
- `userId`: Unique identifier
- `ip`: IP address (optional, used for grouping)
- `alias`: Display name (optional)

### Server Configuration
The server can be configured with different update intervals:
- `mtm_refresh_interval`: How often the UI refreshes MTM data
- `chart_update_interval`: How often chart data is updated
- `opening_mtm`: Time when opening MTM values are recorded
- `chart_start_time`: Time when chart data collection begins

## Usage

### Starting the Server
To start the dashboard server:
1. Execute the appropriate command file:
   ```
   main.cmd            # Standard version
   main_optimized.cmd  # Performance optimized version
   ```

2. Access the dashboard in a web browser at:
   ```
   http://localhost:8556
   ```

### User Interface
The main interface displays:
- User IDs and aliases
- Current MTM values
- Daily maximum and minimum MTM values
- Interactive chart icons for trend analysis

### Sorting Data
Click any column header to sort data:
- First click: Sort ascending
- Second click: Sort descending
- The current sort column is indicated with an arrow

### Viewing Charts
To view MTM performance charts:
- Hover over the chart icon for a quick preview (desktop only)
- Click the chart icon to open the full-sized chart in a modal window

## Maintenance and Troubleshooting

### Common Issues
- If connections fail, the dashboard will display a "Reconnecting..." indicator
- Empty MTM values (0,0,0) will hide the corresponding user row
- Charts are only available after the configured `chart_start_time`

### Logs
Log files are stored in the `logs` directory and contain:
- Server activity
- Connection errors
- Data processing events

## Future Enhancements
- OAuth-based authentication
- Multi-exchange support
- Custom alert thresholds
- Export functionality for reports
- Dark mode UI theme
