"""SAANJH operator console (Streamlit).

Run it with:

    streamlit run dashboard/app.py

This is the primary evidence UI for the Phase 1 prototype. It reads the
committed simulation bundles and the hardware-in-the-loop logs written by
``python -m gateway.service``. It never claims a live utility feed.
"""
from __future__ import annotations

import os
import sys

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dashboard.data import (  # noqa: E402
    GROUP_LABELS,
    SCENARIO_LABELS,
    DashboardData,
    annual_rows,
    calibration_checks,
    forecast_rows,
    load_all,
    low_income_points,
    replay_kpis,
    robustness_cases,
    scorecard_rows,
)

GREEN = "#3DCD58"
AMBER = "#F2A900"
RED = "#D64545"
BLUE = "#3B82F6"
GREY = "#8899AC"

st.set_page_config(
    page_title="SAANJH | Reliability & HIL Console",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown(
    """
    <style>
      .block-container {padding-top: 1.6rem;}
      div[data-testid="stMetric"] {
        background: rgba(22, 27, 34, 0.55);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-left: 4px solid #3DCD58;
        border-radius: 8px;
        padding: 10px 14px;
      }
      .saanjh-note {
        border-left: 4px solid #F2A900;
        background: rgba(242, 169, 0, 0.10);
        padding: 10px 14px;
        border-radius: 6px;
        margin: 6px 0 14px 0;
      }
      .saanjh-ok {
        border-left: 4px solid #3DCD58;
        background: rgba(61, 205, 88, 0.10);
        padding: 10px 14px;
        border-radius: 6px;
        margin: 6px 0 14px 0;
      }
    </style>
    """,
    unsafe_allow_html=True,
)


@st.cache_data(show_spinner=False)
def _load() -> DashboardData:
    return load_all()


def _fig(height: int = 340) -> go.Figure:
    fig = go.Figure()
    fig.update_layout(
        template="plotly_dark",
        height=height,
        margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    return fig


def _num(value, digits: int = 1, unit: str = "") -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "n/a"
    return f"{value:,.{digits}f}{unit}"


def _table(frame: pd.DataFrame, **kwargs) -> None:
    if frame.empty:
        st.caption("No data available yet.")
        return
    st.dataframe(frame, use_container_width=True, hide_index=True, **kwargs)


def _metric_row(items: list[tuple[str, str, str | None]]) -> None:
    columns = st.columns(len(items))
    for column, (label, value, help_text) in zip(columns, items):
        column.metric(label, value, help=help_text)


data = _load()
scenario_key = st.sidebar.selectbox(
    "Simulation scenario",
    options=list(SCENARIO_LABELS),
    format_func=lambda key: SCENARIO_LABELS[key],
)
scenario = data.scenario(scenario_key)

st.title("⚡ SAANJH — reliability, economics and hardware-in-the-loop")
mode = data.mode
badge = {"live": "🟢 LIVE LoRa evidence", "replay": "🟡 Replay evidence",
         "no gateway run": "⚪ No gateway run yet"}[mode]
if data.live_summary.get("session_open"):
    badge += " (session in progress)"
st.caption(
    f"{badge} · {SCENARIO_LABELS[scenario_key]} · "
    f"{scenario.get('homes', 'n/a')} homes · {scenario.get('transformer_kva', 'n/a')} kVA DT · "
    "≤12 V DC bench prototype, no mains switching"
)

if data.missing:
    with st.sidebar.expander(f"Data sources ({len(data.missing)} missing)"):
        st.caption("Missing files fall back to an empty view. Regenerate with "
                   "`python scripts/run_all.py`.")
        for item in data.missing:
            st.text(item)

# ----------------------------------------------------------------- sidebar
st.sidebar.divider()
st.sidebar.subheader("Safety invariants")
replay = replay_kpis(data.replay_summary) if data.replay_summary else {}
st.sidebar.metric("Reserve floor", "70% SoC", help="Node and gateway both refuse below this.")
st.sidebar.metric(
    "SoC floor observed",
    _num(replay.get("soc_min_pct"), 1, "%") if replay else "n/a",
)
st.sidebar.metric(
    "Reserve breaches",
    _num(replay.get("reserve_breaches"), 0) if replay else "n/a",
)
st.sidebar.metric(
    "Packet success",
    _num(replay.get("packet_success_pct"), 1, "%") if replay else "n/a",
)
st.sidebar.caption("Node-side enforcement is covered by 34 native firmware tests "
                   "(`pio test -e native`).")

# ------------------------------------------------------------ headline KPIs
rows = annual_rows(data, scenario_key)
if not rows.empty:
    indexed = rows.set_index("metric")
    def _get(metric, field):
        return indexed.loc[metric, field] if metric in indexed.index else None
    availability = _get("Essential supply availability", "saanjh")
    saidi = _get("Outage hours per home", "saanjh")
    unserved = _get("Energy not served", "saanjh")
    peak = _get("DT peak loading", "saanjh")
    availability_before = _get("Essential supply availability", "baseline")
    saidi_before = _get("Outage hours per home", "baseline")
    _metric_row([
        ("Essential supply availability", _num(availability, 1, "%"),
         f"Baseline {_num(availability_before, 1, '%')}"),
        ("Outage hours per home", _num(saidi, 1, " h"),
         f"Baseline {_num(saidi_before, 1, ' h')}"),
        ("Energy not served", _num(unserved, 0, " kWh"), "Essential energy not delivered"),
        ("DT peak loading", _num(peak, 1, "%"), "100% of the 100 kVA rating"),
    ])

tab_reliability, tab_energy, tab_low_income, tab_stress, tab_cal, tab_hil, tab_discom = st.tabs([
    "1 · Reliability",
    "2 · Energy balance",
    "3 · Low-income economics",
    "4 · Overload & robustness",
    "5 · India calibration",
    "6 · HIL gateway",
    "7 · DISCOM dispatch",
])

# ------------------------------------------------------------- 1 reliability
with tab_reliability:
    st.subheader("Reliability scorecard")
    st.caption(
        "Essential-supply availability and unserved energy are the primary metrics; "
        "transformer thermal loading is secondary. Reliability is reported over the "
        "deficit windows the households actually experience."
    )
    scorecard = scorecard_rows(data, scenario_key)
    _table(scorecard)

    if not scorecard.empty:
        fig = _fig()
        fig.add_trace(go.Bar(
            x=scorecard["metric"], y=scorecard["baseline"], name="Baseline",
            marker_color=GREY,
        ))
        fig.add_trace(go.Bar(
            x=scorecard["metric"], y=scorecard["saanjh"], name="SAANJH",
            marker_color=GREEN,
        ))
        fig.update_layout(title="Baseline vs SAANJH (mean across seeds)", barmode="group",
                          yaxis_title="Value (mixed units)")
        st.plotly_chart(fig, use_container_width=True)

    fairness = scenario.get("seed0_saanjh_fairness", {})
    if fairness:
        st.markdown("**Fairness at seed 0**")
        _metric_row([
            ("Outage Gini", _num(fairness.get("gini"), 3), "0 = identical across homes"),
            ("Max / median", _num(fairness.get("max_over_median"), 2), "Lower is fairer"),
            ("Homes affected", _num((fairness.get("share_of_homes_affected") or 0) * 100, 1, "%"), None),
        ])
    st.caption("Annual run: 30 Monte Carlo seeds, 365 days, NASA POWER Lucknow 2023 weather.")

# ----------------------------------------------------------- 2 energy balance
with tab_energy:
    st.subheader("Battery vs deferred energy reconciliation")
    balance = data.energy_balance
    if not balance:
        st.caption("Run `python simulation/run_analysis.py` to produce energy_balance.json.")
    else:
        rec = balance.get("reconciliation", {})
        _metric_row([
            ("Legacy claim", _num(rec.get("target_kwh"), 1, " kWh"), "Audited, not reproduced"),
            ("Delivered", _num(rec.get("delivered_kwh"), 1, " kWh"), "Battery + deferred"),
            ("Unmet", _num(rec.get("unmet_kwh"), 1, " kWh"), "Honest shortfall"),
            ("Delivered / claim", _num(rec.get("delivered_pct_of_claim"), 1, "%"), None),
        ])
        if rec.get("adds_up"):
            st.markdown(
                f"<div class='saanjh-ok'><strong>Energy identity holds.</strong> "
                f"{_num(rec.get('battery_kwh'), 1)} kWh battery + "
                f"{_num(rec.get('deferred_kwh'), 1)} kWh deferred = "
                f"{_num(rec.get('delivered_kwh'), 1)} kWh delivered.</div>",
                unsafe_allow_html=True,
            )
        else:
            st.markdown("<div class='saanjh-note'>The reconciliation identity does not hold; "
                        "treat the totals as indicative.</div>", unsafe_allow_html=True)

        fig = _fig()
        fig.add_trace(go.Bar(
            x=["Battery", "Deferred", "Unmet", "Legacy claim"],
            y=[rec.get("battery_kwh"), rec.get("deferred_kwh"),
               rec.get("unmet_kwh"), rec.get("target_kwh")],
            marker_color=[GREEN, BLUE, AMBER, GREY],
        ))
        fig.update_layout(title="What actually delivers the 45-minute window", yaxis_title="kWh")
        st.plotly_chart(fig, use_container_width=True)

        best = balance.get("best_45_min", {})
        if best:
            st.markdown("**Best 45-minute window in the modelled fleet (upper bound)**")
            _metric_row([
                ("Window", f"{best.get('start', '?')}–{best.get('end', '?')}", None),
                ("Battery", _num(best.get("battery_kwh"), 1, " kWh"), None),
                ("Deferred", _num(best.get("deferred_kwh"), 1, " kWh"), None),
                ("Peak delivered", _num(best.get("peak_delivered_kw"), 2, " kW"), None),
            ])
        fleet = balance.get("fleet_requirement", {})
        if fleet:
            st.markdown(
                f"<div class='saanjh-note'><strong>Fleet reality check:</strong> "
                f"{fleet.get('note', '')}</div>", unsafe_allow_html=True)
        with st.expander("Audit notes"):
            for note in balance.get("notes", []):
                st.write(f"- {note}")

# ------------------------------------------------------ 3 low-income economics
with tab_low_income:
    st.subheader("Three-group adoption and economics")
    st.caption(
        "Low-income households cannot buy a 5 kWh wall battery. The three routes are "
        "existing inverter batteries, a shared community battery, and the combined fleet."
    )
    groups = data.low_income.get("groups", {})
    if not groups:
        st.caption("Run `python simulation/run_analysis.py` to produce low_income.json.")
    else:
        fig = _fig()
        for key, colour in (("inverter_batteries", BLUE),
                            ("shared_battery", AMBER),
                            ("combined", GREEN)):
            frame = low_income_points(data, key)
            if frame.empty:
                continue
            fig.add_trace(go.Scatter(
                x=frame["adoption"] * 100, y=frame["essential_supply_availability_pct"],
                mode="lines+markers", name=GROUP_LABELS[key],
                line=dict(color=colour, width=3),
            ))
        fig.update_layout(
            title="Adoption vs essential-supply availability",
            xaxis_title="Adoption (% of homes)", yaxis_title="Availability (%)",
        )
        st.plotly_chart(fig, use_container_width=True)

        selected = st.select_slider(
            "Adoption level for the table",
            options=sorted({p for g in groups.values() for p in
                            (point.get("adoption") for point in g.get("points", []))
                            if p is not None}),
            value=0.5,
            format_func=lambda value: f"{value * 100:.0f}%",
        )
        rows = []
        for key in ("inverter_batteries", "shared_battery", "combined"):
            frame = low_income_points(data, key)
            if frame.empty:
                continue
            match = frame[frame["adoption"] == selected]
            if match.empty:
                continue
            point = match.iloc[0]
            rows.append({
                "group": GROUP_LABELS[key],
                "availability_pct": point.get("essential_supply_availability_pct"),
                "saidi_h_per_home": point.get("saidi_hours_per_home"),
                "capex_inr": point.get("capex_inr"),
                "cost_per_home_inr": point.get("cost_per_home_inr"),
                "payback_years": point.get("simple_payback_years"),
            })
        _table(pd.DataFrame(rows))

        best = data.low_income.get("best_case", {})
        if best:
            _metric_row([
                ("Best group", GROUP_LABELS.get(best.get("group", ""), best.get("group", "n/a")), None),
                ("Availability", _num(best.get("essential_supply_availability_pct"), 1, "%"), None),
                ("CAPEX", f"₹{_num(best.get('capex_inr'), 0)}", None),
                ("Discom payback", _num(best.get("simple_payback_years"), 1, " y"), None),
            ])
    with st.expander("Assumptions and limits"):
        for note in data.low_income.get("notes", []):
            st.write(f"- {note}")

# ------------------------------------------------- 4 overload and robustness
with tab_stress:
    st.subheader("Overload and communications robustness")
    st.caption(
        "Overload success is defined by essential-supply availability and unserved energy, "
        "not by thermal peak alone."
    )
    minimum = data.overload.get("minimum", {})
    if minimum:
        st.markdown("**What is needed to reach the service targets**")
        _metric_row([
            ("95% essential, no battery",
             "not achievable" if minimum.get("adoption_without_battery_for_95pct_essential") is None
             else _num(minimum.get("adoption_without_battery_for_95pct_essential"), 2),
             "Adoption sweep at 60%"),
            ("95% essential, 100 kWh battery",
             _num((minimum.get("adoption_with_100kwh_battery_for_95pct_essential") or {}).get("participation"), 1, "%"),
             None),
            ("99% essential, 60% adoption",
             _num((minimum.get("storage_at_60pct_adoption_for_99pct_essential") or {}).get("battery_kwh"), 0, " kWh"),
             None),
        ])
        note = minimum.get("thermal_limit_only_note")
        if note:
            st.markdown(f"<div class='saanjh-note'>{note}</div>", unsafe_allow_html=True)

    sweep = pd.DataFrame(data.overload.get("adoption_sweep", []))
    if not sweep.empty:
        fig = _fig()
        fig.add_trace(go.Scatter(
            x=sweep["participation"] * 100, y=sweep["essential_supply_availability_pct"],
            mode="lines+markers", name="Essential availability", line=dict(color=GREEN, width=3),
        ))
        fig.add_trace(go.Scatter(
            x=sweep["participation"] * 100, y=sweep["unserved_energy_reduction_pct"],
            mode="lines+markers", name="Unserved-energy reduction",
            line=dict(color=BLUE, width=2, dash="dot"),
        ))
        fig.update_layout(title="Adoption sweep", xaxis_title="Participation (%)",
                          yaxis_title="Percent")
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("**Packet loss and node dropout**")
    cases = robustness_cases(data)
    if not cases.empty:
        cases = cases.rename(columns={
            "essential_supply_availability_pct": "availability_pct",
            "saidi_hours_per_home": "saidi_h",
            "relay_command_delivery_pct": "relay_delivery_pct",
            "curtail_command_delivery_pct": "curtail_delivery_pct",
        })
        _table(cases)
    with st.expander("Modelling limits"):
        for note in data.robustness.get("limits", []) + data.overload.get("limits", []):
            st.write(f"- {note}")

# ----------------------------------------------------------- 5 India calibration
with tab_cal:
    st.subheader("Indian calibration and forecast verification")
    calibration = data.calibration
    if not calibration:
        st.caption("Run `python simulation/run_analysis.py` to produce calibration.json.")
    else:
        site = calibration.get("site", {})
        annual = calibration.get("annual", {})
        st.caption(
            f"{calibration.get('label', '')} · site {site.get('name')} "
            f"({site.get('latitude')}, {site.get('longitude')}), {site.get('year')}"
        )
        _metric_row([
            ("GHI", _num(annual.get("ghi_kwh_m2"), 0, " kWh/m²"), "NASA POWER hourly"),
            ("PV yield", _num(annual.get("pv_yield_kwh_per_kwp"), 0, " kWh/kWp"), "Modelled"),
            ("Days", _num(annual.get("days"), 0), None),
            ("Best forecast MAE", "see table", None),
        ])
        checks = calibration_checks(data)
        _table(checks)

        forecast = forecast_rows(data)
        if not forecast.empty:
            st.markdown("**Forecast verification (MASE below 1 beats seasonal naive)**")
            _table(forecast)

        with st.expander("What the calibration does and does not prove"):
            for note in calibration.get("honest_read", []):
                st.write(f"- {note}")

# --------------------------------------------------------------- 6 HIL gateway
with tab_hil:
    st.subheader("Hardware-in-the-loop gateway evidence")
    summary = data.live_summary or data.replay_summary
    if not summary:
        st.markdown(
            "<div class='saanjh-note'>No gateway run found. Generate replay evidence with "
            "<code>python -m gateway.service --mode replay --nodes 3 --hours 6</code>, or run "
            "<code>--mode live</code> with the CM4 + SX1262 HAT attached.</div>",
            unsafe_allow_html=True,
        )
    else:
        kpi = replay_kpis(summary)
        source = "LIVE radio" if data.live_summary else "Seeded replay"
        if data.live_summary.get("session_open"):
            source += " (session in progress)"
        st.caption(f"{source} · {kpi['nodes']} nodes · {_num(kpi['hours'], 1, ' h')} · "
                   f"feeder peak {_num(kpi['profile_peak_kw'], 0, ' kW')}")
        _metric_row([
            ("Telemetry success", _num(kpi["packet_success_pct"], 1, "%"),
             f"{kpi['telemetry_received']}/{kpi['telemetry_sent']} packets"),
            ("Command delivery", _num(kpi["command_success_pct"], 1, "%"),
             f"{kpi['commands_delivered']}/{kpi['commands_sent']} commands"),
            ("ACK rate", _num(kpi["command_ack_pct"], 1, "%"), None),
            ("Mean / p95 latency", f"{_num(kpi['mean_latency_ms'], 0)} / {_num(kpi['p95_latency_ms'], 0)} ms", None),
        ])
        _metric_row([
            ("SoC floor", _num(kpi["soc_min_pct"], 1, "%"), "Policy floor is 70%"),
            ("Reserve breaches", _num(kpi["reserve_breaches"], 0), None),
            ("DT overload before", _num(kpi["overload_before_min"], 0, " min"), None),
            ("DT overload after", _num(kpi["overload_after_min"], 0, " min"), None),
        ])

        if not data.grid.empty:
            grid = data.grid.iloc[::30].copy()
            fig = _fig(360)
            fig.add_trace(go.Scatter(x=grid["ts"], y=grid["grid_kw"], name="Feeder load",
                                     line=dict(color=GREY, width=1.5)))
            fig.add_trace(go.Scatter(x=grid["ts"], y=grid["relief_kw"], name="Relief delivered",
                                     line=dict(color=GREEN, width=2), fill="tozeroy"))
            fig.update_layout(title="Feeder load and measured relief (10 s samples, plotted every 5 min)",
                              yaxis_title="kW")
            st.plotly_chart(fig, use_container_width=True)

        if not data.telemetry.empty:
            st.markdown("**Relay state per node (1 = load on battery, 0 = grid)**")
            fig = _fig(280)
            for node_id, frame in data.telemetry.groupby("node_id"):
                frame = frame.iloc[::30]
                fig.add_trace(go.Scatter(
                    x=frame["ts"], y=frame["relay"], name=f"Node {node_id}",
                    line_shape="hv", line=dict(width=2),
                ))
            fig.update_layout(yaxis=dict(range=[-0.1, 1.1], title="Relay"))
            st.plotly_chart(fig, use_container_width=True)

        if not data.commands.empty:
            st.markdown("**Commands and acknowledgements**")
            commands = data.commands.tail(15).copy()
            _table(commands)

        peak_commanded = None
        if not data.dispatch.empty:
            peak_commanded = data.dispatch["commanded_kw"].max()
        if peak_commanded is not None:
            st.markdown(
                f"<div class='saanjh-note'><strong>Scale note:</strong> the physical bench is "
                f"{kpi['nodes']} nodes and commanded at most {_num(peak_commanded, 2)} kW. "
                f"It proves the control path, the packet format and the safety interlocks on a "
                f"{_num(kpi['profile_peak_kw'], 0)} kW feeder profile. Feeder-scale relief is "
                f"modelled in the annual simulation, not claimed from this bench.</div>",
                unsafe_allow_html=True,
            )

        with st.expander("Reproduce this evidence"):
            st.code(
                "python -m gateway.service --mode replay --nodes 3 --hours 6 "
                "--duration-min 45 --packet-loss 0.02\n"
                "# live hardware:\n"
                "python -m gateway.service --mode live --transport spi --nodes 3",
                language="bash",
            )

# ------------------------------------------------------------ 7 DISCOM dispatch
with tab_discom:
    st.subheader("DISCOM dispatch decisions")
    if data.dispatch.empty:
        st.caption("No dispatch log yet. Run the gateway replay or live service.")
    else:
        dispatch = data.dispatch.copy()
        dispatched = dispatch[dispatch["commanded_kw"] > 0]
        _metric_row([
            ("Decision intervals", _num(len(dispatch), 0), "Every 15 minutes"),
            ("Intervals with dispatch", _num(len(dispatched), 0), None),
            ("Peak commanded", _num(dispatch["commanded_kw"].max(), 2, " kW"), None),
            ("Peak residual gap", _num(dispatch["residual_kw"].max(), 1, " kW"), None),
        ])
        last = dispatch.iloc[-1]
        st.markdown(
            f"<div class='saanjh-note'><strong>Latest directive "
            f"({last['ts']:%d %b %H:%M}):</strong> {last['headline']}</div>",
            unsafe_allow_html=True,
        )
        fig = _fig(360)
        fig.add_trace(go.Scatter(x=dispatch["ts"], y=dispatch["gap_kw"], name="Flexibility gap",
                                 line=dict(color=AMBER, width=2, dash="dash")))
        fig.add_trace(go.Scatter(x=dispatch["ts"], y=dispatch["commanded_kw"], name="Commanded",
                                 line=dict(color=GREEN, width=2)))
        fig.add_trace(go.Scatter(x=dispatch["ts"], y=dispatch["residual_kw"], name="Residual",
                                 line=dict(color=RED, width=1.5)))
        fig.update_layout(title="Gap, command and residual", yaxis_title="kW")
        st.plotly_chart(fig, use_container_width=True)
        _table(dispatch.tail(12)[["ts", "grid_load_kw", "limit_kw", "gap_kw",
                                  "commanded_kw", "residual_kw", "action", "headline"]])

st.divider()
st.caption(
    "SAANJH Phase 1 prototype · MIT licence · simulation results are committed; "
    "hardware evidence is labelled replay or live and is never presented as utility data."
)
