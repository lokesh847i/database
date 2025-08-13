# mtm_html_part8.py
# File 16: HTML template part 8

# This is part 8 of the HTML template

DASHBOARD_HTML_PART8 = """
<script>
    function showGraphModal(userId) {
        lastChartUserId = userId;
        // Remove any existing modal
        const oldModal = document.getElementById('graph-modal-bg');
        if (oldModal) oldModal.remove();
        // Create modal
        const modalBg = document.createElement('div');
        modalBg.className = 'graph-modal-bg';
        modalBg.id = 'graph-modal-bg';
        modalBg.innerHTML = `
            <div class="graph-modal" style="width:75vw;height:75vh;min-width:320px;min-height:240px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <button class="graph-modal-close" onclick="document.getElementById('graph-modal-bg').remove()">&times;</button>
                <h3 style="text-align:center;font-weight:600;margin-bottom:12px;">${userId}</h3>
                <div id="graph-modal-spinner">${spinnerSVG}</div>
                <canvas id="graph-canvas-${userId}-modal" width="${Math.floor(window.innerWidth*0.7)}" height="${Math.floor(window.innerHeight*0.55)}" style="display:none;"></canvas>
            </div>
        `;
        document.body.appendChild(modalBg);
        // Render chart with cache and spinner
        setTimeout(() => {
            const canvas = document.getElementById(`graph-canvas-${userId}-modal`);
            if (historyCache[userId]) {
                document.getElementById('graph-modal-spinner').style.display = 'none';
                canvas.style.display = '';
                renderUserGraph(userId, canvas, true, true);
            } else {
                renderUserGraph(userId, canvas, true, false);
                // Wait for data, then hide spinner
                fetch(`/history?UserID=${userId}`)
                    .then(res => res.json())
                    .then(data => {
                        historyCache[userId] = data.history || [];
                        document.getElementById('graph-modal-spinner').style.display = 'none';
                        canvas.style.display = '';
                        renderUserGraph(userId, canvas, true, true);
                    });
            }
        }, 0);
        // Close on background click
        modalBg.addEventListener('click', (e) => {
            if (e.target === modalBg) modalBg.remove();
        });
    }
    
    function showChartNotAvailableModal() {
        // Remove any existing modal
        const oldModal = document.getElementById('graph-modal-bg');
        if (oldModal) oldModal.remove();
        // Create modal
        const modalBg = document.createElement('div');
        modalBg.className = 'graph-modal-bg';
        modalBg.id = 'graph-modal-bg';
        modalBg.innerHTML = `
            <div class="graph-modal" style="width:75vw;height:30vh;min-width:320px;min-height:120px;display:flex;flex-direction:column;align-items:center;justify-content:center;">
                <button class="graph-modal-close" onclick="document.getElementById('graph-modal-bg').remove()">&times;</button>
                <h3 style="text-align:center;font-weight:600;margin-bottom:12px;">MTM Chart</h3>
                <div style='font-size:1.15rem;text-align:center;padding:18px 0;'><b>Chart will be available after ${window.globalSettings.chart_start_time}</b></div>
            </div>
        `;
        document.body.appendChild(modalBg);
        // Close on background click
        modalBg.addEventListener('click', (e) => {
            if (e.target === modalBg) modalBg.remove();
        });
    }
</script>
"""