# mtm_html_part2.py
# File 10: HTML template part 2

# This is part 2 of the HTML template

DASHBOARD_HTML_PART2 = """
<style>
    @media (max-width: 900px) {
        .container { max-width: 100%; }
        .header-bar, .info-message, .table-wrapper { padding-left: 8px; padding-right: 8px; }
        th, td { font-size: 0.98rem; padding: 10px 6px; }
    }
    @media (max-width: 600px) {
        .header-title { font-size: 1.2rem; }
        .header-bar img { height: 32px; }
        th, td { font-size: 0.85rem; padding: 7px 2px; }
        .info-message { font-size: 0.95rem; padding: 8px 4px; margin: 16px 4px 0 4px; }
        .last-updated { margin: 12px 8px 0 0; font-size: 0.95rem; position: static !important; display: block; text-align: center; }
        .graph-modal {
            width: 98vw !important;
            min-width: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            padding: 8px 2px 8px 2px !important;
            border-radius: 14px !important;
        }
        .graph-popover {
            width: 98vw !important;
            min-width: 0 !important;
            height: auto !important;
            min-height: 0 !important;
            border-radius: 10px !important;
            padding: 8px 2px 8px 2px !important;
        }
        .graph-modal canvas,
        .graph-popover canvas {
            width: 90% !important;
            height: auto !important;
            max-width: 100vw !important;
        }
    }
    .graph-icon {
        cursor: pointer;
        font-size: 1.3rem;
        color: #2a5298;
        transition: color 0.2s;
        vertical-align: middle;
    }
    .graph-icon:hover {
        color: #0f9d58;
    }
    .graph-popover {
        width: 320px;
        height: 180px;
        background: #fff;
        padding: 8px 0 0 0;
        border-radius: 10px;
        box-shadow: none !important;
        border: 4px solid #e0e0e0;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .graph-modal-bg {
        position: fixed;
        top: 0; left: 0; right: 0; bottom: 0;
        background: rgba(0,0,0,0.25);
        z-index: 1000;
            display: flex;
        align-items: center;
        justify-content: center;
    }
    .graph-modal {
        background: #fff;
        border-radius: 16px;
        padding: 24px 24px 12px 24px;
        min-width: 400px;
        min-height: 320px;
        box-shadow: 0 4px 32px rgba(0,0,0,0.18);
        position: relative;
    }
    .graph-modal-close {
        position: absolute;
        top: 10px;
        right: 18px;
        font-size: 1.5rem;
        color: #888;
        cursor: pointer;
        background: none;
        border: none;
    }
    #reconnect-indicator { display: none; align-items: center; margin-left: 10px; font-size: 0.98rem; color: #ea4335; font-weight: 500; vertical-align: middle; }
    #reconnect-indicator svg { margin-right: 4px; vertical-align: middle; }
    .tippy-box[data-theme~='light'] {
        border: none !important;
        box-shadow: none !important;
        background: #fff !important;
    }
    .tippy-box[data-theme~='light'],
    .tippy-box[data-theme~='light'] .tippy-content {
        border: none !important;
        outline: none !important;
        background: #fff !important;
    }
    .tippy-box[data-theme~='light'] .tippy-arrow {
        color: #fff !important;
        border: none !important;
    }
</style>
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script src="https://unpkg.com/@popperjs/core@2"></script>
<script src="https://unpkg.com/tippy.js@6"></script>
</head>
<body>
    <div class="container">
    <div class="card">
        <div class="info-message" style="display:flex;align-items:center;justify-content:space-between;color:#333;font-weight:600;font-size:1.15rem;margin:10px 32px 0 32px;min-height:56px;">
            <img src="/static/MQ-Logo-Main.svg" alt="MarvelQuant Logo" style="height:48px;vertical-align:middle;margin-right:18px;flex-shrink:0;">
            <span style="flex:1;text-align:center;font-size:1.3rem;font-weight:600;">MTM Tracker</span>
            <span class="last-updated" id="lastUpdated" style="margin:0;font-size:1rem;color:#666;font-weight:400;text-align:right;min-width:140px;"></span>
        </div>
        <div class="table-wrapper">
        <table class="mtm-table">
            <thead>
                <tr>
                    <th class="sortable" onclick="sortTable('index')">S.No.</th>
                    <th class="sortable" onclick="sortTable('userId')">User ID</th>
                    <th class="sortable" onclick="sortTable('alias')">User Alias</th>
                    <th class="sortable" onclick="sortTable('mtm')">Intraday MTM</th>
                    <th class="sortable" onclick="sortTable('maxMtm')">Max MTM</th>
                    <th class="sortable" onclick="sortTable('minMtm')">Min MTM</th>
                    <th>MTM Analyzer</th>
                </tr>
            </thead>
            <tbody id="mtmTableBody">
                    <tr>
                        <td>-</td><td>-</td><td>-</td><td class="neutral">-</td><td class="positive">-</td><td class="negative">-</td>
                </tr>
            </tbody>
        </table>
        </div>
    </div>
</div>
<div class="last-updated" id="lastUpdated-mobile" style="display:none;margin:12px 0 0 0;font-size:0.95rem;color:#666;font-weight:400;text-align:center;"></div>
<span id="reconnect-indicator">
    <svg width="18" height="18" viewBox="0 0 40 40" fill="none"><circle cx="20" cy="20" r="16" stroke="#ea4335" stroke-width="4" stroke-linecap="round" stroke-dasharray="80" stroke-dashoffset="60"><animate attributeName="stroke-dashoffset" values="60;0" dur="1s" repeatCount="indefinite"/></circle></svg>
    Reconnecting…
</span>
"""