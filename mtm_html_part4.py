# mtm_html_part4.py
# File 12: HTML template part 4

# This is part 4 of the HTML template

DASHBOARD_HTML_PART4 = """
<script>
    function updateUserUI(userId, data) {
        const mtmElement = document.getElementById(`mtm-${userId}`);
        const maxElement = document.getElementById(`max-${userId}`);
        const minElement = document.getElementById(`min-${userId}`);
        const rowElement = document.getElementById(`row-${userId}`);
        const openingHourElement = document.getElementById(`opening-hour-${userId}`);
        if (!mtmElement || !maxElement || !minElement || !rowElement) return;
        const userIndex = users.findIndex(user => user.userId === userId);
        if (userIndex === -1) return;
        const user = users[userIndex];
        if (data.status === 'error') {
            mtmElement.textContent = 'Connection Error';
            mtmElement.className = 'neutral';
            return;
        }
        const mtmValue = data.response;
        const maxMtm = data.max_mtm || 0;
        const minMtm = data.min_mtm || 0;
        user.mtm = mtmValue;
        if (mtmValue === 0 && maxMtm === 0 && minMtm === 0 && user.openingHourMtm === 0) {
            rowElement.style.display = 'none';
            return;
        } else {
            rowElement.style.display = '';
        }
        mtmElement.classList.add('data-updated');
        setTimeout(() => { mtmElement.classList.remove('data-updated'); }, 600);
        mtmElement.textContent = formatCurrency(mtmValue);
        mtmElement.className = mtmValue > 0 ? 'positive' : mtmValue < 0 ? 'negative' : 'neutral';
        if (data.max_mtm !== undefined && data.max_mtm !== null && data.max_mtm !== -Infinity) {
            user.maxMtm = data.max_mtm;
            maxElement.textContent = formatCurrency(data.max_mtm);
            maxElement.className = data.max_mtm > 0 ? 'positive' : data.max_mtm < 0 ? 'negative' : 'neutral';
        }
        if (data.min_mtm !== undefined && data.min_mtm !== null && data.min_mtm !== Infinity) {
            user.minMtm = data.min_mtm;
            minElement.textContent = formatCurrency(data.min_mtm);
            minElement.className = data.min_mtm > 0 ? 'positive' : data.min_mtm < 0 ? 'negative' : 'neutral';
        }
        if (openingHourElement) {
            openingHourElement.className = user.openingHourMtm > 0 ? 'positive' : user.openingHourMtm < 0 ? 'negative' : 'neutral';
            openingHourElement.textContent = formatCurrency(user.openingHourMtm);
        }
    }
    function updateLastUpdated() {
        const now = new Date();
        const text = `Last updated: ${now.toLocaleTimeString()}`;
        const desktop = document.getElementById('lastUpdated');
        const mobile = document.getElementById('lastUpdated-mobile');
        if (window.innerWidth <= 600) {
            if (desktop) desktop.style.display = 'none';
            if (mobile) {
                mobile.style.display = 'block';
                mobile.textContent = text;
            }
        } else {
            if (desktop) {
                desktop.style.display = '';
                desktop.textContent = text;
                // Move reconnect indicator next to last updated if not already present
                const indicator = document.getElementById('reconnect-indicator');
                if (indicator && desktop && indicator.parentNode !== desktop.parentNode) {
                    desktop.parentNode.insertBefore(indicator, desktop.nextSibling);
                }
            }
            if (mobile) mobile.style.display = 'none';
        }
        saveUserStats();
    }
    function handleFetchError() {
        consecutiveErrors++;
        if (consecutiveErrors >= MAX_CONSECUTIVE_ERRORS) {
            showReconnectIndicator();
        }
    }
    function resetErrorCount() {
        consecutiveErrors = 0;
        hideReconnectIndicator();
    }
    function showReconnectIndicator() {
        const indicator = document.getElementById('reconnect-indicator');
        if (indicator) indicator.style.display = 'inline-flex';
    }
    function hideReconnectIndicator() {
        const indicator = document.getElementById('reconnect-indicator');
        if (indicator) indicator.style.display = 'none';
    }
    async function fetchUserMTM(userId) {
        try {
            const response = await fetch(`/MTM?UserID=${userId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            if (data.opening_mtm !== undefined) {
                const user = users.find(u => u.userId === userId);
                if (user) user.openingHourMtm = data.opening_mtm;
            }
            updateUserUI(userId, data);
            resetErrorCount();
            resetMtmBackoff();
            return true;
        } catch (error) {
            handleFetchError();
            increaseMtmBackoff();
            setTimeout(() => fetchUserMTM(userId), mtmFetchBackoff);
            return false;
        }
    }
</script>
"""