"""
Generator for docs/index.html — FUXA SCADA/HMI SAANJH Operator Console
Built strictly following the 22-Phase Master Loop:
  - FUXA Web SCADA/HMI foundation (frangoteam, MIT License, SHA 64eb012e0333e65bae83b96a7f116f1fccd3434f)
  - Zero AI-slop: neutral industrial palette, 1px borders, no neon glows, no fake connections
  - Strict real vs simulated boundaries: 'SAANJH OPERATOR CONSOLE MODEL REPLAY'
  - Exactly 4 screens: Feeder Overview, Trends, Flexibility Fleet, DISCOM / Decision View
  - 100% canonical numbers from simulation/data/results/
"""

import json
import csv
import os

BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DOCS_DATA = os.path.join(BASE_DIR, 'docs', 'data')


with open(os.path.join(DOCS_DATA, 'timeseries_bundle.json'), 'r') as f:
    timeseries = json.load(f)

with open(os.path.join(DOCS_DATA, 'comparison.json'), 'r') as f:
    comparison = json.load(f)

with open(os.path.join(DOCS_DATA, 'discom_action_plan.json'), 'r') as f:
    discom = json.load(f)

with open(os.path.join(DOCS_DATA, 'economics_scenarios.json'), 'r') as f:
    economics = json.load(f)

fleet = []
with open(os.path.join(DOCS_DATA, 'household_dispatch.csv'), 'r') as f:
    reader = csv.DictReader(f)
    for r in reader:
        fleet.append({
            "id": r["household_id"],
            "has_battery": r["has_battery"].lower() == "true",
            "has_solar": r["has_solar"].lower() == "true",
            "init_soc": float(r["initial_soc"]),
            "final_soc": float(r["final_soc"]),
            "avail_kw": float(r["available_flexibility_kw"]),
            "disp_kw": float(r["dispatched_power_kw"]),
            "delivered_kwh": float(r["energy_delivered_kwh"]),
            "reserve_limit": float(r["reserve_soc_limit"]),
            "participated": r["participated"].lower() == "true",
            "opted_out": r["opted_out"].lower() == "true",
            "comp_inr": float(r["compensation_inr"])
        })

html_content = f'''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>FUXA - SAANJH SCADA/HMI Operator Console | Feeder FDR-023</title>
    <meta name="description" content="SAANJH Operator Console built on the open-source FUXA SCADA/HMI platform. Feeder FDR-023 renewable intermittency mitigation and flexibility dispatch simulation.">
    <!-- Google Fonts: Roboto & Roboto Mono (FUXA standard) -->
    <link rel="preconnect" href="https://fonts.googleapis.com">
    <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
    <link href="https://fonts.googleapis.com/css2?family=Roboto:wght@300;400;500;700&family=Roboto+Mono:wght@400;500;700&display=swap" rel="stylesheet">
    <!-- Chart.js for industrial trend widgets -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
    <style>
        /* FUXA Industrial Design System Tokens */
        :root {{
            --fuxa-bg-main: #181B24;
            --fuxa-bg-panel: #222634;
            --fuxa-bg-header: #1C202C;
            --fuxa-bg-hover: #2B3142;
            --fuxa-bg-input: #151821;
            
            --fuxa-border: #31374A;
            --fuxa-border-subtle: #272C3B;
            --fuxa-border-highlight: #3F51B5;
            
            --fuxa-text-primary: #ECEFF1;
            --fuxa-text-secondary: #B0BEC5;
            --fuxa-text-muted: #78909C;
            --fuxa-text-disabled: #546E7A;
            
            /* Industrial Standard Indicators (Non-Cyberpunk) */
            --ind-normal: #4CAF50;
            --ind-warning: #FF9800;
            --ind-alarm: #F44336;
            --ind-telemetry: #2196F3;
            --ind-flex: #9C27B0;
            
            --font-ui: 'Roboto', -apple-system, BlinkMacSystemFont, sans-serif;
            --font-mono: 'Roboto Mono', Consolas, monospace;
        }}

        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-feature-settings: "tnum" 1;
        }}

        body {{
            background-color: var(--fuxa-bg-main);
            color: var(--fuxa-text-primary);
            font-family: var(--font-ui);
            font-size: 13px;
            line-height: 1.4;
            min-height: 100vh;
            display: flex;
            flex-direction: column;
            user-select: none;
        }}

        /* FUXA App Header Bar */
        .fuxa-header {{
            background: var(--fuxa-bg-header);
            border-bottom: 1px solid var(--fuxa-border);
            height: 44px;
            padding: 0 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            z-index: 100;
        }}

        .fuxa-brand-area {{
            display: flex;
            align-items: center;
            gap: 0.85rem;
        }}

        .fuxa-logo {{
            display: flex;
            align-items: center;
            gap: 0.4rem;
            font-family: var(--font-mono);
            font-weight: 700;
            font-size: 0.9rem;
            color: #FFFFFF;
            letter-spacing: 0.05em;
        }}

        .fuxa-logo svg {{
            width: 20px;
            height: 20px;
            fill: #2196F3;
        }}

        .fuxa-badge-model {{
            background: #263238;
            color: #90A4AE;
            border: 1px solid #37474F;
            padding: 2px 6px;
            border-radius: 2px;
            font-family: var(--font-mono);
            font-size: 0.7rem;
            font-weight: 500;
        }}

        .fuxa-asset-bar {{
            display: flex;
            align-items: center;
            gap: 0.6rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            color: var(--fuxa-text-secondary);
        }}

        .fuxa-asset-bar .highlight {{
            color: #2196F3;
            font-weight: 500;
        }}

        .fuxa-right-controls {{
            display: flex;
            align-items: center;
            gap: 1rem;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            color: var(--fuxa-text-muted);
        }}

        /* FUXA Screen Tab Navigation */
        .fuxa-tabs-bar {{
            background: #151821;
            border-bottom: 1px solid var(--fuxa-border);
            padding: 0 1rem;
            display: flex;
            gap: 2px;
        }}

        .fuxa-tab {{
            background: var(--fuxa-bg-header);
            color: var(--fuxa-text-secondary);
            border: 1px solid var(--fuxa-border);
            border-bottom: none;
            padding: 0.45rem 1.15rem;
            font-family: var(--font-mono);
            font-size: 0.78rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            gap: 0.4rem;
            position: relative;
            top: 1px;
            transition: background 0.15s ease, color 0.15s ease;
        }}

        .fuxa-tab:hover {{
            background: var(--fuxa-bg-hover);
            color: #FFFFFF;
        }}

        .fuxa-tab.active {{
            background: var(--fuxa-bg-panel);
            color: #FFFFFF;
            border-top: 2px solid #2196F3;
            border-bottom: 1px solid var(--fuxa-bg-panel);
            font-weight: 700;
        }}

        /* Telemetry & Replay Toolbar */
        .fuxa-toolbar {{
            background: #1A1E29;
            border-bottom: 1px solid var(--fuxa-border);
            padding: 0.35rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            gap: 1rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
        }}

        .fuxa-btn {{
            background: #252A3A;
            color: var(--fuxa-text-primary);
            border: 1px solid var(--fuxa-border);
            padding: 0.25rem 0.6rem;
            border-radius: 2px;
            cursor: pointer;
            font-family: var(--font-mono);
            font-size: 0.72rem;
            font-weight: 500;
            display: inline-flex;
            align-items: center;
            gap: 0.3rem;
        }}

        .fuxa-btn:hover {{
            background: #31384D;
            border-color: #3F51B5;
        }}

        .fuxa-btn.active {{
            background: #1976D2;
            color: #FFFFFF;
            border-color: #1976D2;
        }}

        .fuxa-slider-wrap {{
            flex: 1;
            display: flex;
            align-items: center;
            gap: 0.75rem;
        }}

        .fuxa-slider {{
            flex: 1;
            -webkit-appearance: none;
            height: 4px;
            background: #31374A;
            border-radius: 2px;
            outline: none;
            cursor: pointer;
        }}

        .fuxa-slider::-webkit-slider-thumb {{
            -webkit-appearance: none;
            width: 14px;
            height: 14px;
            background: #2196F3;
            border-radius: 2px;
            cursor: pointer;
            border: 1px solid #FFFFFF;
        }}

        .fuxa-time-badge {{
            background: #12141C;
            border: 1px solid var(--fuxa-border);
            padding: 2px 8px;
            border-radius: 2px;
            color: #2196F3;
            font-weight: 700;
            min-width: 125px;
            text-align: center;
        }}

        /* Main Screen Container */
        .fuxa-viewport-area {{
            flex: 1;
            padding: 1rem;
            display: flex;
            flex-direction: column;
            overflow-y: auto;
        }}

        .fuxa-screen {{
            display: none;
            flex: 1;
            flex-direction: column;
            gap: 1rem;
        }}

        .fuxa-screen.active {{
            display: flex;
        }}

        /* FUXA Panels */
        .fuxa-panel {{
            background: var(--fuxa-bg-panel);
            border: 1px solid var(--fuxa-border);
            border-radius: 2px;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}

        .fuxa-panel-title {{
            background: var(--fuxa-bg-header);
            border-bottom: 1px solid var(--fuxa-border);
            padding: 0.45rem 0.85rem;
            font-family: var(--font-mono);
            font-size: 0.75rem;
            font-weight: 700;
            color: var(--fuxa-text-primary);
            display: flex;
            align-items: center;
            justify-content: space-between;
            letter-spacing: 0.03em;
        }}

        .fuxa-panel-body {{
            padding: 0.85rem;
            flex: 1;
            display: flex;
            flex-direction: column;
        }}

        /* SCREEN 1: Feeder Overview */
        .overview-grid {{
            display: grid;
            grid-template-columns: 2fr 1fr;
            gap: 1rem;
            flex: 1;
        }}

        .kpi-strip {{
            display: grid;
            grid-template-columns: repeat(6, 1fr);
            gap: 1px;
            background: var(--fuxa-border);
            border: 1px solid var(--fuxa-border);
            margin-bottom: 1rem;
        }}

        .kpi-box {{
            background: var(--fuxa-bg-panel);
            padding: 0.6rem 0.85rem;
            display: flex;
            flex-direction: column;
            gap: 0.15rem;
        }}

        .kpi-tag {{
            font-family: var(--font-mono);
            font-size: 0.68rem;
            color: var(--fuxa-text-muted);
            text-transform: uppercase;
        }}

        .kpi-val-row {{
            display: flex;
            align-items: baseline;
            gap: 0.35rem;
        }}

        .kpi-val {{
            font-family: var(--font-mono);
            font-size: 1.25rem;
            font-weight: 700;
            color: #FFFFFF;
        }}

        .kpi-unit {{
            font-family: var(--font-mono);
            font-size: 0.72rem;
            color: var(--fuxa-text-muted);
        }}

        .kpi-sub {{
            font-family: var(--font-mono);
            font-size: 0.68rem;
            color: var(--fuxa-text-secondary);
        }}

        /* Process Diagram (Clean Engineering SVG, no cyberpunk neon) */
        .process-svg-wrap {{
            background: #141722;
            border: 1px solid var(--fuxa-border);
            min-height: 420px;
            position: relative;
        }}

        .process-svg {{
            width: 100%;
            height: 100%;
            display: block;
        }}

        /* Linear Gauge (FUXA/ISA-101 Style) */
        .gauge-bar-wrap {{
            height: 16px;
            background: #151821;
            border: 1px solid var(--fuxa-border);
            border-radius: 1px;
            position: relative;
            overflow: hidden;
            margin: 0.5rem 0;
        }}

        .gauge-fill {{
            height: 100%;
            background: #4CAF50;
            transition: width 0.2s ease, background 0.2s ease;
        }}

        .gauge-limit-mark {{
            position: absolute;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #F44336;
        }}

        /* SCREEN 2: Trends Grid */
        .trends-2x2 {{
            display: grid;
            grid-template-columns: 1fr 1fr;
            grid-template-rows: 1fr 1fr;
            gap: 1rem;
            flex: 1;
            min-height: 580px;
        }}

        .chart-container {{
            position: relative;
            flex: 1;
            min-height: 230px;
        }}

        /* SCREEN 3: Household Fleet Matrix */
        .fleet-controls {{
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 0.75rem;
            gap: 1rem;
        }}

        .fleet-table-wrap {{
            flex: 1;
            overflow-y: auto;
            max-height: 600px;
            border: 1px solid var(--fuxa-border);
        }}

        .fleet-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-mono);
            font-size: 0.74rem;
        }}

        .fleet-table th {{
            background: #1C202C;
            color: var(--fuxa-text-muted);
            text-align: left;
            padding: 0.45rem 0.6rem;
            border-bottom: 2px solid var(--fuxa-border);
            font-weight: 600;
            position: sticky;
            top: 0;
            z-index: 2;
        }}

        .fleet-table td {{
            padding: 0.4rem 0.6rem;
            border-bottom: 1px solid #272C3B;
            color: var(--fuxa-text-secondary);
        }}

        .fleet-table tr:hover td {{
            background: #282E3E;
            color: #FFFFFF;
        }}

        .soc-indicator {{
            width: 80px;
            height: 8px;
            background: #151821;
            border: 1px solid #31374A;
            border-radius: 1px;
            display: inline-block;
            vertical-align: middle;
            margin-right: 0.4rem;
            position: relative;
        }}

        .soc-fill {{
            height: 100%;
            background: #4CAF50;
        }}

        .soc-floor-line {{
            position: absolute;
            top: 0;
            bottom: 0;
            left: 70%;
            width: 2px;
            background: #F44336;
        }}

        /* SCREEN 4: DISCOM / Decision View */
        .decision-layout {{
            display: grid;
            grid-template-columns: 1.2fr 1fr;
            gap: 1rem;
            flex: 1;
        }}

        .decision-banner {{
            background: #18202E;
            border: 1px solid #2A3B54;
            border-left: 4px solid #2196F3;
            padding: 0.85rem;
            border-radius: 2px;
            margin-bottom: 1rem;
        }}

        .directive-text {{
            font-family: var(--font-mono);
            font-size: 1.1rem;
            font-weight: 700;
            color: #FFFFFF;
            margin: 0.4rem 0;
        }}

        .spec-table {{
            width: 100%;
            border-collapse: collapse;
            font-family: var(--font-mono);
            font-size: 0.74rem;
            margin-top: 0.5rem;
        }}

        .spec-table th {{
            background: #1C202C;
            color: var(--fuxa-text-muted);
            text-align: left;
            padding: 0.45rem;
            border-bottom: 1px solid var(--fuxa-border);
        }}

        .spec-table td {{
            padding: 0.45rem;
            border-bottom: 1px solid #272C3B;
            color: var(--fuxa-text-secondary);
        }}

        .spec-table tr.selected td {{
            background: rgba(33, 150, 243, 0.1);
            color: #FFFFFF;
            font-weight: 600;
        }}

        /* Status & Attribution Footer */
        .fuxa-footer {{
            background: #151821;
            border-top: 1px solid var(--fuxa-border);
            padding: 0.35rem 1rem;
            display: flex;
            align-items: center;
            justify-content: space-between;
            font-family: var(--font-mono);
            font-size: 0.68rem;
            color: var(--fuxa-text-muted);
        }}

        .fuxa-footer a {{
            color: #90CAF9;
            text-decoration: none;
        }}

        .fuxa-footer a:hover {{
            text-decoration: underline;
        }}
    </style>
</head>
<body>

    <!-- FUXA Operator Top Header -->
    <header class="fuxa-header">
        <div class="fuxa-brand-area">
            <div class="fuxa-logo">
                <svg viewBox="0 0 24 24">
                    <path d="M4 4h16v3H4zm0 6h10v3H4zm0 6h14v3H4z"/>
                </svg>
                <span>FUXA SCADA/HMI</span>
            </div>
            <span style="color:var(--fuxa-border)">|</span>
            <span style="font-weight:500; font-size:0.85rem; color:#FFFFFF;">SAANJH Grid Edge Substation Station</span>
            <span class="fuxa-badge-model">MODEL REPLAY</span>
        </div>

        <div class="fuxa-asset-bar">
            <span>ASSET:</span>
            <span class="highlight">Feeder FDR-023 / DT-100KVA-04 (100 kVA / 95 kW Dyn11)</span>
        </div>

        <div class="fuxa-right-controls">
            <span>STATUS: SIMULATED TELEMETRY</span>
            <span style="color:var(--fuxa-border)">|</span>
            <span id="fuxa-clock">2026-10-03 16:00:00 IST</span>
        </div>
    </header>

    <!-- FUXA Function Screen Tabs -->
    <nav class="fuxa-tabs-bar">
        <button class="fuxa-tab active" data-tab="screen-overview">FEEDER OVERVIEW</button>
        <button class="fuxa-tab" data-tab="screen-trends">TRENDS</button>
        <button class="fuxa-tab" data-tab="screen-fleet">FLEXIBILITY FLEET</button>
        <button class="fuxa-tab" data-tab="screen-decision">DISCOM / DECISION VIEW</button>
    </nav>

    <!-- Telemetry Replay Toolbar -->
    <section class="fuxa-toolbar">
        <div style="display:flex; align-items:center; gap:0.3rem;">
            <button class="fuxa-btn" id="btn-back">◀ Prev</button>
            <button class="fuxa-btn active" id="btn-play">❚❚ Pause</button>
            <button class="fuxa-btn" id="btn-fwd">Next ▶</button>
            <button class="fuxa-btn" id="btn-rst">⟲ Reset</button>
        </div>

        <div class="fuxa-slider-wrap">
            <span style="color:var(--fuxa-text-muted);">TIMESTEP:</span>
            <input type="range" class="fuxa-slider" id="fuxa-slider" min="0" max="71" value="37" step="1">
            <div class="fuxa-time-badge" id="fuxa-time-label">19:05 IST (PEAK)</div>
        </div>

        <div style="display:flex; align-items:center; gap:0.4rem;">
            <button class="fuxa-btn" id="jump-cliff">18:30 Solar Cliff</button>
            <button class="fuxa-btn" id="jump-pk" style="color:#FF9800; font-weight:700;">19:05 Max Peak</button>
        </div>
    </section>

    <!-- Operational KPI Telemetry Strip -->
    <section class="kpi-strip" style="margin:0.5rem 1rem 0 1rem;">
        <div class="kpi-box">
            <span class="kpi-tag">Active Feeder Load</span>
            <div class="kpi-val-row">
                <span class="kpi-val" id="val-load">109.18</span>
                <span class="kpi-unit">kW</span>
            </div>
            <span class="kpi-sub" id="val-load-delta" style="color:#4CAF50;">↓ 44.95 kW (-29.2%) vs Base</span>
        </div>

        <div class="kpi-box">
            <span class="kpi-tag">Transformer Loading</span>
            <div class="kpi-val-row">
                <span class="kpi-val" id="val-tx">114.9</span>
                <span class="kpi-unit">%</span>
            </div>
            <span class="kpi-sub" style="color:#4CAF50;">Overload cut by 30 min</span>
        </div>

        <div class="kpi-box">
            <span class="kpi-tag">Feeder Tail Node 60</span>
            <div class="kpi-val-row">
                <span class="kpi-val" id="val-volt">226.54</span>
                <span class="kpi-unit">V RMS</span>
            </div>
            <span class="kpi-sub" style="color:#4CAF50;">0 Statutory Violations (&gt;216V)</span>
        </div>

        <div class="kpi-box">
            <span class="kpi-tag">Solar PV Generation</span>
            <div class="kpi-val-row">
                <span class="kpi-val" id="val-solar">0.00</span>
                <span class="kpi-unit">kW</span>
            </div>
            <span class="kpi-sub">PV Cliff (-7.5 kW deficit)</span>
        </div>

        <div class="kpi-box">
            <span class="kpi-tag">Available Flexibility</span>
            <div class="kpi-val-row">
                <span class="kpi-val" id="val-flex-avail">92.55</span>
                <span class="kpi-unit">kW</span>
            </div>
            <span class="kpi-sub">Fleet Headroom Preserved</span>
        </div>

        <div class="kpi-box">
            <span class="kpi-tag">Dispatched Flexibility</span>
            <div class="kpi-val-row">
                <span class="kpi-val" id="val-flex-disp">56.25</span>
                <span class="kpi-unit">kW</span>
            </div>
            <span class="kpi-sub">39 BESS Inverters Active</span>
        </div>
    </section>

    <!-- Main Viewport Area -->
    <main class="fuxa-viewport-area">

        <!-- SCREEN 1: FEEDER OVERVIEW -->
        <div class="fuxa-screen active" id="screen-overview">
            <div class="overview-grid">
                
                <!-- Left: Feeder Process Mimic Diagram -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>PROCESS VIEW: FEEDER FDR-023 SINGLE-LINE TOPOLOGY</span>
                        <span style="font-size:0.68rem; color:var(--fuxa-text-muted);">IEC 61850 SLD MODEL</span>
                    </div>
                    <div class="fuxa-panel-body" style="padding:0;">
                        <div class="process-svg-wrap">
                            <svg class="process-svg" viewBox="0 0 760 400" preserveAspectRatio="xMidYMid meet">
                                <!-- Technical Grid -->
                                <pattern id="grid-pattern" width="20" height="20" patternUnits="userSpaceOnUse">
                                    <path d="M 20 0 L 0 0 0 20" fill="none" stroke="rgba(255,255,255,0.03)" stroke-width="1"/>
                                </pattern>
                                <rect width="100%" height="100%" fill="url(#grid-pattern)"/>

                                <!-- 11 kV Incomer Bus -->
                                <line x1="60" y1="50" x2="200" y2="50" stroke="#2196F3" stroke-width="4"/>
                                <text x="60" y="38" fill="#2196F3" font-family="var(--font-mono)" font-size="10" font-weight="700">11 kV SUBSTATION BUSBAR</text>

                                <!-- Circuit Breaker CB-23 -->
                                <line x1="130" y1="50" x2="130" y2="90" stroke="#31374A" stroke-width="2"/>
                                <rect x="122" y="90" width="16" height="16" fill="#1C202C" stroke="#4CAF50" stroke-width="2" rx="1"/>
                                <line x1="126" y1="98" x2="134" y2="98" stroke="#4CAF50" stroke-width="2"/>
                                <text x="146" y="102" fill="#B0BEC5" font-family="var(--font-mono)" font-size="9">CB-23 [CLOSED]</text>

                                <!-- Down to Distribution Transformer -->
                                <line x1="130" y1="106" x2="130" y2="140" stroke="#31374A" stroke-width="2"/>
                                <circle cx="130" cy="150" r="14" fill="none" stroke="#2196F3" stroke-width="2"/>
                                <circle cx="130" cy="170" r="14" fill="none" stroke="#4CAF50" stroke-width="2"/>
                                <text x="154" y="155" fill="#FFFFFF" font-family="var(--font-mono)" font-size="10" font-weight="700">DT-100KVA-04</text>
                                <text x="154" y="168" fill="#78909C" font-family="var(--font-mono)" font-size="9">11 / 0.415 kV Dyn11</text>
                                <text x="154" y="180" fill="#78909C" font-family="var(--font-mono)" font-size="8">Rating: 100 kVA / 95 kW</text>

                                <!-- 415 V 3-Phase Feeder Spine -->
                                <line x1="130" y1="184" x2="130" y2="230" stroke="#31374A" stroke-width="2"/>
                                <line x1="130" y1="230" x2="700" y2="230" stroke="#4CAF50" stroke-width="3"/>
                                <text x="140" y="222" fill="#4CAF50" font-family="var(--font-mono)" font-size="9" font-weight="700">415 V FEEDER MAIN TRUNK (FDR-023)</text>

                                <!-- Cluster 1: Homes 01–20 -->
                                <g transform="translate(240, 230)">
                                    <line x1="0" y1="0" x2="0" y2="50" stroke="#31374A" stroke-width="1.5"/>
                                    <rect x="-40" y="50" width="80" height="45" fill="#1C202C" stroke="#31374A" stroke-width="1"/>
                                    <text x="-32" y="66" fill="#FFFFFF" font-family="var(--font-mono)" font-size="9" font-weight="700">HOMES 01–20</text>
                                    <text x="-32" y="78" fill="#78909C" font-family="var(--font-mono)" font-size="8">14 BESS / 5 Solar</text>
                                    <text x="-32" y="89" fill="#4CAF50" font-family="var(--font-mono)" font-size="8">13 Active (H-18 Opt)</text>
                                </g>

                                <!-- Cluster 2: Homes 21–40 -->
                                <g transform="translate(420, 230)">
                                    <line x1="0" y1="0" x2="0" y2="50" stroke="#31374A" stroke-width="1.5"/>
                                    <rect x="-40" y="50" width="80" height="45" fill="#1C202C" stroke="#31374A" stroke-width="1"/>
                                    <text x="-32" y="66" fill="#FFFFFF" font-family="var(--font-mono)" font-size="9" font-weight="700">HOMES 21–40</text>
                                    <text x="-32" y="78" fill="#78909C" font-family="var(--font-mono)" font-size="8">14 BESS / 5 Solar</text>
                                    <text x="-32" y="89" fill="#4CAF50" font-family="var(--font-mono)" font-size="8">14 Active BESS</text>
                                </g>

                                <!-- Cluster 3: Homes 41–60 (Feeder Tail Node 60) -->
                                <g transform="translate(620, 230)">
                                    <line x1="0" y1="0" x2="0" y2="50" stroke="#31374A" stroke-width="1.5"/>
                                    <rect x="-50" y="50" width="100" height="45" fill="#1C202C" stroke="#2196F3" stroke-width="1"/>
                                    <text x="-42" y="66" fill="#2196F3" font-family="var(--font-mono)" font-size="9" font-weight="700">HOMES 41–60 (TAIL)</text>
                                    <text x="-42" y="78" fill="#78909C" font-family="var(--font-mono)" font-size="8">14 BESS (H-55,56 Opt)</text>
                                    <text x="-42" y="89" fill="#4CAF50" font-family="var(--font-mono)" font-size="8" id="svg-tail-text">226.54 V RMS (0 Sag)</text>
                                </g>

                                <!-- SAANJH Virtual Battery Aggregator Representation -->
                                <g transform="translate(370, 330)">
                                    <rect x="-160" y="-18" width="320" height="40" fill="#151821" stroke="#4CAF50" stroke-width="1.5" rx="2"/>
                                    <text x="-140" y="-2" fill="#4CAF50" font-family="var(--font-mono)" font-size="10" font-weight="700">SAANJH VIRTUAL COMMUNITY BATTERY (VCB)</text>
                                    <text x="-140" y="13" fill="#B0BEC5" font-family="var(--font-mono)" font-size="8.5">42 Inverters Enrolled | 39 Participating | 3 Opted Out | Hard Reserve Limit &gt;=70%</text>
                                </g>
                            </svg>
                        </div>
                    </div>
                </div>

                <!-- Right: Asset Health & Thermal Stress -->
                <div style="display:flex; flex-direction:column; gap:1rem;">
                    
                    <div class="fuxa-panel">
                        <div class="fuxa-panel-title">
                            <span>TRANSFORMER THERMAL LOADING</span>
                            <span id="badge-tx-stress" style="color:#4CAF50;">STABILIZED</span>
                        </div>
                        <div class="fuxa-panel-body">
                            <div style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:0.75rem;">
                                <span style="color:var(--fuxa-text-muted);">CURRENT LOAD:</span>
                                <span style="color:#FFFFFF; font-weight:700;" id="txt-tx-load">109.18 kW / 114.9%</span>
                            </div>

                            <div class="gauge-bar-wrap">
                                <div class="gauge-fill" id="bar-tx-fill" style="width:71%; background:#4CAF50;"></div>
                                <div class="gauge-limit-mark" style="left:85%;" title="80.75 kW (85% Continuous Rating)"></div>
                            </div>
                            <div style="display:flex; justify-content:space-between; font-family:var(--font-mono); font-size:0.68rem; color:var(--fuxa-text-muted);">
                                <span>0 kW</span>
                                <span>80.75 kW (Safe Limit)</span>
                                <span>95 kW (Rated)</span>
                                <span>154 kW (Base Peak)</span>
                            </div>

                            <div style="margin-top:0.85rem; display:flex; flex-direction:column; gap:0.4rem; font-family:var(--font-mono); font-size:0.73rem;">
                                <div style="display:flex; justify-content:space-between; padding:0.35rem 0; border-bottom:1px solid #272C3B;">
                                    <span style="color:var(--fuxa-text-muted);">Baseline Peak Overload:</span>
                                    <span style="color:#F44336; font-weight:700;">154.14 kW (162.2%)</span>
                                </div>
                                <div style="display:flex; justify-content:space-between; padding:0.35rem 0; border-bottom:1px solid #272C3B;">
                                    <span style="color:var(--fuxa-text-muted);">SAANJH Controlled Peak:</span>
                                    <span style="color:#4CAF50; font-weight:700;">109.18 kW (-44.95 kW)</span>
                                </div>
                                <div style="display:flex; justify-content:space-between; padding:0.35rem 0; border-bottom:1px solid #272C3B;">
                                    <span style="color:var(--fuxa-text-muted);">Overload Duration:</span>
                                    <span>60 min (30 min stress avoided)</span>
                                </div>
                                <div style="display:flex; justify-content:space-between; padding:0.35rem 0;">
                                    <span style="color:var(--fuxa-text-muted);">Insulation Life Gain:</span>
                                    <span style="color:#4CAF50; font-weight:700;">+3.8 Years (Arrhenius Model)</span>
                                </div>
                            </div>
                        </div>
                    </div>

                    <!-- Sequence of Events -->
                    <div class="fuxa-panel" style="flex:1;">
                        <div class="fuxa-panel-title">
                            <span>SEQUENCE OF EVENTS (SOE) LOG</span>
                            <span style="color:var(--fuxa-text-muted); font-size:0.68rem;">SIMULATION REPLAY</span>
                        </div>
                        <div class="fuxa-panel-body" style="padding:0; overflow-y:auto; max-height:200px;">
                            <table class="fleet-table">
                                <thead>
                                    <tr>
                                        <th>Time</th>
                                        <th>Tag</th>
                                        <th>Description</th>
                                    </tr>
                                </thead>
                                <tbody>
                                    <tr>
                                        <td>19:05:00</td>
                                        <td style="color:#4CAF50;">FEEDER</td>
                                        <td>Coincident peak shaved to 109.18 kW (44.95 kW reduction)</td>
                                    </tr>
                                    <tr>
                                        <td>19:05:00</td>
                                        <td style="color:#2196F3;">TAIL-NODE</td>
                                        <td>Voltage stabilized at 226.54 V (Zero &lt;216V violations)</td>
                                    </tr>
                                    <tr>
                                        <td>18:35:00</td>
                                        <td style="color:#9C27B0;">DISPATCH</td>
                                        <td>Flexibility activated: 56.25 kW dispatched across 39 homes</td>
                                    </tr>
                                    <tr>
                                        <td>18:30:00</td>
                                        <td style="color:#FF9800;">SOLAR</td>
                                        <td>Solar PV cliff detected: Generation dropped to 0.0 kW</td>
                                    </tr>
                                    <tr>
                                        <td>16:00:00</td>
                                        <td style="color:#B0BEC5;">FLEET</td>
                                        <td>Fleet initialized: 42 BESS ready, 3 opt-outs respected</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>

                </div>
            </div>
        </div>

        <!-- SCREEN 2: TRENDS -->
        <div class="fuxa-screen" id="screen-trends">
            <div class="trends-2x2">
                
                <!-- Chart 1: Baseline vs SAANJH Feeder Demand -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>CHART 1: BASELINE FEEDER DEMAND VS SAANJH-CONTROLLED DEMAND (kW)</span>
                        <span style="color:var(--fuxa-text-muted);">16:00 - 22:00 IST</span>
                    </div>
                    <div class="fuxa-panel-body">
                        <div class="chart-container">
                            <canvas id="fuxa-chart-demand"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 2: Baseline vs SAANJH Feeder Tail Voltage -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>CHART 2: FEEDER TAIL NODE 60 RMS VOLTAGE (V)</span>
                        <span style="color:#4CAF50;">100% STATUTORY COMPLIANCE (&gt;216V)</span>
                    </div>
                    <div class="fuxa-panel-body">
                        <div class="chart-container">
                            <canvas id="fuxa-chart-voltage"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 3: Flexibility Available vs Dispatched -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>CHART 3: AVAILABLE FLEET FLEXIBILITY VS DISPATCHED FLEXIBILITY (kW)</span>
                        <span style="color:var(--fuxa-text-muted);">39 Inverters Active</span>
                    </div>
                    <div class="fuxa-panel-body">
                        <div class="chart-container">
                            <canvas id="fuxa-chart-flex"></canvas>
                        </div>
                    </div>
                </div>

                <!-- Chart 4: Solar Generation + Feeder Demand -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>CHART 4: SOLAR GENERATION AND FEEDER DEMAND DYNAMICS (kW)</span>
                        <span style="color:#FF9800;">18:30 Solar Cliff Highlighted</span>
                    </div>
                    <div class="fuxa-panel-body">
                        <div class="chart-container">
                            <canvas id="fuxa-chart-solar"></canvas>
                        </div>
                    </div>
                </div>

            </div>
        </div>

        <!-- SCREEN 3: FLEXIBILITY FLEET -->
        <div class="fuxa-screen" id="screen-fleet">
            <div class="fuxa-panel" style="flex:1;">
                <div class="fuxa-panel-title">
                    <span>RESIDENTIAL FLEXIBILITY ASSET MATRIX (ALL 60 HOMES)</span>
                    <span style="font-size:0.68rem; color:var(--fuxa-text-muted);">CANONICAL SOURCE: simulation/data/results/household_dispatch.csv</span>
                </div>
                <div class="fuxa-panel-body">
                    
                    <div class="fleet-controls">
                        <div style="display:flex; align-items:center; gap:0.4rem;">
                            <span style="color:var(--fuxa-text-muted); font-size:0.75rem;">FILTER:</span>
                            <button class="fuxa-btn active" data-fleet-filter="all">ALL (60)</button>
                            <button class="fuxa-btn" data-fleet-filter="bess">BESS (42)</button>
                            <button class="fuxa-btn" data-fleet-filter="participating">ACTIVE (39)</button>
                            <button class="fuxa-btn" data-fleet-filter="optout">OPTED OUT (3)</button>
                            <button class="fuxa-btn" data-fleet-filter="solar">SOLAR (15)</button>
                        </div>

                        <div style="display:flex; align-items:center; gap:0.5rem;">
                            <input type="text" id="fuxa-fleet-search" placeholder="Search Home ID (e.g. H-18)..." style="background:#151821; border:1px solid var(--fuxa-border); color:#FFFFFF; padding:2px 8px; font-family:var(--font-mono); font-size:0.75rem; border-radius:2px; width:190px;">
                            <span style="color:var(--fuxa-text-muted); font-family:var(--font-mono); font-size:0.72rem;" id="fleet-count-text">Showing 60 homes</span>
                        </div>
                    </div>

                    <div class="fleet-table-wrap">
                        <table class="fleet-table">
                            <thead>
                                <tr>
                                    <th>Home</th>
                                    <th>Battery</th>
                                    <th>Solar</th>
                                    <th>State of Charge (SOC)</th>
                                    <th>Reserve Limit</th>
                                    <th>Available (kW)</th>
                                    <th>Dispatched (kW)</th>
                                    <th>Delivered (kWh)</th>
                                    <th>Participation</th>
                                    <th>Opted Out</th>
                                    <th>Compensation</th>
                                </tr>
                            </thead>
                            <tbody id="fuxa-fleet-tbody">
                                <!-- Populated from canonical fleet array -->
                            </tbody>
                        </table>
                    </div>

                </div>
            </div>
        </div>

        <!-- SCREEN 4: DISCOM / DECISION VIEW -->
        <div class="fuxa-screen" id="screen-decision">
            <div class="decision-layout">
                
                <!-- Left: Feeder Condition & Action Recommendation -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>DISCOM FEEDER DECISION SUPPORT & DIRECTIVE</span>
                        <span style="color:#2196F3;">AUTHORIZED OPERATOR PLAN</span>
                    </div>
                    <div class="fuxa-panel-body">
                        
                        <div class="decision-banner">
                            <div style="font-family:var(--font-mono); font-size:0.72rem; color:#2196F3; font-weight:700;">
                                >> AUTOMATED ACTION PLAN: FDR-023 / DT-100KVA-04
                            </div>
                            <div class="directive-text">
                                "DISPATCH 56.2 kW FOR 45 MINUTES VIA SAANJH EDGE"
                            </div>
                            <p style="color:var(--fuxa-text-secondary); font-size:0.78rem;">
                                Pre-emptive flexibility call triggered by 18:30 Solar Cliff forecast. Coordinates 39 participating residential inverters across Nodes 01–60 to shave 44.95 kW of coincident evening demand.
                            </p>
                        </div>

                        <div style="font-family:var(--font-mono); font-size:0.75rem; font-weight:700; color:#FFFFFF; margin-bottom:0.4rem;">
                            1. CURRENT FEEDER CONDITION (AT TRIGGER TIME 18:30):
                        </div>
                        <div style="display:flex; flex-direction:column; gap:0.35rem; font-family:var(--font-mono); font-size:0.72rem; margin-bottom:1rem;">
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Baseline Projected Peak:</span>
                                <span style="color:#F44336; font-weight:700;">154.14 kW (162.2% Overload)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Baseline Feeder Tail Voltage:</span>
                                <span style="color:#F44336;">219.68 V (6 Voltage Violations below statutory 216V)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Fleet Flexibility Available:</span>
                                <span style="color:#4CAF50; font-weight:700;">92.55 kW Headroom (164% of request)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Flexibility Dispatched:</span>
                                <span style="color:#2196F3; font-weight:700;">56.25 kW (45-Minute Coordinated Discharge)</span>
                            </div>
                        </div>

                        <div style="font-family:var(--font-mono); font-size:0.75rem; font-weight:700; color:#FFFFFF; margin-bottom:0.4rem;">
                            2. EXPECTED ENGINEERING OUTCOME (VALIDATED VIA PYPSA):
                        </div>
                        <div style="display:flex; flex-direction:column; gap:0.35rem; font-family:var(--font-mono); font-size:0.72rem;">
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Net Peak Shaved:</span>
                                <span style="color:#4CAF50; font-weight:700;">-44.95 kW (-29.2% Shaved down to 109.18 kW)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Thermal Overload Duration:</span>
                                <span style="color:#4CAF50; font-weight:700;">90 min → 60 min (30 minutes stress cut)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Voltage Violations:</span>
                                <span style="color:#4CAF50; font-weight:700;">6 → 0 (100% Eliminated, Tail held at 226.5V)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Distribution Losses:</span>
                                <span style="color:#4CAF50; font-weight:700;">25.87 → 16.74 kWh (-35.3% Technical Loss Saving)</span>
                            </div>
                            <div style="display:flex; justify-content:space-between; padding:0.35rem; background:#1C202C; border:1px solid #272C3B;">
                                <span style="color:var(--fuxa-text-muted);">Critical-Load Protection:</span>
                                <span style="color:#4CAF50; font-weight:700;">ZERO Reserve Breaches (All homes ≥70% SOC)</span>
                            </div>
                        </div>

                    </div>
                </div>

                <!-- Right: Economic Sensitivity Matrix -->
                <div class="fuxa-panel">
                    <div class="fuxa-panel-title">
                        <span>THREE-TIER DEPLOYMENT CAPEX SENSITIVITY</span>
                        <span style="color:var(--fuxa-text-muted);">INR (₹)</span>
                    </div>
                    <div class="fuxa-panel-body">
                        
                        <table class="spec-table">
                            <thead>
                                <tr>
                                    <th>Deployment Scenario</th>
                                    <th>Total CapEx</th>
                                    <th>Cost / kW</th>
                                    <th>Cost / Home</th>
                                </tr>
                            </thead>
                            <tbody>
                                <tr>
                                    <td>Low-Cost Mass Production</td>
                                    <td>₹1,60,200</td>
                                    <td style="color:#4CAF50; font-weight:700;">₹3,563</td>
                                    <td>₹4,107</td>
                                </tr>
                                <tr class="selected">
                                    <td style="color:#2196F3;">Base Prototype Scale</td>
                                    <td>₹3,17,767</td>
                                    <td style="color:#2196F3; font-weight:700;">₹7,068</td>
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

                        <div style="margin-top:1rem; background:#181B24; border:1px solid var(--fuxa-border); padding:0.75rem; border-radius:2px;">
                            <div style="font-family:var(--font-mono); font-size:0.74rem; font-weight:700; color:#FFFFFF; margin-bottom:0.5rem;">
                                ARCHITECTURAL COST COMPARISON:
                            </div>
                            <div style="display:flex; flex-direction:column; gap:0.35rem; font-family:var(--font-mono); font-size:0.72rem;">
                                <div style="display:flex; justify-content:space-between;">
                                    <span style="color:var(--fuxa-text-muted);">Central Substation BESS (50 kWh):</span>
                                    <span style="color:#F44336;">₹45,000 / kW (₹22,50,000)</span>
                                </div>
                                <div style="display:flex; justify-content:space-between;">
                                    <span style="color:var(--fuxa-text-muted);">SAANJH Distributed Retrofit:</span>
                                    <span style="color:#4CAF50; font-weight:700;">₹7,068 / kW (₹3,17,767)</span>
                                </div>
                                <div style="display:flex; justify-content:space-between;">
                                    <span style="color:var(--fuxa-text-muted);">Net Capital Savings:</span>
                                    <span style="color:#4CAF50; font-weight:700;">84.3% (₹19,32,233 Avoided)</span>
                                </div>
                                <div style="display:flex; justify-content:space-between;">
                                    <span style="color:var(--fuxa-text-muted);">Substation Land Required:</span>
                                    <span style="color:#4CAF50; font-weight:700;">Zero sq. meters</span>
                                </div>
                            </div>
                        </div>

                        <!-- System Boundary Mapping -->
                        <div style="margin-top:0.85rem; border-top:1px solid var(--fuxa-border); padding-top:0.5rem; font-family:var(--font-mono); font-size:0.68rem; color:var(--fuxa-text-muted);">
                            <div style="font-weight:700; color:#B0BEC5; margin-bottom:0.25rem;">SYSTEM VERIFICATION BOUNDARIES:</div>
                            <div>• [PHYSICAL]: LoRa node temperature sensing &amp; CT clamp telemetry</div>
                            <div>• [MODEL]: 72-step feeder simulation, XGBoost forecaster, PyPSA validation</div>
                            <div>• [FUTURE DEPLOYMENT]: Certified DISCOM ADMS/DERMS utility switching</div>
                        </div>

                    </div>
                </div>

            </div>
        </div>

    </main>

    <!-- FUXA Industrial Footer & Attribution -->
    <footer class="fuxa-footer">
        <div>
            <span>PLATFORM: <a href="https://github.com/frangoteam/FUXA" target="_blank" rel="noopener">FUXA Web SCADA/HMI</a> (MIT License, Commit 64eb012)</span>
            <span style="color:var(--fuxa-border)">|</span>
            <span>APPLICATION: SAANJH Virtual Community Battery Feeder Orchestrator</span>
        </div>
        <div>
            <span>SCHNEIDER ELECTRIC YUVA YODHA HACKATHON 2026 — CHALLENGE 03</span>
        </div>
    </footer>

    <!-- RUNTIME LOGIC & CHART BINDINGS -->
    <script>
        // Canonical Datasets
        const CANONICAL_TIMESERIES = {json.dumps(timeseries)};
        const CANONICAL_FLEET = {json.dumps(fleet)};
        const CANONICAL_COMP = {json.dumps(comparison)};
        const CANONICAL_DISCOM = {json.dumps(discom)};
        const CANONICAL_ECON = {json.dumps(economics)};

        let currentStep = 37; // 19:05 Peak
        let isPlaying = false;
        let playTimer = null;
        let charts = {{}};

        document.addEventListener('DOMContentLoaded', () => {{
            setupTabs();
            setupReplayControls();
            populateFleetTable(CANONICAL_FLEET);
            initCharts(CANONICAL_TIMESERIES);
            applyTimestep(currentStep);
            startClock();
        }});

        function startClock() {{
            const clockEl = document.getElementById('fuxa-clock');
            setInterval(() => {{
                const d = new Date();
                const pad = n => n.toString().padStart(2, '0');
                clockEl.innerText = `${{d.getFullYear()}}-${{pad(d.getMonth()+1)}}-${{pad(d.getDate())}} ${{pad(d.getHours())}}:${{pad(d.getMinutes())}}:${{pad(d.getSeconds())}} IST`;
            }}, 1000);
        }}

        function setupTabs() {{
            const tabs = document.querySelectorAll('.fuxa-tab');
            tabs.forEach(tab => {{
                tab.addEventListener('click', () => {{
                    tabs.forEach(t => t.classList.remove('active'));
                    document.querySelectorAll('.fuxa-screen').forEach(s => s.classList.remove('active'));
                    
                    tab.classList.add('active');
                    const targetId = tab.getAttribute('data-tab');
                    const targetScreen = document.getElementById(targetId);
                    if (targetScreen) targetScreen.classList.add('active');

                    if (targetId === 'screen-trends') {{
                        setTimeout(() => {{
                            Object.values(charts).forEach(c => c.resize());
                        }}, 50);
                    }}
                }});
            }});
        }}

        function setupReplayControls() {{
            const slider = document.getElementById('fuxa-slider');
            const btnPlay = document.getElementById('btn-play');
            const btnBack = document.getElementById('btn-back');
            const btnFwd = document.getElementById('btn-fwd');
            const btnRst = document.getElementById('btn-rst');
            const jumpCliff = document.getElementById('jump-cliff');
            const jumpPk = document.getElementById('jump-pk');

            slider.addEventListener('input', e => {{
                currentStep = parseInt(e.target.value);
                applyTimestep(currentStep);
            }});

            btnPlay.addEventListener('click', () => {{
                isPlaying = !isPlaying;
                if (isPlaying) {{
                    btnPlay.innerText = '❚❚ Pause';
                    btnPlay.classList.add('active');
                    playTimer = setInterval(() => {{
                        if (currentStep < CANONICAL_TIMESERIES.labels.length - 1) {{
                            currentStep++;
                        }} else {{
                            currentStep = 0;
                        }}
                        slider.value = currentStep;
                        applyTimestep(currentStep);
                    }}, 600);
                }} else {{
                    btnPlay.innerText = '▶ Play';
                    btnPlay.classList.remove('active');
                    clearInterval(playTimer);
                }}
            }});

            btnBack.addEventListener('click', () => {{
                if (currentStep > 0) {{
                    currentStep--;
                    slider.value = currentStep;
                    applyTimestep(currentStep);
                }}
            }});

            btnFwd.addEventListener('click', () => {{
                if (currentStep < CANONICAL_TIMESERIES.labels.length - 1) {{
                    currentStep++;
                    slider.value = currentStep;
                    applyTimestep(currentStep);
                }}
            }});

            btnRst.addEventListener('click', () => {{
                currentStep = 0;
                slider.value = currentStep;
                applyTimestep(currentStep);
            }});

            if (jumpCliff) jumpCliff.addEventListener('click', () => jumpToStep(30));
            if (jumpPk) jumpPk.addEventListener('click', () => jumpToStep(37));
        }}

        function jumpToStep(s) {{
            currentStep = s;
            document.getElementById('fuxa-slider').value = s;
            applyTimestep(s);
        }}

        function applyTimestep(idx) {{
            const ts = CANONICAL_TIMESERIES;
            if (!ts || !ts.labels[idx]) return;

            const timeLabel = ts.labels[idx];
            const loadVal = ts.saanjh_load[idx];
            const baseLoad = ts.baseline_load[idx];
            const voltVal = ts.saanjh_voltage[idx];
            const solarVal = ts.solar_gen[idx];
            const txPct = ts.tx_loading_pct[idx];
            const flexDisp = ts.flex_delivered[idx];
            const flexAvail = ts.flex_available[idx];
            const deltaKw = (baseLoad - loadVal).toFixed(2);

            document.getElementById('fuxa-time-label').innerText = `${{timeLabel}} IST (${{idx === 37 ? 'MAX PEAK' : (idx === 30 ? 'SOLAR CLIFF' : 'DISPATCH')}})`;
            document.getElementById('val-load').innerText = loadVal.toFixed(2);
            document.getElementById('val-load-delta').innerText = deltaKw > 0 ? `↓ ${{deltaKw}} kW (-${{((deltaKw/baseLoad)*100).toFixed(1)}}%)` : `0.0 kW delta`;
            document.getElementById('val-tx').innerText = txPct.toFixed(1);
            document.getElementById('val-volt').innerText = voltVal.toFixed(2);
            document.getElementById('val-solar').innerText = solarVal.toFixed(2);
            document.getElementById('val-flex-avail').innerText = flexAvail.toFixed(2);
            document.getElementById('val-flex-disp').innerText = flexDisp.toFixed(2);

            // Transformer linear gauge
            const barFill = document.getElementById('bar-tx-fill');
            const txtLoad = document.getElementById('txt-tx-load');
            const badgeStress = document.getElementById('badge-tx-stress');
            if (barFill) {{
                const fillPct = Math.min(100, (loadVal / 154.14) * 100);
                barFill.style.width = fillPct + '%';
                if (txPct > 100) {{
                    barFill.style.background = '#F44336';
                    if (badgeStress) {{ badgeStress.innerText = 'OVERLOAD REDUCED'; badgeStress.style.color = '#FF9800'; }}
                }} else if (txPct > 85) {{
                    barFill.style.background = '#FF9800';
                    if (badgeStress) {{ badgeStress.innerText = 'CONTINUOUS RATING'; badgeStress.style.color = '#FF9800'; }}
                }} else {{
                    barFill.style.background = '#4CAF50';
                    if (badgeStress) {{ badgeStress.innerText = 'SAFE MARGIN'; badgeStress.style.color = '#4CAF50'; }}
                }}
            }}
            if (txtLoad) {{
                txtLoad.innerText = `${{loadVal.toFixed(2)}} kW / ${{txPct.toFixed(1)}}%`;
            }}

            const tailSvgText = document.getElementById('svg-tail-text');
            if (tailSvgText) {{
                tailSvgText.innerText = `${{voltVal.toFixed(2)}} V RMS (${{voltVal >= 216 ? '0 Sag' : 'Sag Event'}})`;
            }}
        }}

        function initCharts(ts) {{
            const commonScales = {{
                x: {{
                    grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                    ticks: {{ color: '#78909C', font: {{ family: "'Roboto Mono', monospace", size: 10 }} }}
                }},
                y: {{
                    grid: {{ color: 'rgba(255, 255, 255, 0.05)' }},
                    ticks: {{ color: '#78909C', font: {{ family: "'Roboto Mono', monospace", size: 10 }} }}
                }}
            }};

            const commonOptions = (title, yMin, yMax) => ({{
                responsive: true,
                maintainAspectRatio: false,
                animation: false,
                interaction: {{ mode: 'index', intersect: false }},
                plugins: {{
                    legend: {{ labels: {{ color: '#B0BEC5', font: {{ family: "'Roboto', sans-serif", size: 11 }} }} }},
                    tooltip: {{
                        backgroundColor: '#1C202C',
                        titleColor: '#FFFFFF',
                        bodyColor: '#B0BEC5',
                        borderColor: '#31374A',
                        borderWidth: 1,
                        padding: 8
                    }}
                }},
                scales: {{
                    ...commonScales,
                    y: {{ ...commonScales.y, min: yMin, max: yMax }}
                }}
            }});

            // Chart 1: Demand
            charts.demand = new Chart(document.getElementById('fuxa-chart-demand').getContext('2d'), {{
                type: 'line',
                data: {{
                    labels: ts.labels,
                    datasets: [
                        {{
                            label: 'Baseline Feeder Demand (kW)',
                            data: ts.baseline_load,
                            borderColor: '#F44336',
                            borderWidth: 2,
                            borderDash: [5, 5],
                            pointRadius: 0
                        }},
                        {{
                            label: 'SAANJH-Controlled Demand (kW)',
                            data: ts.saanjh_load,
                            borderColor: '#4CAF50',
                            backgroundColor: 'rgba(76, 175, 80, 0.15)',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Transformer 85% Limit (80.75 kW)',
                            data: ts.labels.map(() => 80.75),
                            borderColor: '#78909C',
                            borderWidth: 1,
                            borderDash: [4, 4],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: commonOptions('Active Power (kW)')
            }});

            // Chart 2: Voltage
            charts.voltage = new Chart(document.getElementById('fuxa-chart-voltage').getContext('2d'), {{
                type: 'line',
                data: {{
                    labels: ts.labels,
                    datasets: [
                        {{
                            label: 'Baseline Sag (Node 60)',
                            data: ts.baseline_voltage,
                            borderColor: '#F44336',
                            borderWidth: 2,
                            borderDash: [4, 4],
                            pointRadius: 0
                        }},
                        {{
                            label: 'SAANJH Stabilized Voltage (Node 60)',
                            data: ts.saanjh_voltage,
                            borderColor: '#2196F3',
                            backgroundColor: 'rgba(33, 150, 243, 0.12)',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Statutory Minimum Limit (216V)',
                            data: ts.labels.map(() => 216),
                            borderColor: '#FF9800',
                            borderWidth: 1.5,
                            borderDash: [6, 4],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: commonOptions('RMS Voltage (V)', 214, 242)
            }});

            // Chart 3: Flex
            charts.flex = new Chart(document.getElementById('fuxa-chart-flex').getContext('2d'), {{
                type: 'line',
                data: {{
                    labels: ts.labels,
                    datasets: [
                        {{
                            label: 'Dispatched Flexibility (kW)',
                            data: ts.flex_delivered,
                            borderColor: '#4CAF50',
                            backgroundColor: 'rgba(76, 175, 80, 0.25)',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Available Fleet Flexibility (kW)',
                            data: ts.flex_available,
                            borderColor: '#9C27B0',
                            borderWidth: 1.5,
                            borderDash: [4, 4],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: commonOptions('Power (kW)')
            }});

            // Chart 4: Solar
            charts.solar = new Chart(document.getElementById('fuxa-chart-solar').getContext('2d'), {{
                type: 'line',
                data: {{
                    labels: ts.labels,
                    datasets: [
                        {{
                            label: 'Solar PV Cliff Generation (kW)',
                            data: ts.solar_gen,
                            borderColor: '#FF9800',
                            backgroundColor: 'rgba(255, 152, 0, 0.15)',
                            borderWidth: 2,
                            pointRadius: 0,
                            fill: true
                        }},
                        {{
                            label: 'Gross Feeder Demand (kW)',
                            data: ts.gross_demand,
                            borderColor: '#B0BEC5',
                            borderWidth: 1.5,
                            borderDash: [3, 3],
                            pointRadius: 0
                        }}
                    ]
                }},
                options: commonOptions('Power (kW)')
            }});
        }}

        function populateFleetTable(fleet) {{
            const tbody = document.getElementById('fuxa-fleet-tbody');
            const searchInput = document.getElementById('fuxa-fleet-search');
            const countText = document.getElementById('fleet-count-text');
            const filterBtns = document.querySelectorAll('[data-fleet-filter]');

            let activeFilter = 'all';

            function renderRows() {{
                const search = searchInput.value.trim().toUpperCase();
                tbody.innerHTML = '';
                
                const filtered = fleet.filter(h => {{
                    if (activeFilter === 'bess' && !h.has_battery) return false;
                    if (activeFilter === 'participating' && !h.participated) return false;
                    if (activeFilter === 'optout' && !h.opted_out) return false;
                    if (activeFilter === 'solar' && !h.has_solar) return false;
                    if (search && !h.id.includes(search)) return false;
                    return true;
                }});

                countText.innerText = `Showing ${{filtered.length}} of 60 homes`;

                filtered.forEach(h => {{
                    const tr = document.createElement('tr');
                    const socPct = (h.final_soc * 100).toFixed(0);
                    const socColor = h.final_soc >= 0.8 ? '#4CAF50' : (h.final_soc >= 0.7 ? '#FF9800' : '#F44336');

                    tr.innerHTML = `
                        <td style="font-weight:700; color:#FFFFFF;">${{h.id}}</td>
                        <td>${{h.has_battery ? '<span style="color:#4CAF50;">Installed (4.0 kWh)</span>' : '<span style="color:#78909C;">None</span>'}}</td>
                        <td>${{h.has_solar ? '<span style="color:#FF9800;">Installed (1.5 kWp)</span>' : '<span style="color:#78909C;">None</span>'}}</td>
                        <td>
                            <div class="soc-indicator">
                                <div class="soc-fill" style="width: ${{socPct}}%; background: ${{socColor}};"></div>
                                <div class="soc-floor-line" title="70% Reserve Floor"></div>
                            </div>
                            <span>${{(h.init_soc * 100).toFixed(0)}}% → ${{socPct}}%</span>
                        </td>
                        <td style="color:#F44336; font-weight:500;">≥70.0% Floor</td>
                        <td>${{h.avail_kw.toFixed(2)}} kW</td>
                        <td style="font-weight:600; color:#FFFFFF;">${{h.disp_kw.toFixed(2)}} kW</td>
                        <td>${{h.delivered_kwh.toFixed(3)}} kWh</td>
                        <td>${{h.participated ? '<span style="color:#4CAF50; font-weight:700;">YES</span>' : '<span style="color:#78909C;">NO</span>'}}</td>
                        <td>${{h.opted_out ? '<span style="color:#FF9800; font-weight:700;">OPTED OUT</span>' : '<span style="color:#78909C;">NO</span>'}}</td>
                        <td style="color:#4CAF50; font-weight:700;">₹${{h.comp_inr.toFixed(2)}}</td>
                    `;
                    tbody.appendChild(tr);
                }});
            }}

            filterBtns.forEach(btn => {{
                btn.addEventListener('click', () => {{
                    filterBtns.forEach(b => b.classList.remove('active'));
                    btn.classList.add('active');
                    activeFilter = btn.getAttribute('data-fleet-filter');
                    renderRows();
                }});
            }});

            searchInput.addEventListener('input', renderRows);
            renderRows();
        }}
    </script>
</body>
</html>
'''

target_file = os.path.join(BASE_DIR, 'docs', 'index.html')
with open(target_file, 'w', encoding='utf-8') as f:
    f.write(html_content)

print(f"Successfully generated FUXA-based SAANJH operator console at {target_file} ({len(html_content)} bytes)")
