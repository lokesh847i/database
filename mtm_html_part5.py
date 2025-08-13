# mtm_html_part5.py
# File 13: HTML template part 5

# This is part 5 of the HTML template

DASHBOARD_HTML_PART5 = """
<script>
    async function fetchAllMTM() {
        const fetchPromises = users.map(user => fetchUserMTM(user.userId));
        try {
            await Promise.all(fetchPromises);
            // Only update chart data every CHART_UPDATE_INTERVAL
            const now = Date.now();
            let chartUpdated = false;
            for (const user of users) {
                if (!lastChartUpdate[user.userId] || (now - lastChartUpdate[user.userId]) >= CHART_UPDATE_INTERVAL) {
                    await updateChartHistory(user.userId);
                    lastChartUpdate[user.userId] = now;
                    chartUpdated = true;
                }
            }
            
            // Only update UI elements if a chart was updated
            if (chartUpdated) {
                refreshChartDisplays();
            }
            
            updateLastUpdated();
        } catch (error) {
            handleFetchError();
        }
    }
    function startAutoRefresh() {
        if (refreshInterval) clearInterval(refreshInterval);
        refreshInterval = setInterval(fetchAllMTM, REFRESH_INTERVAL);
        console.log(`Auto refresh started: MTM data every ${REFRESH_INTERVAL}ms, Chart updates every ${CHART_UPDATE_INTERVAL}ms`);
    }
    function saveUserStats() {
        const stats = {};
        users.forEach(user => {
            stats[user.userId] = {
                maxMtm: user.maxMtm,
                minMtm: user.minMtm,
                openingHourMtm: user.openingHourMtm
            };
        });
        localStorage.setItem('mtmTrackerStats', JSON.stringify(stats));
    }
    function renderUserTable() {
        const mtmTableBody = document.getElementById('mtmTableBody');
        mtmTableBody.innerHTML = '';
        const usersByIp = {};
        users.forEach(user => {
            const cleanIp = user.ip ? user.ip.split(':')[0] : 'N/A';
            if (!usersByIp[cleanIp]) usersByIp[cleanIp] = [];
            usersByIp[cleanIp].push(user);
        });
        
        // Sort users array based on current sort column and direction
        let allUsers = [];
        for (const ip in usersByIp) {
            const usersWithSameIp = usersByIp[ip];
            allUsers = allUsers.concat(usersWithSameIp);
        }
        
        // Perform the sort
        sortUserArray(allUsers);
        
        let rowIndex = 1;
        allUsers.forEach(user => {
            const row = document.createElement('tr');
            row.id = `row-${user.userId}`;
            const mtmValue = user.mtm || 0;
            const maxMtm = user.maxMtm !== -Infinity ? user.maxMtm : 0;
            const minMtm = user.minMtm !== Infinity ? user.minMtm : 0;
            const mtmClass = mtmValue > 0 ? 'positive' : mtmValue < 0 ? 'negative' : 'neutral';
            const maxClass = maxMtm > 0 ? 'positive' : maxMtm < 0 ? 'negative' : 'neutral';
            const minClass = minMtm > 0 ? 'positive' : minMtm < 0 ? 'negative' : 'neutral';
            const maxMtmDisplay = formatCurrency(maxMtm);
            const minMtmDisplay = formatCurrency(minMtm);
            row.innerHTML += `
                <td>${rowIndex}</td>
                <td>${user.userId}</td>
                <td>${user.alias || ''}</td>
                <td id="mtm-${user.userId}" class="mtm-col ${mtmClass}">${formatCurrency(mtmValue)}</td>
                <td id="max-${user.userId}" class="mtm-col ${maxClass}">${maxMtmDisplay}</td>
                <td id="min-${user.userId}" class="mtm-col ${minClass}">${minMtmDisplay}</td>
                <td><span class="graph-icon" data-userid="${user.userId}" title="View MTM Graph">📈</span></td>
            `;
            mtmTableBody.appendChild(row);
            rowIndex++;
        });
        setTimeout(initGraphPopovers, 0);
        
        // Update header styling based on current sort
        document.querySelectorAll('th.sortable').forEach(th => {
            th.classList.remove('asc', 'desc');
            const sortCol = th.getAttribute('onclick').match(/sortTable\('(.+?)'\)/)[1];
            if (sortCol === currentSortColumn) {
                th.classList.add(currentSortDirection);
            }
        });
    }
    
    // Function to sort the users array based on current sort state
    function sortUserArray(usersArray) {
        usersArray.sort((a, b) => {
            let aValue, bValue;
            
            // For index column, use the userId for consistent sorting
            if (currentSortColumn === 'index') {
                aValue = a.userId;
                bValue = b.userId;
            } else {
                aValue = a[currentSortColumn];
                bValue = b[currentSortColumn];
            }
            
            // Handle undefined or special values
            if (currentSortColumn === 'maxMtm') {
                aValue = aValue === -Infinity ? 0 : aValue;
                bValue = bValue === -Infinity ? 0 : bValue;
            }
            if (currentSortColumn === 'minMtm') {
                aValue = aValue === Infinity ? 0 : aValue;
                bValue = bValue === Infinity ? 0 : bValue;
            }
            
            // Handle null or undefined values
            aValue = aValue === null || aValue === undefined ? '' : aValue;
            bValue = bValue === null || bValue === undefined ? '' : bValue;
            
            // Sort string values case-insensitively
            if (typeof aValue === 'string' && typeof bValue === 'string') {
                aValue = aValue.toLowerCase();
                bValue = bValue.toLowerCase();
            }
            
            // Compare the values
            if (aValue < bValue) return currentSortDirection === 'asc' ? -1 : 1;
            if (aValue > bValue) return currentSortDirection === 'asc' ? 1 : -1;
            
            // If values are equal, sort by userId as secondary criteria
            if (currentSortColumn !== 'userId') {
                if (a.userId < b.userId) return -1;
                if (a.userId > b.userId) return 1;
            }
            
            return 0;
        });
    }
    function isBeforeChartStartTime() {
        if (!window.globalSettings || !window.globalSettings.chart_start_time) return false;
        const now = new Date();
        const [h, m] = window.globalSettings.chart_start_time.split(':').map(Number);
        const chartStart = new Date(now.getFullYear(), now.getMonth(), now.getDate(), h, m, 0, 0);
        return now < chartStart;
    }
</script>
"""