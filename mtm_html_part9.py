# mtm_html_part9.py
# File 17: HTML template part 9

# This is part 9 of the HTML template

DASHBOARD_HTML_PART9 = """
<script>
    // Refresh chart cache when returning to the tab
    document.addEventListener('visibilitychange', function() {
        if (document.visibilityState === 'visible') {
            // Clear chart history cache so next chart open fetches fresh data
            for (const key in historyCache) {
                delete historyCache[key];
            }
            // Re-initialize popovers
            setTimeout(initGraphPopovers, 0);
            // Proactively refresh all chart histories
            users.forEach(user => updateChartHistory(user.userId));
            // If chart modal is open, refresh its data
            const modal = document.getElementById('graph-modal-bg');
            if (modal && lastChartUserId) {
                const canvas = document.getElementById(`graph-canvas-${lastChartUserId}-modal`);
                if (canvas) {
                    updateChartHistory(lastChartUserId).then(() => {
                        renderUserGraph(lastChartUserId, canvas, true, true);
                    });
                }
            }
            // If a popover is open, refresh its data
            if (lastPopoverUserId) {
                // Try to find the open tippy popover for this user
                const popover = document.querySelector('.tippy-box[data-state="visible"]');
                if (popover) {
                    const canvas = popover.querySelector('canvas');
                    if (canvas) {
                        updateChartHistory(lastPopoverUserId).then(() => {
                            renderUserGraph(lastPopoverUserId, canvas, false, true);
                        });
                    }
                }
            }
        }
    });
</script>
</body>
</html>
"""