# mtm_html_part1.py
# File 9: HTML template part 1

# The HTML template is split into two parts due to size limits
# This is part 1 - the first half of the HTML template

DASHBOARD_HTML_PART1 = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>MarvelQuant | MTM Tracker</title>
    <link rel="icon" type="image/svg+xml" href="/static/MQ-Logo-Main.svg">
    <link rel="stylesheet" href="https://unpkg.com/tippy.js@6/dist/tippy.css" />
    <style>
        body {
            background: #fff;
            font-family: 'Segoe UI', 'Poppins', Arial, sans-serif;
            margin: 0;
            padding: 0;
        }
        .container {
            max-width: 1100px;
            margin: 40px auto;
            padding: 0 8px;
        }
        .card {
            background: none;
            border-radius: 20px;
            box-shadow: 0 4px 24px rgba(0,0,0,0.08);
            padding: 0 0 32px 0;
            margin: 0 auto;
            overflow: hidden;
        }
        .header-bar {
            background: #fff;
            display: flex;
            align-items: center;
            padding: 24px 32px 10px 32px;
        }
        .header-bar img {
            height: 48px;
            margin-right: 18px;
        }
        .header-title {
            font-size: 2rem;
            font-weight: 600;
            color: #222;
            letter-spacing: 0.5px;
        }
        .info-message {
            display:flex;align-items:center;justify-content:space-between;color:#333;font-weight:600;font-size:1.15rem;margin:10px 32px 0 32px;min-height:56px;
        }
        .last-updated {
            text-align: right;
            font-size: 1rem;
            color: #666;
            margin: 18px 32px 0 0;
        }
        .table-wrapper {
            padding: 0 32px;
            overflow-x: auto;
        }
        table {
            width: 100%;
            border-collapse: separate;
            border-spacing: 0;
            margin-top: 18px;
            background: #fff;
            min-width: 0;
        }
        thead tr {
            background: #f2f2f2;
        }
        th, td {
            padding: 14px 12px;
            text-align: left;
            font-size: 1.08rem;
            vertical-align: middle;
        }
        th.sortable {
            cursor: pointer;
            position: relative;
        }
        th.sortable:hover {
            background-color: #e1e7f2;
        }
        th.sortable::after {
            content: "⇅";
            display: inline-block;
            margin-left: 5px;
            opacity: 0.4;
            font-size: 0.9em;
        }
        th.sortable.asc::after {
            content: "↑";
            opacity: 1;
        }
        th.sortable.desc::after {
            content: "↓";
            opacity: 1;
        }
        td.mtm-col {
            min-width: 130px;
        }
        th {
            color: #222;
            font-weight: 600;
            border: none;
            white-space: nowrap;
        }
        tbody tr {
            background: #fff;
            transition: background 0.2s;
        }
        tbody tr:nth-child(even) {
            background: #f6f8fb;
        }
        tbody tr:hover {
            background: #eaf1fb;
        }
        .positive {
            color: #0f9d58;
            font-weight: 600;
        }
        .negative {
            color: #ea4335;
            font-weight: 600;
        }
        .neutral {
            color: #2a5298;
            font-weight: 600;
        }
        .data-updated {
            animation: pulse 0.6s ease-in-out;
        }
        @keyframes pulse {
            0% { background-color: rgba(255,255,255,0); }
            50% { background-color: rgba(42,82,152,0.18); }
            100% { background-color: rgba(255,255,255,0); }
        }
        /* Sort transition effect */
        tbody tr {
            transition: transform 0.3s ease-out;
        }
    </style>
"""