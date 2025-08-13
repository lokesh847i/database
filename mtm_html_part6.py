# mtm_html_part6.py
# File 14: HTML template part 6

# This is part 6 of the HTML template

DASHBOARD_HTML_PART6 = """
<script>
    function initGraphPopovers() {
        document.querySelectorAll('.graph-icon').forEach(icon => {
            const userId = icon.getAttribute('data-userid');
            // Only enable hover popover on desktop
            if (window.innerWidth > 600) {
                tippy(icon, {
                    content: spinnerSVG,
                    allowHTML: true,
                    interactive: true,
                    placement: 'top',
                    theme: 'light',
                    onShow(instance) {
                        lastPopoverUserId = userId;
                        if (isBeforeChartStartTime()) {
                            instance.setContent(`<div style='padding:18px 12px;text-align:center;max-width:260px;'><b>Chart will be available after ${window.globalSettings.chart_start_time}</b></div>`);
                            return;
                        }
                        if (historyCache[userId]) {
                            instance.setContent(createGraphPopoverContent(userId, false));
                            setTimeout(() => renderUserGraph(userId, instance.popper.querySelector('canvas'), false, true), 0);
                        } else {
                            instance.setContent(spinnerSVG);
                            fetch(`/history?UserID=${userId}`)
                                .then(res => res.json())
                                .then(data => {
                                    historyCache[userId] = data.history || [];
                                    instance.setContent(createGraphPopoverContent(userId, false));
                                    setTimeout(() => renderUserGraph(userId, instance.popper.querySelector('canvas'), false, true), 0);
                                });
                        }
                    },
                    onHidden(instance) {
                        const canvas = instance.popper.querySelector('canvas');
                        if (canvas && canvas._chartInstance) {
                            canvas._chartInstance.destroy();
                        }
                        lastPopoverUserId = null;
                    }
                });
            }
            // Always allow click to open modal
            icon.addEventListener('click', (e) => {
                e.stopPropagation();
                if (isBeforeChartStartTime()) {
                    // Show modal with message instead of chart
                    showChartNotAvailableModal();
                    return;
                }
                showGraphModal(userId);
            });
        });
    }
    function createGraphPopoverContent(userId, isModal) {
        return `<div class="graph-popover"><canvas id="graph-canvas-${userId}-${isModal ? 'modal' : 'popover'}" width="300" height="150"></canvas></div>`;
    }
    
    // Function to update chart history for a specific user
    async function updateChartHistory(userId) {
        try {
            const response = await fetch(`/history?UserID=${userId}`);
            if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
            const data = await response.json();
            historyCache[userId] = data.history || [];
            return true;
        } catch (error) {
            console.error(`Error updating chart history for ${userId}:`, error);
            return false;
        }
    }
    
    // Function to refresh all active chart displays
    function refreshChartDisplays() {
        // Update popover chart if visible
        if (lastPopoverUserId) {
            const popover = document.querySelector('.tippy-box[data-state="visible"]');
            if (popover) {
                const canvas = popover.querySelector('canvas');
                if (canvas) {
                    renderUserGraph(lastPopoverUserId, canvas, false, true);
                }
            }
        }
        
        // Update modal chart if visible
        if (lastChartUserId) {
            const modal = document.getElementById('graph-modal-bg');
            if (modal) {
                const canvas = document.getElementById(`graph-canvas-${lastChartUserId}-modal`);
                if (canvas) {
                    renderUserGraph(lastChartUserId, canvas, true, true);
                }
            }
        }
    }
</script>
"""