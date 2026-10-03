"""
Builder script to generate docs/index.html with authentic industrial SCADA/HMI architecture,
inspired by React SCADA HMI (ISA-101 high performance HMI principles),
incorporating all canonical SAANJH simulation results.
"""

import json
import os

with open('docs/data/timeseries_bundle.json', 'r') as f:
    timeseries_data = json.load(f)

with open('docs/data/fleet_bundle.json', 'r') as f:
    fleet_data = json.load(f)

with open('docs/data/comparison.json', 'r') as f:
    comparison_data = json.load(f)

with open('docs/data/economics_scenarios.json', 'r') as f:
    economics_data = json.load(f)

with open('docs/data/discom_action_plan.json', 'r') as f:
    discom_data = json.load(f)

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>SAANJH SCADA/HMI | EcoStruxure Grid Edge Console | Feeder FDR-023</title>
    <meta name="description" content="SAANJH Distribution SCADA/HMI - Virtual Community Battery & Flexibility Aggregator for Indian LV Distribution Feeders.">
    <!-- Google Fonts -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;600;700&display=swap" rel="stylesheet">
    <!-- Chart.js CDN -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        :root {{
            --bg-canvas: #090D14;
            --bg-panel: #111622;
            --bg-panel-header: #161D2B;
            --bg-panel-subtle: #0D121B;
            --bg-hover: #1C2436;
            
            --border-primary: #1F293D;
            --border-secondary: #2B3852;
            --border-active: #00D68F;
            
            --text-primary: #F1F5F9;
            --text-secondary: #94A3B8;
            --text-muted: #64748B;
            --text-dim: #475569;
            
            /* ISA-101 SCADA Color Standard */
            --scada-normal: #10B981;
            --scada-normal-glow: rgba(16, 185, 129, 0.2);
            --scada-urgent: #EF4444;
            --scada-urgent-glow: rgba(239, 68, 68, 0.25);
            --scada-high: #F59E0B;
            --scada-medium: #EAB308;
            --scada-telemetry: #38BDF8;
            --scada-flex: #A855F7;
            --scada-solar: #FBBF24;
            
            --schneider-green: #3DCD58;
            --schneider-dark: #00873D;
            
            --font-ui: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            --font-mono: 'JetBrains Mono', 'IBM Plex Mono', Consolas, monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-feature-settings: "tnum" 1;
        }}

        body {{
            background-color: var(--bg-canvas);
            color: var(--text-primary);
            font-family: var(--font-ui);
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            overflow-x: hidden;
            font-size: 13px;
            user-select: none;
        }}

        /* Industrial SCADA Top Bar */
        .scada-masthead {{
            background: #0B0F18;
            border-bottom: 2px solid var(--border-primary);
            padding: 0 1rem;
            height: 48px;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
        }}

        .brand-section {{
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .schneider-badge {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: rgba(61, 205, 88, 0.12);
            border: 1px solid rgba(61, 205, 88, 0.4);
            padding: 0.25rem 0.6rem;
            border-radius: 2px;
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 0.75rem;
            color: var(--schneider-green);
            letter-spacing: 0.05em;
        }}

        .app-title-cluster {{
            display: flex;
            flex-direction: column;
        }}

        .app-title {{
            font-family: var(--font-mono);
            font-size: 0.95rem;
            font-weight: 700;
            letter-spacing: 0.05em;
            color: #FFFFFF;
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .app-title .tag {{
            background: #1E293B;
            color: var(--text-secondary);
            font-size: 0.68rem;
            font-weight: 600;
            padding: 1px 6px;
            border-radius: 2px;
            border: 1px solid #334155;
        }}

        .feeder-selector-box {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
            background: var(--bg-panel-subtle);
            border: 1px solid var(--border-primary);
            padding: 0.25rem 0.75rem;
            border-radius: 2px;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .feeder-selector-box .asset-label {{
            color: var(--text-muted);
            text-transform: uppercase;
        }}

        .feeder-selector-box .asset-val {{
            color: #38BDF8;
            font-weight: 600;
        }}

        .masthead-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .comm-status {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            color: var(--scada-normal);
        }}

        .comm-dot {{
            width: 7px;
            height: 7px;
            background: var(--scada-normal);
            border-radius: 50%;
            box-shadow: 0 0 6px var(--scada-normal);
            animation: pulse-slow 2s infinite;
        }}

        @keyframes pulse-slow {{
            0%, 100% {{ opacity: 1; transform: scale(1); }}
            50% {{ opacity: 0.4; transform: scale(0.85); }}
        }}

        .sys-clock {{
            background: #06090F;
            border: 1px solid var(--border-primary);
            padding: 0.2rem 0.6rem;
            border-radius: 2px;
            color: #F1F5F9;
            font-weight: 600;
            letter-spacing: 0.05em;
        }}

        /* Operational Telemetry / Annunciator Ribbon */
        .scada-telemetry-ribbon {{
            background: #0E1420;
            border-bottom: 1px solid var(--border-primary);
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 1px;
            background-color: var(--border-primary);
        }}

        .telemetry-cell {{
            background: #0E1420;
            padding: 0.6rem 1rem;
            display: flex;
            flex-direction: column;
            gap: 0.2rem;
            transition: background 0.15s ease;
        }}

        .telemetry-cell:hover {{
            background: #141C2C;
        }}

        .cell-tag {{
            font-family: var(--font-mono);
            font-size: 0.68rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}

        .cell-tag .indicator {{
            width: 6px;
            height: 6px;
            border-radius: 1px;
            background: var(--text-dim);
        }}

        .cell-tag .indicator.normal {{ background: var(--scada-normal); }}
        .cell-tag .indicator.alarm {{ background: var(--scada-urgent); }}
        .cell-tag .indicator.flex {{ background: var(--scada-flex); }}
        .cell-tag .indicator.volt {{ background: var(--scada-telemetry); }}

        .cell-value-row {{
            display: flex;
            align-items: baseline;
            gap: 0.4rem;
        }}

        .cell-val {{
            font-family: var(--font-mono);
            font-size: 1.35rem;
            font-weight: 700;
            letter-spacing: -0.02em;
            color: #FFFFFF;
        }}

        .cell-unit {{
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--text-muted);
        }}

        .cell-delta {{
            font-family: var(--font-mono);
            font-size: 0.7rem;
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        .delta-good {{ color: var(--scada-normal); }}
        .delta-bad {{ color: var(--scada-urgent); }}
        .delta-warn {{ color: var(--scada-high); }}
        .delta-neutral {{ color: var(--text-secondary); }}

        /* Playback Scrubber & Time Travel Ribbon */
        .scada-scrubber-ribbon {{
            background: #111724;
            border-bottom: 1px solid var(--border-primary);
            padding: 0.4rem 1rem;
            display: flex;
            align-items: center;
            gap: 1rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .playback-controls {{
            display: flex;
            align-items: center;
            gap: 0.25rem;
        }}

        .scada-btn {{
            background: #1A2336;
            color: var(--text-primary);
            border: 1px solid var(--border-primary);
            padding: 0.3rem 0.6rem;
            border-radius: 2px;
            cursor: pointer;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            font-weight: 600;
            display: inline-flex;
            align-items: center;
            gap: 0.35rem;
            transition: all 0.15s ease;
        }}

        .scada-btn:hover {{
            background: #25334E;
            border-color: #3B82F6;
        }}

        .scada-btn.active {{
            background: #00D68F;
            color: #000000;
            border-color: #00D68F;
            font-weight: 700;
        }}

        .scada-btn.alert {{
            background: rgba(239, 68, 68, 0.15);
            color: #EF4444;
            border-color: rgba(239, 68, 68, 0.4);
        }}

        .scada-btn.alert:hover {{
            background: #EF4444;
            color: #FFFFFF;
        }}

        .time-slider-container {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .time-slider {{
            flex: 1;
            -webkit-appearance: none;
            height: 6px;
            background: #1E293B;
            border-radius: 3px;
            outline: none;
            cursor: pointer;
        }}

        .time-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            appearance: none;
            width: 16px;
            height: 16px;
            border-radius: 2px;
            background: #00D68F;
            cursor: pointer;
            border: 2px solid #06090F;
            box-shadow: 0 0 6px rgba(0, 214, 143, 0.5);
        }}

        .time-readout {{
            background: #070A10;
            border: 1px solid var(--border-primary);
            padding: 0.25rem 0.75rem;
            border-radius: 2px;
            color: #00D68F;
            font-weight: 700;
            min-width: 140px;
            text-align: center;
        }}

        .event-shortcuts {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }}

        /* F-Key Navigation Tab Bar */
        .scada-nav-tabs {{
            background: #0B0E17;
            border-bottom: 2px solid var(--border-primary);
            display: flex;
            gap: 2px;
            padding: 0 1rem;
        }}

        .nav-tab {{
            background: #101622;
            color: var(--text-secondary);
            border: 1px solid var(--border-primary);
            border-bottom: none;
            padding: 0.5rem 1.25rem;
            cursor: pointer;
            font-family: var(--font-mono);
            font-size: 0.8rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 0.5rem;
            position: relative;
            top: 2px;
            transition: all 0.15s ease;
        }}

        .nav-tab:hover {{
            background: #182234;
            color: #FFFFFF;
        }}

        .nav-tab.active {{
            background: var(--bg-panel);
            color: #00D68F;
            border-top: 2px solid #00D68F;
            border-left: 1px solid var(--border-primary);
            border-right: 1px solid var(--border-primary);
            border-bottom: 2px solid var(--bg-panel);
            font-weight: 700;
            z-index: 10;
        }}

        .nav-tab .f-key {{
            background: #070A10;
            color: var(--text-muted);
            font-size: 0.7rem;
            padding: 1px 4px;
            border-radius: 2px;
            border: 1px solid var(--border-primary);
        }}

        .nav-tab.active .f-key {{
            color: #00D68F;
            border-color: rgba(0, 214, 143, 0.4);
        }}

        /* Main Workspace Container */
        .scada-workspace {{
            flex: 1;
            padding: 1rem;
            background: var(--bg-canvas);
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}

        .tab-viewport {{
            display: none;
            flex: 1;
            flex-direction: column;
            gap: 1rem;
        }}

        .tab-viewport.active {{
            display: flex;
        }}

        /* Industrial Panels */
        .scada-panel {{
            background: var(--bg-panel);
            border: 1px solid var(--border-primary);
            border-radius: 2px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .panel-header {{
            background: var(--bg-panel-header);
            border-bottom: 1px solid var(--border-primary);
            padding: 0.5rem 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            font-weight: 600;
            color: var(--text-primary);
            letter-spacing: 0.03em;
        }}

        .panel-header .title-left {{
            display: flex;
            align-items: center;
            gap: 0.5rem;
        }}

        .panel-header .status-tag {{
            font-size: 0.68rem;
            padding: 1px 6px;
            border-radius: 2px;
            border: 1px solid;
            font-weight: 700;
        }}

        .status-tag.active {{
            background: rgba(16, 185, 129, 0.1);
            color: var(--scada-normal);
            border-color: rgba(16, 185, 129, 0.3);
        }}

        .status-tag.warning {{
            background: rgba(245, 158, 11, 0.1);
            color: var(--scada-high);
            border-color: rgba(245, 158, 11, 0.3);
        }}

        .status-tag.alert {{
            background: rgba(239, 68, 68, 0.1);
            color: var(--scada-urgent);
            border-color: rgba(239, 68, 68, 0.3);
        }}

        .panel-body {{
            padding: 0.85rem;
            flex: 1;
            display: flex;
            flex-direction: column;
        }}

        /* Screen 1: SLD & Mimic Layout */
        .mimic-layout-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1rem;
            flex: 1;
        }}

        /* SVG Mimic Canvas */
        .sld-canvas-container {{
            background: #0A0E18;
            border: 1px solid var(--border-primary);
            border-radius: 2px;
            position: relative;
            min-height: 480px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .sld-svg {{
            width: 100%;
            height: 100%;
            flex: 1;
        }}

        /* Mimic SVG Elements */
        .busbar {{
            stroke: #475569;
            stroke-width: 4;
            stroke-linecap: square;
        }}

        .busbar.energized {{
            stroke: #38BDF8;
            filter: drop-shadow(0 0 3px rgba(56, 189, 248, 0.5));
        }}

        .feeder-line {{
            stroke: #334155;
            stroke-width: 2.5;
            stroke-linecap: round;
        }}

        .feeder-line.active {{
            stroke: #00D68F;
        }}

        .pulse-path {{
            stroke-dasharray: 6, 12;
            animation: dash-flow 1.5s linear infinite;
        }}

        @keyframes dash-flow {{
            to {{ stroke-dashoffset: -18; }}
        }}

        /* Linear Gauge Component (ISA-101 high performance) */
        .linear-gauge-container {{
            display: flex;
            flex-direction: column;
            gap: 0.35rem;
            font-family: var(--font-mono);
        }}

        .gauge-track {{
            height: 20px;
            background: #141C2C;
            border: 1px solid var(--border-primary);
            position: relative;
            border-radius: 2px;
            overflow: hidden;
        }}

        .gauge-fill {{
            height: 100%;
            background: var(--scada-normal);
            transition: width 0.25s ease, background 0.25s ease;
        }}

        .gauge-threshold {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #EF4444;
            z-index: 5;
        }}

        .gauge-setpoint {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #F59E0B;
            border-right: 1px dashed #000;
            z-index: 4;
        }}

        .gauge-labels {{
            display: flex;
            justify-content: space-between;
            font-size: 0.68rem;
            color: var(--text-muted);
        }}

        /* SCADA Alarm Table */
        .alarm-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .alarm-table th {{
            background: var(--bg-panel-header);
            color: var(--text-muted);
            text-align: left;
            padding: 0.4rem 0.6rem;
            border-bottom: 1px solid var(--border-primary);
            font-weight: 600;
            text-transform: uppercase;
            font-size: 0.68rem;
        }}

        .alarm-table td {{
            padding: 0.45rem 0.6rem;
            border-bottom: 1px solid #141C2B;
            color: var(--text-secondary);
        }}

        .alarm-table tr:hover td {{
            background: #141C2C;
        }}

        .alarm-row.urgent td {{
            color: #EF4444;
            font-weight: 600;
        }}

        .alarm-row.high td {{
            color: #F59E0B;
            font-weight: 500;
        }}

        .alarm-row.normal td {{
            color: #10B981;
        }}

        .alarm-badge {{
            display: inline-block;
            padding: 1px 5px;
            border-radius: 2px;
            font-size: 0.65rem;
            font-weight: 700;
            text-transform: uppercase;
        }}

        .alarm-badge.urgent {{ background: #EF4444; color: #FFFFFF; }}
        .alarm-badge.high {{ background: #F59E0B; color: #000000; }}
        .alarm-badge.normal {{ background: #10B981; color: #000000; }}
        .alarm-badge.info {{ background: #38BDF8; color: #000000; }}

        /* Screen 2: Trends 2x2 Grid */
        .trends-grid {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 1rem;
            flex: 1;
            min-height: 640px;
        }}

        .chart-box {{
            flex: 1;
            position: relative;
            min-height: 250px;
        }}

        /* Screen 3: Fleet Matrix */
        .fleet-controls-bar {{
            background: var(--bg-panel-header);
            border-bottom: 1px solid var(--border-primary);
            padding: 0.5rem 0.85rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
        }}

        .filter-group {{
            display: flex;
            align-items: center;
            gap: 0.35rem;
        }}

        .fleet-search {{
            background: #0A0E18;
            border: 1px solid var(--border-primary);
            color: #FFFFFF;
            padding: 0.25rem 0.6rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            border-radius: 2px;
            width: 200px;
            outline: none;
        }}

        .fleet-search:focus {{
            border-color: #38BDF8;
        }}

        .fleet-table-container {{
            flex: 1;
            overflow-y: auto;
            max-height: 620px;
        }}

        .fleet-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .fleet-table th {{
            background: #141B2A;
            color: var(--text-muted);
            text-align: left;
            padding: 0.5rem 0.75rem;
            border-bottom: 2px solid var(--border-primary);
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 5;
            text-transform: uppercase;
            font-size: 0.68rem;
        }}

        .fleet-table td {{
            padding: 0.45rem 0.75rem;
            border-bottom: 1px solid #141C2B;
            color: var(--text-secondary);
        }}

        .fleet-table tr:hover td {{
            background: #151E30;
            color: #FFFFFF;
        }}

        .soc-bar-container {{
            width: 120px;
            height: 10px;
            background: #1E293B;
            border-radius: 2px;
            overflow: hidden;
            position: relative;
            display: inline-block;
            vertical-align: middle;
            margin-right: 0.5rem;
        }}

        .soc-bar-fill {{
            height: 100%;
            background: var(--scada-normal);
            border-radius: 1px;
        }}

        .soc-bar-reserve {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 70%;
            width: 2px;
            background: #EF4444;
            z-index: 2;
        }}

        .tag-pill {{
            padding: 1px 6px;
            border-radius: 2px;
            font-size: 0.65rem;
            font-weight: 700;
            display: inline-block;
        }}

        .tag-pill.participating {{ background: rgba(16, 185, 129, 0.15); color: #10B981; border: 1px solid rgba(16, 185, 129, 0.3); }}
        .tag-pill.optout {{ background: rgba(245, 158, 11, 0.15); color: #F59E0B; border: 1px solid rgba(245, 158, 11, 0.3); }}
        .tag-pill.passive {{ background: rgba(100, 116, 139, 0.15); color: #94A3B8; border: 1px solid rgba(100, 116, 139, 0.3); }}

        /* Screen 4: DISCOM Directive & Economics */
        .directive-grid {{
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 1rem;
            flex: 1;
        }}

        .action-plan-banner {{
            background: #080D16;
            border: 1px solid var(--border-secondary);
            border-left: 4px solid var(--schneider-green);
            padding: 1rem;
            border-radius: 2px;
            margin-bottom: 1rem;
        }}

        .directive-command {{
            font-family: var(--font-mono);
            font-size: 1.15rem;
            font-weight: 700;
            color: #FFFFFF;
            margin: 0.5rem 0;
            letter-spacing: 0.02em;
        }}

        .matrix-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            margin-top: 0.5rem;
        }}

        .matrix-table th {{
            background: var(--bg-panel-header);
            color: var(--text-muted);
            text-align: left;
            padding: 0.5rem;
            border-bottom: 1px solid var(--border-primary);
            font-size: 0.68rem;
        }}

        .matrix-table td {{
            padding: 0.5rem;
            border-bottom: 1px solid #141C2B;
            color: var(--text-secondary);
        }}

        .matrix-table tr.highlight td {{
            background: rgba(61, 205, 88, 0.08);
            color: #FFFFFF;
            font-weight: 600;
        }}

        .key-value-list {{
            display: flex;
            flex-direction: column;
            gap: 0.5rem;
            margin-top: 0.5rem;
        }}

        .kv-item {{
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 0.5rem;
            background: #0C121D;
            border: 1px solid var(--border-primary);
            border-radius: 2px;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .kv-item .label {{
            color: var(--text-muted);
        }}

        .kv-item .value {{
            color: #FFFFFF;
            font-weight: 600;
        }}

        .kv-item .value.accent {{
            color: #00D68F;
        }}

        /* Industrial Footer */
        .scada-footer {{
            background: #080C14;
            border-top: 1px solid var(--border-primary);
            padding: 0.35rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--font-mono);
            font-size: 0.68rem;
            color: var(--text-muted);
            z-index: 100;
        }}

        .footer-left {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}

        .footer-right {{
            display: flex;
            align-items: center;
            gap: 1rem;
        }}
    </style>
</head>
<body>

    <!-- SCADA Top Masthead -->
    <header class="scada-masthead">
        <div class="brand-section">
            <div class="schneider-badge">
                <svg width="14" height="14" viewBox="0 0 24 24" fill="currentColor">
                    <path d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
                </svg>
                <span>SCHNEIDER ELECTRIC</span>
            </div>
            <div class="app-title-cluster">
                <div class="app-title">
                    SAANJH <span class="tag">SCADA / HMI v2.6</span>
                </div>
            </div>
        </div>

        <div class="feeder-selector-box">
            <span class="asset-label">Substation:</span>
            <span class="asset-val">33/11 kV SS-04</span>
            <span style="color:var(--border-secondary)">|</span>
            <span class="asset-label">Feeder:</span>
            <span class="asset-val">FDR-023</span>
            <span style="color:var(--border-secondary)">|</span>
            <span class="asset-label">Transformer:</span>
            <span class="asset-val">DT-100KVA-04 (100 kVA / 95 kW)</span>
        </div>

        <div class="masthead-right">
            <div class="comm-status">
                <div class="comm-dot"></div>
                <span>IEC 60870-5-104: ONLINE (24ms)</span>
            </div>
            <div class="sys-clock" id="wall-clock">2026-10-03 16:00:00 IST</div>
        </div>
    </header>

    <!-- Operational Telemetry Annunciator Ribbon (ISA-101 High Performance) -->
    <section class="scada-telemetry-ribbon">
        <!-- 1. Feeder Demand -->
        <div class="telemetry-cell">
            <div class="cell-tag">
                <span>Feeder Active Load</span>
                <span class="indicator normal" id="ind-load"></span>
            </div>
            <div class="cell-value-row">
                <span class="cell-val" id="kpi-load-val">109.2</span>
                <span class="cell-unit">kW</span>
            </div>
            <div class="cell-delta">
                <span class="delta-good" id="kpi-load-delta">↓ 44.95 kW (-29.2%)</span>
                <span class="delta-neutral">vs 154.1 kW base</span>
            </div>
        </div>

        <!-- 2. Transformer Loading -->
        <div class="telemetry-cell">
            <div class="cell-tag">
                <span>TX Loading (100 kVA)</span>
                <span class="indicator alarm" id="ind-tx"></span>
            </div>
            <div class="cell-value-row">
                <span class="cell-val" id="kpi-tx-val">114.9</span>
                <span class="cell-unit">%</span>
            </div>
            <div class="cell-delta">
                <span class="delta-good" id="kpi-tx-delta">↓ 30 min stress cut</span>
                <span class="delta-neutral">162.2% base peak</span>
            </div>
        </div>

        <!-- 3. Flexibility Dispatched -->
        <div class="telemetry-cell">
            <div class="cell-tag">
                <span>VCB Flexibility Dispatched</span>
                <span class="indicator flex"></span>
            </div>
            <div class="cell-value-row">
                <span class="cell-val" id="kpi-flex-val">56.25</span>
                <span class="cell-unit">kW</span>
            </div>
            <div class="cell-delta">
                <span class="delta-good" id="kpi-flex-delta">61.57 kWh (98.5% ratio)</span>
            </div>
        </div>

        <!-- 4. Feeder Tail Voltage -->
        <div class="telemetry-cell">
            <div class="cell-tag">
                <span>Feeder Tail Node 60</span>
                <span class="indicator volt"></span>
            </div>
            <div class="cell-value-row">
                <span class="cell-val" id="kpi-volt-val">226.5</span>
                <span class="cell-unit">V RMS</span>
            </div>
            <div class="cell-delta">
                <span class="delta-good">0 Violations (100% fixed)</span>
                <span class="delta-bad">219.7V base sag</span>
            </div>
        </div>

        <!-- 5. Participating Fleet -->
        <div class="telemetry-cell">
            <div class="cell-tag">
                <span>Aggregated Fleet</span>
                <span class="indicator normal"></span>
            </div>
            <div class="cell-value-row">
                <span class="cell-val" id="kpi-fleet-val">39 / 42</span>
                <span class="cell-unit">BESS</span>
            </div>
            <div class="cell-delta">
                <span class="delta-neutral">3 Opted Out (H-18,55,56)</span>
            </div>
        </div>

        <!-- 6. Economic Efficiency -->
        <div class="telemetry-cell">
            <div class="cell-tag">
                <span>CapEx Efficiency</span>
                <span class="indicator normal"></span>
            </div>
            <div class="cell-value-row">
                <span class="cell-val">₹7,068</span>
                <span class="cell-unit">/ kW</span>
            </div>
            <div class="cell-delta">
                <span class="delta-good">84% CapEx savings</span>
                <span class="delta-neutral">vs ₹45k utility BESS</span>
            </div>
        </div>
    </section>

    <!-- Simulation Time Travel & Scrubber Bar -->
    <section class="scada-scrubber-ribbon">
        <div class="playback-controls">
            <button class="scada-btn" id="btn-step-back" title="Previous 5-min step">◀◀</button>
            <button class="scada-btn active" id="btn-play-pause">❚❚ PAUSE</button>
            <button class="scada-btn" id="btn-step-fwd" title="Next 5-min step">▶▶</button>
            <button class="scada-btn" id="btn-reset">⟲ RESET</button>
        </div>

        <div class="time-slider-container">
            <span style="color:var(--text-muted)">TIMESTEP:</span>
            <input type="range" class="time-slider" id="time-slider" min="0" max="71" value="37" step="1">
            <div class="time-readout" id="active-time-readout">19:05 IST (PEAK)</div>
        </div>

        <div class="event-shortcuts">
            <span style="color:var(--text-muted)">JUMP TO:</span>
            <button class="scada-btn" id="jump-solar-cliff" style="color:var(--scada-solar)">18:30 SOLAR CLIFF</button>
            <button class="scada-btn alert" id="jump-peak">19:05 MAX OVERLOAD</button>
            <button class="scada-btn" id="jump-recovery">20:30 RECOVERY</button>
        </div>
    </section>

    <!-- F-Key Navigation Tabs -->
    <nav class="scada-nav-tabs">
        <button class="nav-tab active" data-tab="tab-mimic">
            <span class="f-key">F1</span>
            <span>SLD & FEColorScheme MIMIC</span>
        </button>
        <button class="nav-tab" data-tab="tab-trends">
            <span class="f-key">F2</span>
            <span>SCADA TRENDS & TELEMETRY</span>
        </button>
        <button class="nav-tab" data-tab="tab-fleet">
            <span class="f-key">F3</span>
            <span>FLEET MATRIX (60 HOMES)</span>
        </button>
        <button class="nav-tab" data-tab="tab-directive">
            <span class="f-key">F4</span>
            <span>DISCOM DIRECTIVE & ECONOMICS</span>
        </button>
    </nav>

    <!-- Main SCADA Workspace -->
    <main class="scada-workspace">

        <!-- VIEWPORT 1: [F1] SLD & MIMIC DIAGRAM -->
        <div class="tab-viewport active" id="tab-mimic">
            <div class="mimic-layout-grid">
                
                <!-- Left: Interactive Feeder Single Line Diagram (SLD) -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <rect x="3" y="3" width="18" height="18" rx="2"/>
                                <line x1="3" y1="9" x2="21" y2="9"/>
                                <line x1="9" y1="21" x2="9" y2="9"/>
                            </svg>
                            <span>FEEDER FDR-023 SINGLE LINE MIMIC DIAGRAM</span>
                        </div>
                        <div class="status-tag active" id="sld-state-tag">DISPATCH MITIGATION ACTIVE</div>
                    </div>
                    
                    <div class="panel-body" style="padding:0; position:relative;">
                        <div class="sld-canvas-container">
                            <svg class="sld-svg" viewBox="0 0 840 480" preserveAspectRatio="xMidYMid meet">
                                <defs>
                                    <linearGradient id="grad-pulse" x1="0%" y1="0%" x2="100%" y2="0%">
                                        <stop offset="0%" stop-color="#38BDF8" stop-opacity="0.8"/>
                                        <stop offset="100%" stop-color="#00D68F" stop-opacity="0.9"/>
                                    </linearGradient>
                                    <filter id="glow-green" x="-20%" y="-20%" width="140%" height="140%">
                                        <feGaussianBlur stdDeviation="3" result="blur" />
                                        <feComposite in="SourceGraphic" in2="blur" operator="over" />
                                    </filter>
                                </defs>

                                <!-- Grid Background Grid Lines -->
                                <pattern id="scada-grid" width="20" height="20" patternUnits="userSpaceOnUse">
                                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255, 255, 255, 0.03)" stroke-width="1"/>
                                </pattern>
                                <rect width="100%" height="100%" fill="url(#scada-grid)"/>

                                <!-- 1. Substation Busbar 11 kV -->
                                <line x1="60" y1="60" x2="220" y2="60" class="busbar energized" />
                                <text x="60" y="45" fill="#38BDF8" font-family="var(--font-mono)" font-size="11" font-weight="700">SUBSTATION 11 kV BUSBAR</text>
                                
                                <!-- Feeder Breaker CB-23 -->
                                <line x1="140" y1="60" x2="140" y2="100" class="feeder-line active" />
                                <rect x="130" y="100" width="20" height="20" fill="#0E1626" stroke="#10B981" stroke-width="2" rx="2"/>
                                <line x1="135" y1="110" x2="145" y2="110" stroke="#10B981" stroke-width="2" />
                                <text x="160" y="114" fill="#94A3B8" font-family="var(--font-mono)" font-size="10">CB-23 [CLOSED]</text>

                                <!-- Down to Distribution Transformer DT-100KVA-04 -->
                                <line x1="140" y1="120" x2="140" y2="160" class="feeder-line active" />
                                
                                <!-- Transformer Symbol (Dual Overlapping Circles Dyn11) -->
                                <g transform="translate(140, 190)">
                                    <circle cx="0" cy="-12" r="18" fill="none" stroke="#38BDF8" stroke-width="2.5" />
                                    <circle cx="0" cy="12" r="18" fill="none" stroke="#00D68F" stroke-width="2.5" />
                                    <text x="32" y="-5" fill="#FFFFFF" font-family="var(--font-mono)" font-size="11" font-weight="700">DT-100KVA-04</text>
                                    <text x="32" y="10" fill="#94A3B8" font-family="var(--font-mono)" font-size="10">11 kV / 415 V Dyn11</text>
                                    <text x="32" y="24" fill="#64748B" font-family="var(--font-mono)" font-size="9">Rated: 100 kVA / 95 kW</text>
                                </g>

                                <!-- 2. Low Voltage Feeder Spine (415V / 240V) -->
                                <line x1="140" y1="220" x2="140" y2="280" class="feeder-line active" />
                                
                                <!-- Main Distribution Spine -->
                                <line x1="140" y1="280" x2="760" y2="280" class="busbar energized" />
                                <text x="150" y="270" fill="#00D68F" font-family="var(--font-mono)" font-size="10" font-weight="600">415V 3-PHASE 4-WIRE FEEDER SPINE (FDR-023)</text>

                                <!-- Active Power Flow Animated Pulses -->
                                <line x1="140" y1="280" x2="760" y2="280" stroke="#00D68F" stroke-width="2" class="pulse-path" id="flow-pulse-line"/>

                                <!-- Feeder Nodes & Clusters -->
                                <!-- Lateral Cluster 1: Nodes 01-15 -->
                                <g transform="translate(260, 280)">
                                    <line x1="0" y1="0" x2="0" y2="60" class="feeder-line active" />
                                    <rect x="-45" y="60" width="90" height="50" fill="#111622" stroke="#1F293D" stroke-width="1.5" rx="2"/>
                                    <text x="-38" y="76" fill="#FFFFFF" font-family="var(--font-mono)" font-size="10" font-weight="700">CLUSTER 1</text>
                                    <text x="-38" y="90" fill="#94A3B8" font-family="var(--font-mono)" font-size="9">Nodes H-01..H-15</text>
                                    <text x="-38" y="102" fill="#10B981" font-family="var(--font-mono)" font-size="8">11 BESS / 3 Solar</text>
                                </g>

                                <!-- Lateral Cluster 2: Nodes 16-30 -->
                                <g transform="translate(420, 280)">
                                    <line x1="0" y1="0" x2="0" y2="60" class="feeder-line active" />
                                    <rect x="-45" y="60" width="90" height="50" fill="#111622" stroke="#1F293D" stroke-width="1.5" rx="2"/>
                                    <text x="-38" y="76" fill="#FFFFFF" font-family="var(--font-mono)" font-size="10" font-weight="700">CLUSTER 2</text>
                                    <text x="-38" y="90" fill="#94A3B8" font-family="var(--font-mono)" font-size="9">Nodes H-16..H-30</text>
                                    <text x="-38" y="102" fill="#F59E0B" font-family="var(--font-mono)" font-size="8">10 BESS (H-18 Opt)</text>
                                </g>

                                <!-- Lateral Cluster 3: Nodes 31-45 -->
                                <g transform="translate(580, 280)">
                                    <line x1="0" y1="0" x2="0" y2="60" class="feeder-line active" />
                                    <rect x="-45" y="60" width="90" height="50" fill="#111622" stroke="#1F293D" stroke-width="1.5" rx="2"/>
                                    <text x="-38" y="76" fill="#FFFFFF" font-family="var(--font-mono)" font-size="10" font-weight="700">CLUSTER 3</text>
                                    <text x="-38" y="90" fill="#94A3B8" font-family="var(--font-mono)" font-size="9">Nodes H-31..H-45</text>
                                    <text x="-38" y="102" fill="#10B981" font-family="var(--font-mono)" font-size="8">10 BESS / 4 Solar</text>
                                </g>

                                <!-- Lateral Cluster 4: Nodes 46-60 (FEEDER TAIL) -->
                                <g transform="translate(740, 280)">
                                    <line x1="0" y1="0" x2="0" y2="60" class="feeder-line active" />
                                    <rect x="-55" y="60" width="105" height="50" fill="#111622" stroke="#38BDF8" stroke-width="1.5" rx="2"/>
                                    <text x="-48" y="76" fill="#38BDF8" font-family="var(--font-mono)" font-size="10" font-weight="700">NODE 60 (TAIL)</text>
                                    <text x="-48" y="90" fill="#94A3B8" font-family="var(--font-mono)" font-size="9">Nodes H-46..H-60</text>
                                    <text x="-48" y="102" fill="#10B981" font-family="var(--font-mono)" font-size="8" id="tail-volt-mimic">226.5 V (0 Sag)</text>
                                </g>

                                <!-- VIRTUAL COMMUNITY BATTERY AGGREGATOR BADGE -->
                                <g transform="translate(420, 390)">
                                    <rect x="-180" y="-30" width="360" height="60" fill="#0C1420" stroke="#00D68F" stroke-width="2" rx="4" filter="url(#glow-green)"/>
                                    <text x="-160" y="-10" fill="#00D68F" font-family="var(--font-mono)" font-size="11" font-weight="700">SAANJH VIRTUAL COMMUNITY BATTERY (VCB)</text>
                                    <text x="-160" y="8" fill="#94A3B8" font-family="var(--font-mono)" font-size="9">42 Aggregated Inverters | Available: 92.55 kW | Dispatched: <tspan id="mimic-disp-kw" fill="#FFFFFF" font-weight="700">56.25 kW</tspan></text>
                                    <text x="-160" y="21" fill="#64748B" font-family="var(--font-mono)" font-size="8">Reserve SOC Limit: ≥70% Protected | Opted Out: 3 Units Safe</text>
                                </g>

                                <!-- Upward Reverse Active Power Flow from VCB during Peak -->
                                <g id="vcb-injection-lines">
                                    <line x1="300" y1="360" x2="300" y2="330" stroke="#00D68F" stroke-width="2" stroke-dasharray="4,4" class="pulse-path"/>
                                    <line x1="420" y1="360" x2="420" y2="330" stroke="#00D68F" stroke-width="2" stroke-dasharray="4,4" class="pulse-path"/>
                                    <line x1="540" y1="360" x2="540" y2="330" stroke="#00D68F" stroke-width="2" stroke-dasharray="4,4" class="pulse-path"/>
                                </g>
                            </svg>
                        </div>
                    </div>
                </div>

                <!-- Right: Asset Health & SCADA Alarm Annunciator Panel -->
                <div style="display:flex; flex-direction:column; gap:1rem;">
                    
                    <!-- Transformer Linear Gauge Widget (React SCADA HMI style) -->
                    <div class="scada-panel">
                        <div class="panel-header">
                            <div class="title-left">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/>
                                </svg>
                                <span>DT-100KVA-04 THERMAL LOADING</span>
                            </div>
                            <span class="status-tag active" id="tx-thermal-tag">NORMAL MITIGATED</span>
                        </div>
                        <div class="panel-body">
                            <div class="linear-gauge-container">
                                <div style="display:flex; justify-content:space-between; margin-bottom:0.2rem;">
                                    <span style="color:var(--text-muted); font-size:0.75rem;">CURRENT LOADING:</span>
                                    <span style="color:#FFFFFF; font-weight:700; font-size:0.9rem;" id="gauge-load-num">109.18 kW / 114.9%</span>
                                </div>
                                <div class="gauge-track">
                                    <div class="gauge-fill" id="tx-gauge-fill" style="width: 71%; background: #00D68F;"></div>
                                    <!-- 85% Warning Setpoint -->
                                    <div class="gauge-setpoint" style="left: 85%;" title="Warning Setpoint 85%"></div>
                                    <!-- 100% Thermal Rating -->
                                    <div class="gauge-threshold" style="left: 95%;" title="Rated Capacity 95 kW (100%)"></div>
                                </div>
                                <div class="gauge-labels">
                                    <span>0 kW</span>
                                    <span>80.75 kW (Safe Limit)</span>
                                    <span>95 kW (Rated)</span>
                                    <span>154 kW (Base Peak)</span>
                                </div>
                            </div>

                            <div class="key-value-list" style="margin-top:0.85rem;">
                                <div class="kv-item">
                                    <span class="label">Baseline Unmanaged Overload:</span>
                                    <span class="value" style="color:#EF4444;">154.14 kW (162.2% Overload)</span>
                                </div>
                                <div class="kv-item">
                                    <span class="label">SAANJH Controlled Peak:</span>
                                    <span class="value accent" id="kv-saanjh-peak">109.18 kW (-44.95 kW Shaved)</span>
                                </div>
                                <div class="kv-item">
                                    <span class="label">Overload Duration:</span>
                                    <span class="value" id="kv-overload-dur">60 min (30 min stress avoided)</span>
                                </div>
                                <div class="kv-item">
                                    <span class="label">Insulation Life Extension:</span>
                                    <span class="value accent">+3.8 Years (Arrhenius Model)</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- SCADA Real-Time Alarm & Event Log -->
                    <div class="scada-panel" style="flex:1;">
                        <div class="panel-header">
                            <div class="title-left">
                                <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                    <path d="M18 8A6 6 0 0 0 6 8c0 7-3 9-3 9h18s-3-2-3-9"/>
                                    <path d="M13.73 21a2 2 0 0 1-3.46 0"/>
                                </svg>
                                <span>SCADA SEQUENCE OF EVENTS (SOE) LOG</span>
                            </div>
                            <span style="font-size:0.68rem; color:var(--text-muted);">AUTO-REFRESH</span>
                        </div>
                        <div class="panel-body" style="padding:0; overflow-y:auto; max-height:220px;">
                            <table class="alarm-table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Sev</th>
                                        <th>Asset</th>
                                        <th>Event Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr class="alarm-row normal">
                                        <td>19:05:00</td>
                                        <td><span class="alarm-badge normal">NORM</span></td>
                                        <td>NODE-60</td>
                                        <td>Tail voltage held at 226.5V RMS (sag averted)</td>
                                    </tr>
                                    <tr class="alarm-row urgent">
                                        <td>19:05:00</td>
                                        <td><span class="alarm-badge urgent">URGT</span></td>
                                        <td>DT-100</td>
                                        <td>Baseline would exceed 154 kW (Mitigated by 56.2 kW)</td>
                                    </tr>
                                    <tr class="alarm-row high">
                                        <td>18:35:00</td>
                                        <td><span class="alarm-badge high">HIGH</span></td>
                                        <td>VCB-EDGE</td>
                                        <td>Dispatch executed: 39 BESS commanded to 56.25 kW</td>
                                    </tr>
                                    <tr class="alarm-row high">
                                        <td>18:30:00</td>
                                        <td><span class="alarm-badge high">HIGH</span></td>
                                        <td>SOLAR-PV</td>
                                        <td>PV Cliff detected: Solar generation drop to 0.0 kW</td>
                                    </tr>
                                    <tr class="alarm-row normal">
                                        <td>16:00:00</td>
                                        <td><span class="alarm-badge info">INFO</span></td>
                                        <td>SYS-COMM</td>
                                        <td>Telecontrol link online. 42 BESS heartbeat OK</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>
            </div>
        </div>

        <!-- VIEWPORT 2: [F2] SCADA TRENDS & TELEMETRY -->
        <div class="tab-viewport" id="tab-trends">
            <div class="trends-grid">
                
                <!-- Chart 1: Active Power & Peak Shaving -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <span style="color:#00D68F;">●</span>
                            <span>TREND 1: FEEDER ACTIVE POWER & PEAK SHAVING PROFILE (kW)</span>
                        </div>
                        <span style="font-size:0.68rem; color:var(--text-muted)">16:00 - 22:00 IST</span>
                    </div>
                    <div class="panel-body">
                        <div class="chart-box">
                            <canvas id="chart-demand"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 2: Feeder Tail Voltage (Node 60) -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <span style="color:#38BDF8;">●</span>
                            <span>TREND 2: FEEDER TAIL VOLTAGE PROFILE — NODE 60 (V RMS)</span>
                        </div>
                        <span class="status-tag active">0 STATUTORY VIOLATIONS</span>
                    </div>
                    <div class="panel-body">
                        <div class="chart-box">
                            <canvas id="chart-voltage"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 3: Flexibility Dispatch vs Availability -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <span style="color:#A855F7;">●</span>
                            <span>TREND 3: VCB FLEXIBILITY DISPATCHED VS FLEET HEADROOM (kW)</span>
                        </div>
                        <span style="font-size:0.68rem; color:var(--text-muted)">39 Active Inverters</span>
                    </div>
                    <div class="panel-body">
                        <div class="chart-box">
                            <canvas id="chart-flex"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 4: XGBoost Loss Convergence -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <span style="color:#F59E0B;">●</span>
                            <span>TREND 4: EDGE XGBOOST LOSS FORECAST ERROR CONVERGENCE</span>
                        </div>
                        <span style="font-size:0.68rem; color:var(--text-muted)">Best Iter: 171 (RMSE 0.546 kW)</span>
                    </div>
                    <div class="panel-body">
                        <div class="chart-box">
                            <canvas id="chart-xgb"></canvas>
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <!-- VIEWPORT 3: [F3] FLEET MATRIX (60 HOMES) -->
        <div class="tab-viewport" id="tab-fleet">
            <div class="scada-panel" style="flex:1;">
                <div class="fleet-controls-bar">
                    <div class="filter-group">
                        <span style="color:var(--text-muted); font-size:0.75rem; margin-right:0.5rem;">FILTER FLEET:</span>
                        <button class="scada-btn active" data-filter="all">ALL (60)</button>
                        <button class="scada-btn" data-filter="battery">BESS FLEET (42)</button>
                        <button class="scada-btn" data-filter="participating">ACTIVE (39)</button>
                        <button class="scada-btn alert" data-filter="optout">OPTED OUT (3)</button>
                        <button class="scada-btn" data-filter="solar">SOLAR PV (15)</button>
                    </div>

                    <div style="display:flex; align-items:center; gap:0.5rem;">
                        <input type="text" class="fleet-search" id="fleet-search-input" placeholder="Search Node ID (e.g. H-18)...">
                        <span style="color:var(--text-muted); font-size:0.75rem;" id="fleet-count-badge">Showing 60 nodes</span>
                    </div>
                </div>

                <div class="fleet-table-container">
                    <table class="fleet-table" id="fleet-matrix-table">
                        <thead>
                            <tr>
                                <th>Node ID</th>
                                <th>BESS Hardware</th>
                                <th>Solar PV</th>
                                <th>Battery SOC (State of Charge)</th>
                                <th>Emergency Reserve</th>
                                <th>Avail Flex (kW)</th>
                                <th>Delivered (kWh)</th>
                                <th>Dispatch Status</th>
                                <th>Incentive Tariff Credit</th>
                            </tr>
                        </thead>
                        <tbody id="fleet-table-body">
                            <!-- Populated dynamically via JS -->
                        </tbody>
                    </table>
                </div>
            </div>
        </div>

        <!-- VIEWPORT 4: [F4] DISCOM DIRECTIVE & ECONOMICS -->
        <div class="tab-viewport" id="tab-directive">
            <div class="directive-grid">
                
                <!-- Left: Official DISCOM Directive -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <polygon points="12 2 15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2"/>
                            </svg>
                            <span>DISCOM FEEDER OPERATOR DISPATCH DIRECTIVE</span>
                        </div>
                        <span class="status-tag active">AUTHORIZED DIRECTIVE</span>
                    </div>
                    <div class="panel-body">
                        
                        <div class="action-plan-banner">
                            <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--schneider-green); font-weight:700;">
                                >> DIRECTIVE ID: DIR-FDR023-20261003-PEAK
                            </div>
                            <div class="directive-command">
                                "DISPATCH 56.2 kW FOR 45 MINUTES VIA SAANJH EDGE"
                            </div>
                            <p style="color:var(--text-secondary); font-size:0.8rem; line-height:1.5;">
                                Pre-emptive peak mitigation order automatically generated for feeder operator verification. Coordinates 39 participating residential inverters across Nodes 01–60 to shave 44.95 kW of coincident evening demand following the 18:30 Solar Cliff.
                            </p>
                        </div>

                        <div class="key-value-list">
                            <div class="kv-item">
                                <span class="label">Target Distribution Feeder:</span>
                                <span class="value">FDR-023 | DT-100KVA-04</span>
                            </div>
                            <div class="kv-item">
                                <span class="label">Trigger Condition:</span>
                                <span class="value" style="color:#F59E0B;">Solar Drop-off at 18:30 (PV Cliff -7.5 kW)</span>
                            </div>
                            <div class="kv-item">
                                <span class="label">Required Grid Relief:</span>
                                <span class="value">56.25 kW for 45 min</span>
                            </div>
                            <div class="kv-item">
                                <span class="label">Aggregated Fleet Availability:</span>
                                <span class="value accent">92.55 kW (164% of request)</span>
                            </div>
                            <div class="kv-item">
                                <span class="label">Dependable Delivery Ratio:</span>
                                <span class="value accent">98.51% (Rigorous Reserve Guarantee)</span>
                            </div>
                            <div class="kv-item">
                                <span class="label">Distribution Technical Loss Saving:</span>
                                <span class="value accent">9.13 kWh Saved (-35.3%)</span>
                            </div>
                        </div>

                        <div style="margin-top:1rem; border-top:1px solid var(--border-primary); padding-top:0.75rem;">
                            <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted); margin-bottom:0.4rem;">
                                OPERATIONAL COMPLIANCE CHECKLIST:
                            </div>
                            <div style="display:flex; flex-direction:column; gap:0.3rem; font-family:var(--font-mono); font-size:0.72rem; color:var(--text-secondary);">
                                <div>☑ Frequency & Phase Synchronization Verified (IEEE 1547 compliant)</div>
                                <div>☑ Consumer Emergency Reserve Floor Enforced (All units ≥70% SOC)</div>
                                <div>☑ Homeowner Privacy & Opt-Out Guaranteed (H-18, H-55, H-56 Protected)</div>
                                <div>☑ Arrhenius Thermal Stress Model Monitored (+3.8 yrs transformer life)</div>
                            </div>
                        </div>

                    </div>
                </div>

                <!-- Right: Economics & CapEx Sensitivity Matrix -->
                <div class="scada-panel">
                    <div class="panel-header">
                        <div class="title-left">
                            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                                <circle cx="12" cy="12" r="10"/>
                                <path d="M16 8h-6a2 2 0 1 0 0 4h4a2 2 0 1 1 0 4H8"/>
                                <path d="M12 18V6"/>
                            </svg>
                            <span>DEPLOYMENT ECONOMICS & SENSITIVITY BENCHMARK</span>
                        </div>
                        <span style="font-size:0.68rem; color:var(--text-muted)">INR (₹)</span>
                    </div>
                    <div class="panel-body">
                        
                        <div style="font-family:var(--font-mono); font-size:0.75rem; color:var(--text-muted); margin-bottom:0.25rem;">
                            THREE-TIER DEPLOYMENT SENSITIVITY SCENARIOS:
                        </div>

                        <table class="matrix-table">
                            <thead>
                                <tr>
                                    <th>Deployment Tier</th>
                                    <th>Total CapEx</th>
                                    <th>Cost / kW</th>
                                    <th>Cost / Home</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Low-Cost Mass Scale</td>
                                    <td>₹1,60,200</td>
                                    <td style="color:#00D68F; font-weight:700;">₹3,563</td>
                                    <td>₹4,107</td>
                                </tr>
                                <tr class="highlight">
                                    <td style="color:#00D68F;">Base Prototype Scale</td>
                                    <td>₹3,17,767</td>
                                    <td style="color:#00D68F; font-weight:700;">₹7,068</td>
                                    <td>₹8,147</td>
                                </tr>
                                <tr>
                                    <td>High-Contingency Pilot</td>
                                    <td>₹4,37,500</td>
                                    <td>₹9,732</td>
                                    <td>₹11,217</td>
                                </tr>
                            </tbody>
                        </table>

                        <div style="margin-top:1rem; background:#080D16; border:1px solid var(--border-primary); padding:0.85rem; border-radius:2px;">
                            <div style="font-family:var(--font-mono); font-size:0.75rem; font-weight:700; color:#FFFFFF; margin-bottom:0.5rem;">
                                ARCHITECTURAL COST COMPARISON:
                            </div>
                            <div class="key-value-list">
                                <div class="kv-item">
                                    <span class="label">Central Utility Substation BESS (50 kWh):</span>
                                    <span class="value" style="color:#EF4444;">₹45,000 / kW (₹22,50,000)</span>
                                </div>
                                <div class="kv-item">
                                    <span class="label">SAANJH Distributed Inverter Retrofit:</span>
                                    <span class="value accent">₹7,068 / kW (₹3,17,767)</span>
                                </div>
                                <div class="kv-item">
                                    <span class="label">Net Capital Cost Savings:</span>
                                    <span class="value accent">84.3% (₹19,32,233 Avoided)</span>
                                </div>
                                <div class="kv-item">
                                    <span class="label">Substation Real Estate / Land Required:</span>
                                    <span class="value accent">0 sq. meters (Zero Land Acquisition)</span>
                                </div>
                            </div>
                        </div>

                    </div>
                </div>

            </div>
        </div>

    </main>

    <!-- Industrial SCADA Bottom Telemetry Bar -->
    <footer class="scada-footer">
        <div class="footer-left">
            <span>STATION: SAANJH-EDGE-DISPATCHER</span>
            <span style="color:var(--border-secondary)">|</span>
            <span>MODEL: XGBOOST RESIDUAL FORECASTER (VALIDATION RMSE: 0.546 kW)</span>
            <span style="color:var(--border-secondary)">|</span>
            <span>PYPSA VALIDATION: CONVERGED (0 UNRESOLVED FLOWS)</span>
        </div>
        <div class="footer-right">
            <span>IEEE 1547 / CEA GRID CODE COMPLIANT</span>
            <span style="color:var(--border-secondary)">|</span>
            <span style="color:var(--schneider-green)">SCHNEIDER ELECTRIC YUVA YODHA HACKATHON 2026</span>
        </div>
    </footer>

    <!-- CANONICAL DATA INJECTION & RUNTIME ENGINE -->
    <script>
        // Canonical Datasets embedded from repository simulation results
        const EMBEDDED_BUNDLE = {json.dumps(timeseries_data)};
        const EMBEDDED_FLEET = {json.dumps(fleet_data)};
        const EMBEDDED_COMPARISON = {json.dumps(comparison_data)};
        const EMBEDDED_DISCOM = {json.dumps(discom_data)};
        const EMBEDDED_ECON = {json.dumps(economics_data)};

        let currentBundle = EMBEDDED_BUNDLE;
        let currentFleet = EMBEDDED_FLEET;
        let currentStep = 37; // 19:05 Peak by default
        let isPlaying = false;
        let playInterval = null;
        let charts = {{}};

        // Initialize application on DOM load
        document.addEventListener('DOMContentLoaded', () => {{
            setupNavigation();
            setupPlayback();
            setupFleetTable(currentFleet);
            initCharts(currentBundle);
            updateTimestep(currentStep);
            startClock();
        }});

        function startClock() {{
            const clockEl = document.getElementById('wall-clock');
            setInterval(() => {{
                const d = new Date();
                const pad = (n) => n.toString().padStart(2, '0');
                const timeStr = `${{d.getFullYear()}}-${{pad(d.getMonth()+1)}}-${{pad(d.getDate())}} ${{pad(d.getHours())}}:${{pad(d.getMinutes())}}:${{pad(d.getSeconds())}} IST`;
                if (clockEl) clockEl.innerText = timeStr;
            }}, 1000);
        }}

        // Navigation Tabs Handling
        function setupNavigation() {{
            const tabs = document.querySelectorAll('.nav-tab');
            tabs.forEach(tab => {{
                tab.addEventListener('click', () => {{
                    tabs.forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.tab-viewport').forEach(v => v.classList.remove('active'));
                    
                    tab.classList.add('active');
                    const targetId = tab.getAttribute('data-tab');
                    const targetView = document.getElementById(targetId);
                    if (targetView) targetView.classList.add('active');

                    // Resize charts if switching to trends
                    if (targetId === 'tab-trends') {{
                        setTimeout(() => {{
                            Object.values(charts).forEach(c => c.resize());
                        }}, 50);
                    }}
                }});
            }});
        }}

        // Playback and Scrubber Controls
        function setupPlayback() {{
            const slider = document.getElementById('time-slider');
            const playBtn = document.getElementById('btn-play-pause');
            const stepBack = document.getElementById('btn-step-back');
            const stepFwd = document.getElementById('btn-step-fwd');
            const resetBtn = document.getElementById('btn-reset');
            
            const jumpSolar = document.getElementById('jump-solar-cliff');
            const jumpPeak = document.getElementById('jump-peak');
            const jumpRecovery = document.getElementById('jump-recovery');

            slider.addEventListener('input', (e) => {{
                currentStep = parseInt(e.target.value);
                updateTimestep(currentStep);
            }});

            playBtn.addEventListener('click', togglePlay);
            
            stepBack.addEventListener('click', () => {{
                if (currentStep > 0) {{
                    currentStep--;
                    slider.value = currentStep;
                    updateTimestep(currentStep);
                }}
            }});

            stepFwd.addEventListener('click', () => {{
                if (currentStep < currentBundle.labels.length - 1) {{
                    currentStep++;
                    slider.value = currentStep;
                    updateTimestep(currentStep);
                }}
            }});

            resetBtn.addEventListener('click', () => {{
                currentStep = 0;
                slider.value = currentStep;
                updateTimestep(currentStep);
            }});

            if (jumpSolar) jumpSolar.addEventListener('click', () => jumpTo(30)); // 18:30
            if (jumpPeak) jumpPeak.addEventListener('click', () => jumpTo(37)); // 19:05
            if (jumpRecovery) jumpRecovery.addEventListener('click', () => jumpTo(54)); // 20:30
        }}

        function jumpTo(step) {{
            currentStep = step;
            document.getElementById('time-slider').value = step;
            updateTimestep(step);
        }}

        function togglePlay() {{
            const playBtn = document.getElementById('btn-play-pause');
            isPlaying = !isPlaying;
            if (isPlaying) {{
                playBtn.innerText = '❚❚ PAUSE';
                playBtn.classList.add('active');
                playInterval = setInterval(() => {{
                    if (currentStep < currentBundle.labels.length - 1) {{
                        currentStep++;
                    }} else {{
                        currentStep = 0;
                    }}
                    document.getElementById('time-slider').value = currentStep;
                    updateTimestep(currentStep);
                }}, 600);
            }} else {{
                playBtn.innerText = '▶ PLAY';
                playBtn.classList.remove('active');
                clearInterval(playInterval);
            }}
        }}

        // Update UI dynamically for a given timestep
        function updateTimestep(idx) {{
            const b = currentBundle;
            if (!b || !b.labels[idx]) return;

            const timeLabel = b.labels[idx];
            const loadVal = b.saanjh_load[idx];
            const baseLoad = b.baseline_load[idx];
            const flexVal = b.flex_delivered[idx];
            const voltVal = b.saanjh_voltage[idx];
            const baseVolt = b.baseline_voltage[idx];
            const txPct = b.tx_loading_pct[idx];
            const activeHomes = b.active_homes[idx];
            const deltaKw = (baseLoad - loadVal).toFixed(2);

            // Time readout
            document.getElementById('active-time-readout').innerText = `${{timeLabel}} IST (${{idx === 37 ? 'MAX PEAK' : (idx === 30 ? 'SOLAR CLIFF' : 'DISPATCH')}})`;

            // Top Telemetry Cells
            document.getElementById('kpi-load-val').innerText = loadVal.toFixed(1);
            document.getElementById('kpi-load-delta').innerText = deltaKw > 0 ? `↓ ${{deltaKw}} kW shaved` : `0.0 kW delta`;
            
            document.getElementById('kpi-tx-val').innerText = txPct.toFixed(1);
            document.getElementById('kpi-flex-val').innerText = flexVal.toFixed(2);
            document.getElementById('kpi-volt-val').innerText = voltVal.toFixed(1);

            // Transformer Linear Gauge update
            const gaugeFill = document.getElementById('tx-gauge-fill');
            const gaugeLoadNum = document.getElementById('gauge-load-num');
            if (gaugeFill) {{
                const fillPct = Math.min(100, (loadVal / 154.14) * 100);
                gaugeFill.style.width = fillPct + '%';
                if (txPct > 100) {{
                    gaugeFill.style.background = '#EF4444';
                }} else if (txPct > 85) {{
                    gaugeFill.style.background = '#F59E0B';
                }} else {{
                    gaugeFill.style.background = '#00D68F';
                }}
            }}
            if (gaugeLoadNum) {{
                gaugeLoadNum.innerText = `${{loadVal.toFixed(1)}} kW / ${{txPct.toFixed(1)}}%`;
            }}

            // Mimic SVG dynamic updates
            const mimicDispKw = document.getElementById('mimic-disp-kw');
            if (mimicDispKw) mimicDispKw.innerText = `${{flexVal.toFixed(2)}} kW`;

            const tailVoltMimic = document.getElementById('tail-volt-mimic');
            if (tailVoltMimic) tailVoltMimic.innerText = `${{voltVal.toFixed(1)}} V (${{voltVal < 216 ? 'SAG ALARM' : 'OK'}})`;

            const vcbLines = document.getElementById('vcb-injection-lines');
            if (vcbLines) {{
                vcbLines.style.opacity = flexVal > 0 ? '1' : '0.15';
            }}
        }}

        // Render SCADA Trend Charts
        function initCharts(b) {{
            const commonScales = {{
                x: {{
                    grid: {{ color: 'rgba(255, 255, 255, 0.04)' }},
                    ticks: {{ color: '#64748B', font: {{ family: "'JetBrains Mono', monospace", size: 10 }} }}
                }},
                y: {{
                    grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                    ticks: {{ color: '#64748B', font: {{ family: "'JetBrains Mono', monospace", size: 10 }} }}
                }}
            }};

            const commonOptions = (title) => ({{
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{
                    legend: {{ labels: {{ color: '#94A3B8', font: {{ family: "'Inter', sans-serif", size: 11 }} }} }},
                    tooltip: {{
                        backgroundColor: '#0F172A',
                        titleColor: '#FFFFFF',
                        bodyColor: '#94A3B8',
                        borderColor: '#1E293B',
                        borderWidth: 1,
                        padding: 8
                    }}
                }},
                scales: commonScales
            }});

            // 1. Demand Chart
            const ctx1 = document.getElementById('chart-demand').getContext('2d');
            charts.demand = new Chart(ctx1, {{
                type: 'line',
                data: {{
                    labels: b.labels,
                    datasets: [
                        {{
                            label: 'Baseline Unmanaged Load (kW)',
                            data: b.baseline_load,
                            borderColor: '#EF4444',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointRadius: 0,
                            fill: false
                        }},
                        {{
                            label: 'SAANJH Controlled Load (kW)',
                            data: b.saanjh_load,
                            borderColor: '#00D68F',
                            backgroundColor: 'rgba(0, 214, 143, 0.15)',
                            borderWidth: 2.5,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Solar PV Cliff Generation (kW)',
                            data: b.solar_gen,
                            borderColor: '#F59E0B',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: false
                        }},
                        {{
                            label: 'Transformer Safe Thermal Limit (80.75 kW)',
                            data: b.labels.map(() => 80.75),
                            borderColor: '#64748B',
                            borderWidth: 1.5,
                            borderDash: [8, 4],
                            pointRadius: 0,
                            fill: false
                        }}
                    ]
                }},
                options: commonOptions('Active Power (kW)')
            }});

            // 2. Voltage Chart
            const ctx2 = document.getElementById('chart-voltage').getContext('2d');
            charts.voltage = new Chart(ctx2, {{
                type: 'line',
                data: {{
                    labels: b.labels,
                    datasets: [
                        {{
                            label: 'Baseline Sag (Node 60)',
                            data: b.baseline_voltage,
                            borderColor: '#EF4444',
                            borderWidth: 2,
                            borderDash: [4, 4],
                            pointRadius: 0
                        }},
                        {{
                            label: 'SAANJH Stabilized Voltage (Node 60)',
                            data: b.saanjh_voltage,
                            borderColor: '#38BDF8',
                            backgroundColor: 'rgba(56, 189, 248, 0.12)',
                            borderWidth: 2.5,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Statutory Lower Limit (216V)',
                            data: b.labels.map(() => 216),
                            borderColor: '#F59E0B',
                            borderWidth: 1.5,
                            borderDash: [6, 4],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: {{
                    ...commonOptions('RMS Volts'),
                    scales: {{
                        ...commonScales,
                        y: {{ ...commonScales.y, min: 212, max: 242 }}
                    }}
                }}
            }});

            // 3. Flex Chart
            const ctx3 = document.getElementById('chart-flex').getContext('2d');
            charts.flex = new Chart(ctx3, {{
                type: 'line',
                data: {{
                    labels: b.labels,
                    datasets: [
                        {{
                            label: 'Flexibility Dispatched (kW)',
                            data: b.flex_delivered,
                            borderColor: '#00D68F',
                            backgroundColor: 'rgba(0, 214, 143, 0.25)',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Total Available Fleet Flex (kW)',
                            data: b.flex_available,
                            borderColor: '#A855F7',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: commonOptions('Power (kW)')
            }});

            // 4. XGBoost Loss Chart
            const ctx4 = document.getElementById('chart-xgb').getContext('2d');
            charts.xgb = new Chart(ctx4, {{
                type: 'line',
                data: {{
                    labels: b.xgb_iterations.map(i => 'Iter ' + i),
                    datasets: [
                        {{
                            label: 'Validation RMSE (kW)',
                            data: b.xgb_val_metric,
                            borderColor: '#00D68F',
                            borderWidth: 2.5,
                            pointRadius: 0
                        }},
                        {{
                            label: 'Training RMSE (kW)',
                            data: b.xgb_train_metric,
                            borderColor: '#64748B',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: commonOptions('Loss (RMSE kW)')
            }});
        }}

        // Setup 60-Household Fleet Matrix Table
        function setupFleetTable(fleet) {{
            const tbody = document.getElementById('fleet-table-body');
            const searchInput = document.getElementById('fleet-search-input');
            const countBadge = document.getElementById('fleet-count-badge');
            const filterBtns = document.querySelectorAll('.filter-group .scada-btn');

            let activeFilter = 'all';

            function renderTable() {{
                const searchTxt = searchInput.value.trim().toUpperCase();
                tbody.innerHTML = '';
                
                const filtered = fleet.filter(h => {{
                    // Filter tag
                    if (activeFilter === 'battery' && !h.has_battery) return false;
                    if (activeFilter === 'participating' && !h.participated) return false;
                    if (activeFilter === 'optout' && !h.opted_out) return false;
                    if (activeFilter === 'solar' && !h.has_solar) return false;

                    // Search text
                    if (searchTxt && !h.id.includes(searchTxt)) return false;

                    return true;
                }});

                countBadge.innerText = `Showing ${{filtered.length}} of 60 nodes`;

                filtered.forEach(h => {{
                    const tr = document.createElement('tr');
                    
                    const socPct = (h.final_soc * 100).toFixed(0);
                    const socColor = h.final_soc >= 0.8 ? '#10B981' : (h.final_soc >= 0.7 ? '#F59E0B' : '#EF4444');
                    
                    let statusBadge = '<span class="tag-pill passive">PASSIVE LOAD</span>';
                    if (h.opted_out) {{
                        statusBadge = '<span class="tag-pill optout">OPTED OUT</span>';
                    }} else if (h.participated) {{
                        statusBadge = '<span class="tag-pill participating">PARTICIPATING</span>';
                    }}

                    tr.innerHTML = `
                        <td style="font-weight:700; color:#FFFFFF;">${{h.id}}</td>
                        <td>${{h.has_battery ? '<span style="color:#00D68F;">Installed (4.0 kWh)</span>' : '<span style="color:#64748B;">None</span>'}}</td>
                        <td>${{h.has_solar ? '<span style="color:#F59E0B;">Installed (1.5 kWp)</span>' : '<span style="color:#64748B;">None</span>'}}</td>
                        <td>
                            <div class="soc-bar-container">
                                <div class="soc-bar-fill" style="width: ${{socPct}}%; background: ${{socColor}};"></div>
                                <div class="soc-bar-reserve" title="Reserve Floor 70%"></div>
                            </div>
                            <span>${{(h.init_soc * 100).toFixed(0)}}% → ${{socPct}}%</span>
                        </td>
                        <td style="color:#EF4444; font-weight:600;">70.0% Reserve Floor</td>
                        <td>${{h.avail_kw.toFixed(2)}} kW</td>
                        <td style="font-weight:600; color:#FFFFFF;">${{h.delivered_kwh.toFixed(3)}} kWh</td>
                        <td>${{statusBadge}}</td>
                        <td style="color:#00D68F; font-weight:700;">₹${{h.comp_inr.toFixed(2)}}</td>
                    `;
                    tbody.appendChild(tr);
                }});
            }}

            filterBtns.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    filterBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    activeFilter = btn.getAttribute('data-filter');
                    renderTable();
                }});
            }});

            searchInput.addEventListener('input', renderTable);
            renderTable();
        }}
    </script>
</body>
</html>
'''

with open('docs/index.html', 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully generated docs/index.html ({len(html_content)} bytes)")
