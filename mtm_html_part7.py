# mtm_html_part7.py
# File 15: HTML template part 7

# This is part 7 of the HTML template

DASHBOARD_HTML_PART7 = """
<script>
    function renderUserGraph(userId, canvas, isModal, useCache) {
        let historyPromise;
        if (useCache && historyCache[userId]) {
            historyPromise = Promise.resolve({ history: historyCache[userId] });
        } else {
            historyPromise = fetch(`/history?UserID=${userId}`).then(res => res.json()).then(data => {
                historyCache[userId] = data.history || [];
                return data;
            });
        }
        historyPromise.then(data => {
            if (!data.history || !canvas) return;
            // Filter history to only include points at or after chart_start_time
            let filteredHistory = data.history;
            if (window.globalSettings && window.globalSettings.chart_start_time) {
                const chartStart = window.globalSettings.chart_start_time;
                filteredHistory = data.history.filter(point => {
                    // point.timestamp is HH:MM:SS, chartStart is HH:MM
                    const pt = point.timestamp.split(":");
                    const ch = chartStart.split(":");
                    const ptVal = parseInt(pt[0],10)*60+parseInt(pt[1],10);
                    const chVal = parseInt(ch[0],10)*60+parseInt(ch[1],10);
                    return ptVal >= chVal;
                });
            }
            const labels = filteredHistory.map(point => point.timestamp);
            const values = filteredHistory.map(point => point.mtm);
            let borderColor = '#2a5298';
            let backgroundColor = 'rgba(180,180,180,0.04)'; // neutral fill for mixed
            let segment = undefined;
            if (values.length > 0) {
                const allPositive = values.every(v => v > 0);
                const allNegative = values.every(v => v < 0);
                if (allPositive) {
                    borderColor = '#0f9d58';
                    backgroundColor = 'rgba(15,157,88,0.08)';
                } else if (allNegative) {
                    borderColor = '#ea4335';
                    backgroundColor = 'rgba(234,67,53,0.08)';
                } else {
                    // Use Chart.js segment coloring for mixed
                    borderColor = undefined;
                    segment = {
                        borderColor: ctx => {
                            const v = ctx.p1.parsed.y;
                            return v >= 0 ? '#0f9d58' : '#ea4335';
                        }
                    };
                }
            }
            if (canvas._chartInstance) canvas._chartInstance.destroy();
            canvas._chartInstance = new Chart(canvas.getContext('2d'), {
                type: 'line',
                data: {
                    labels: labels,
                    datasets: [{
                        label: '',
                        data: values,
                        borderColor: borderColor,
                        backgroundColor: backgroundColor,
                        pointRadius: 0,
                        pointHoverRadius: 5,
                        fill: true,
                        tension: 0.25,
                        segment: segment
                    }]
                },
                options: {
                    responsive: false,
                    plugins: {
                        legend: { display: false },
                        tooltip: { enabled: true }
                    },
                    interaction: {
                        mode: 'nearest',
                        intersect: false
                    },
                    scales: {
                        x: { display: true, title: { display: false } },
                        y: { display: true, title: { display: false } }
                    }
                }
            });
        });
    }
</script>
"""