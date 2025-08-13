# mtm_html_part3.py
# File 11: HTML template part 3

# This is part 3 of the HTML template

DASHBOARD_HTML_PART3 = """
<script>
    // Configuration - Use relative path for API to work from any hostname
    const API_ENDPOINT = '/MTM';
    let REFRESH_INTERVAL = 2000; // Default: 2 seconds (will be updated from server config)
    let CHART_UPDATE_INTERVAL = 30000; // Default: 30 seconds (will be updated from server config)
    let users = [];
    let refreshInterval;
    let chartUpdateInterval; // New interval for chart updates
    let lastChartUpdate = {}; // Track last chart update by user
    let consecutiveErrors = 0;
    const MAX_CONSECUTIVE_ERRORS = 5;
    let zeroMtmCount = {};
    // Sorting state variables
    let currentSortColumn = 'userId'; // Default sort column
    let currentSortDirection = 'asc'; // Default sort direction
    // History cache for user graphs
    const historyCache = {};
    // Spinner SVG
    const spinnerSVG = `<div style='display:flex;align-items:center;justify-content:center;height:100%;'><svg width='40' height='40' viewBox='0 0 40 40' fill='none'><circle cx='20' cy='20' r='16' stroke='#2a5298' stroke-width='4' stroke-linecap='round' stroke-dasharray='80' stroke-dashoffset='60'><animate attributeName='stroke-dashoffset' values='60;0' dur='1s' repeatCount='indefinite'/></circle></svg></div>`;
    // Helper: Exponential backoff for MTM fetch errors
    let mtmFetchBackoff = 2000;
    function resetMtmBackoff() { mtmFetchBackoff = 2000; }
    function increaseMtmBackoff() { mtmFetchBackoff = Math.min(mtmFetchBackoff * 2, 30000); }
    let lastChartUserId = null;
    let lastPopoverUserId = null;
    
    // Function to load configuration from server
    async function loadConfig() {
        try {
            const response = await fetch('/config');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const configData = await response.json();
            
            // Update configuration values
            REFRESH_INTERVAL = configData.mtm_refresh_interval || REFRESH_INTERVAL;
            CHART_UPDATE_INTERVAL = configData.chart_update_interval || CHART_UPDATE_INTERVAL;
            
            console.log(`Loaded configuration: MTM refresh=${REFRESH_INTERVAL}ms, Chart update=${CHART_UPDATE_INTERVAL}ms`);
            
            // If the refresh interval is already running, restart it with the new value
            if (refreshInterval) {
                clearInterval(refreshInterval);
                startAutoRefresh();
            }
            
            return configData;
        } catch (error) {
            console.error("Failed to load configuration:", error);
            return null;
        }
    }
    
    // Function to save the user's sort preferences
    function saveSortPreferences() {
        localStorage.setItem('mtmTrackerSort', JSON.stringify({
            column: currentSortColumn,
            direction: currentSortDirection
        }));
    }
    
    // Function to load the user's sort preferences
    function loadSortPreferences() {
        const savedSort = localStorage.getItem('mtmTrackerSort');
        if (savedSort) {
            try {
                const sortPrefs = JSON.parse(savedSort);
                currentSortColumn = sortPrefs.column || 'userId';
                currentSortDirection = sortPrefs.direction || 'asc';
            } catch (e) {
                console.error("Error loading saved sort preferences:", e);
            }
        }
    }
    
    // Function to handle column sorting
    window.sortTable = function(column) {
        // Toggle direction if clicking the same column
        if (column === currentSortColumn) {
            currentSortDirection = currentSortDirection === 'asc' ? 'desc' : 'asc';
        } else {
            currentSortColumn = column;
            currentSortDirection = 'asc';
        }
        
        // Save the sort preferences
        saveSortPreferences();
        
        // Re-render the table with the new sorting
        renderUserTable();
    }
    
    document.addEventListener('DOMContentLoaded', async function() {
        // Load sort preferences
        loadSortPreferences();
        
        // Load configuration from server
        await loadConfig();
        
        zeroMtmCount = {};
        await fetchUsers();
        users.forEach(user => { zeroMtmCount[user.userId] = 0; });
        renderUserTable();
        startAutoRefresh();
            const savedStats = localStorage.getItem('mtmTrackerStats');
            if (savedStats) {
                try {
                    const stats = JSON.parse(savedStats);
                    users.forEach(user => {
                        if (stats[user.userId]) {
                            user.maxMtm = stats[user.userId].maxMtm || -Infinity;
                            user.minMtm = stats[user.userId].minMtm || Infinity;
                        if (stats[user.userId].openingHourMtm !== undefined) {
                            user.openingHourMtm = stats[user.userId].openingHourMtm;
                        }
                        const maxElement = document.getElementById(`max-${user.userId}`);
                        const minElement = document.getElementById(`min-${user.userId}`);
                        const openingHourElement = document.getElementById(`opening-hour-${user.userId}`);
                        if (maxElement && user.maxMtm !== -Infinity) {
                            maxElement.textContent = formatCurrency(user.maxMtm);
                        }
                        if (minElement && user.minMtm !== Infinity) {
                            minElement.textContent = formatCurrency(user.minMtm);
                        }
                        if (openingHourElement && user.openingHourMtm !== undefined) {
                            openingHourElement.textContent = formatCurrency(user.openingHourMtm);
                            openingHourElement.className = user.openingHourMtm > 0 ? 'positive' : user.openingHourMtm < 0 ? 'negative' : 'neutral';
                        }
                    }
                });
            } catch (e) { console.error("Error loading saved stats:", e); }
        }
    });
    async function fetchUsers() {
        try {
            const response = await fetch('/users');
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            window.globalSettings = {
                opening_mtm: data.opening_mtm || '09:15',
                start_time: data.start_time || '09:16',
                chart_start_time: data.chart_start_time || '09:15'
            };
            if (data && data.users && Array.isArray(data.users)) {
                users = data.users.map(user => ({
                        userId: user.userId,
                        ip: user.ip || null,
                        alias: user.alias || '',
                        mtm: 0,
                        maxMtm: -Infinity,
                        minMtm: Infinity,
                    openingHourMtm: 0
                }));
            } else {
                users = [];
            }
            if (users.length === 0) {
                document.getElementById('mtmTableBody').innerHTML = '<tr><td colspan="8" style="text-align:center;">No users found.</td></tr>';
            }
        } catch (error) {
            document.getElementById('mtmTableBody').innerHTML = '<tr><td colspan="8" style="text-align:center;">Failed to load user data.</td></tr>';
            users = [];
        }
    }
    function formatCurrency(value) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            minimumFractionDigits: 2,
            maximumFractionDigits: 2
        }).format(value);
    }
</script>
"""