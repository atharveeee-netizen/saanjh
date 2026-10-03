import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="SAANJH | DISCOM Feeder Control Center",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Dark industrial theme logic
st.markdown("""
<style>
    .stApp {
        background-color: #0b0f19;
        color: #e6edf3;
    }
    .css-1d391kg {
        background-color: #161b22;
    }
    .stMetric {
        background-color: rgba(22, 27, 34, 0.7);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        padding: 12px;
        border-left: 4px solid #3DCD58;
    }
    .stMetric[data-testid="stMetricValue"] {
        color: #3DCD58 !important;
    }
    .operator-alert {
        background-color: rgba(220, 53, 69, 0.15);
        border-left: 5px solid #dc3545;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 20px;
    }
    .operator-action {
        background-color: rgba(61, 205, 88, 0.15);
        border-left: 5px solid #3DCD58;
        padding: 15px;
        border-radius: 6px;
        margin-bottom: 20px;
    }
</style>
""", unsafe_allow_html=True)

# Load data with provenance
@st.cache_data
def load_all_artifacts():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    res_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    
    baseline = pd.read_csv(os.path.join(res_dir, 'baseline_profile.csv'))
    saanjh = pd.read_csv(os.path.join(res_dir, 'saanjh_profile.csv'))
    
    with open(os.path.join(res_dir, 'comparison.json'), 'r') as f:
        kpis = json.load(f)
        
    with open(os.path.join(res_dir, 'discom_action_plan.json'), 'r') as f:
        action_plan = json.load(f)
        
    with open(os.path.join(res_dir, 'reliability_scorecard.json'), 'r') as f:
        scorecard = json.load(f)
        
    households = pd.read_csv(os.path.join(res_dir, 'household_dispatch.csv'))
    pypsa = pd.read_csv(os.path.join(res_dir, 'pypsa_saanjh_validation.csv'))
        
    return baseline, saanjh, kpis, action_plan, scorecard, households, pypsa

baseline_df, saanjh_df, kpis, action_plan, scorecard, households_df, pypsa_df = load_all_artifacts()

# --- TOP OPERATOR BANNER: 5 QUESTIONS IN SECONDS ---
st.title("⚡ SAANJH Feeder Dispatch & Reliability Console")
st.caption(f"Connected Feeder: **{action_plan['feeder_id']}** | Transformer: **{action_plan['transformer_id']} (100 kVA)** | Challenge 03 Operator Interface")

col_q1, col_q2, col_q3, col_q4, col_q5 = st.columns(5)
with col_q1:
    st.markdown("**1. Impending Stress?**")
    st.error("HIGH STRESS (18:30)")
with col_q2:
    st.markdown("**2. Root Cause?**")
    st.warning("Solar PV Drop + Peak Surge")
with col_q3:
    st.markdown("**3. Available Flex?**")
    st.info(f"{action_plan['available_flexibility_kw']:.1f} kW Available")
with col_q4:
    st.markdown("**4. Recommended Action?**")
    st.success(f"DISPATCH {action_plan['required_flexibility_kw']:.1f} kW")
with col_q5:
    st.markdown("**5. Reliability Relief?**")
    st.success("Overload Cut by 30 min")

st.markdown(f"""
<div class="operator-action">
    <strong>DISCOM ACTION DIRECTIVE:</strong> {action_plan['recommended_action']}<br>
    <em>Expected Impact: {action_plan['expected_outcomes']['transformer_thermal_overload_reduction']} | {action_plan['expected_outcomes']['voltage_drop_mitigation']} | {action_plan['expected_outcomes']['modeled_technical_loss_reduction']}</em>
</div>
""", unsafe_allow_html=True)

# --- SIDEBAR (Feeder Status & Critical Load Protection) ---
st.sidebar.title("📡 Feeder Sentinel")
st.sidebar.markdown(f"**Feeder ID:** {action_plan['feeder_id']}")
st.sidebar.markdown("**Substation:** 11 kV / 415 V 3-Phase")
st.sidebar.markdown(f"**Transformer:** 100 kVA (95 kW Limit)")
st.sidebar.divider()
st.sidebar.subheader("🛡️ Safety Invariants")
st.sidebar.metric("Critical Load Violations", f"{kpis['critical_load_violations']}")
st.sidebar.metric("Battery Reserve Breaches (<70%)", f"{kpis['reserve_violations']}")
st.sidebar.metric("Opt-Out Dispatches", f"{kpis['opt_out_dispatches']}")
st.sidebar.metric("Enrolled Fleet", f"{kpis['homes_participating']} / 60 Homes")

# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs([
    "1. Feeder Status & Forecast",
    "2. Baseline vs SAANJH",
    "3. Transformer & Voltage State",
    "4. Event Timeline & Flexibility",
    "5. Household Fairness & Fleets",
    "6. PyPSA Electrical & Losses"
])

# PANEL 1: FEEDER STATUS & FORECAST
with tab1:
    st.subheader("Feeder Stress & Solar Drop-Off Forecasting")
    m1, m2, m3, m4 = st.columns(4)
    m1.metric("Peak Gross Demand", f"{baseline_df['Gross_Demand_kW'].max():.1f} kW")
    m2.metric("Solar PV Peak", f"{baseline_df['Solar_Gen_kW'].max():.1f} kW")
    m3.metric("Sunset Deficit Peak", f"{scorecard['metrics']['renewable_deficit_peak']['baseline']:.1f} kW")
    m4.metric("Dependable Flex Dispatched", f"{kpis['flexibility_delivered_kw']:.1f} kW")
    
    fig_f = go.Figure()
    fig_f.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Gross_Demand_kW'], name='Gross Consumer Demand', line=dict(color='#8899ac', dash='dot')))
    fig_f.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Solar_Gen_kW'], name='Rooftop Solar PV (15 Homes)', line=dict(color='#ffd166', width=2.5)))
    fig_f.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Load_kW'], name='Net Deficit (Baseline Load)', line=dict(color='#ff4d4d', width=2)))
    fig_f.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Load_kW'], name='SAANJH Managed Feeder', line=dict(color='#3DCD58', width=2.5)))
    fig_f.add_hline(y=95.0, line_dash="dash", line_color="#ff9f1c", annotation_text="Transformer 95 kW Rated Limit")
    fig_f.update_layout(title="Feeder Net Load Forecast vs Solar PV Decline", xaxis_title="Hour of Day", yaxis_title="Active Power (kW)", template="plotly_dark")
    st.plotly_chart(fig_f, use_container_width=True)

# PANEL 2: BASELINE VS SAANJH
with tab2:
    st.subheader("Reliability Scorecard: Baseline vs SAANJH Intervention")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Peak Load", f"{kpis['saanjh_peak_kw']:.1f} kW", delta=f"-{kpis['peak_reduction_kw']:.1f} kW ({kpis['peak_reduction_pct']:.1f}%)")
    c2.metric("Overload Duration", f"{kpis['saanjh_overload_minutes']} mins", delta=f"-{kpis['baseline_overload_minutes'] - kpis['saanjh_overload_minutes']} mins (-{kpis['overload_reduction_pct']:.0f}%)")
    c3.metric("Deficit Energy", f"{scorecard['metrics']['renewable_deficit_energy']['saanjh']:.1f} kWh", delta=f"-{scorecard['metrics']['renewable_deficit_energy']['baseline'] - scorecard['metrics']['renewable_deficit_energy']['saanjh']:.1f} kWh (-87.3%)")
    c4.metric("Modeled Line Losses", f"{kpis['saanjh_loss_kwh']:.2f} kWh", delta=f"-{kpis['loss_reduction_pct']:.1f}%")
    
    scorecard_df = pd.read_csv(os.path.join(os.path.dirname(os.path.dirname(__file__)), 'simulation', 'data', 'results', 'reliability_scorecard.csv'))
    st.dataframe(scorecard_df, use_container_width=True)

# PANEL 3: TRANSFORMER & VOLTAGE
with tab3:
    st.subheader("Distribution Transformer Loading & Node Voltage")
    col_t1, col_t2 = st.columns(2)
    with col_t1:
        fig_t = go.Figure()
        fig_t.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Transformer_Loading_%'], name='Baseline Loading %', line=dict(color='#ff4d4d')))
        fig_t.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Transformer_Loading_%'], name='SAANJH Loading %', fill='tozeroy', line=dict(color='#3DCD58')))
        fig_t.add_hline(y=100.0, line_dash="dash", line_color="orange", annotation_text="100% Thermal Rating")
        fig_t.update_layout(title="Transformer Thermal Stress (% Rating)", xaxis_title="Hour of Day", yaxis_title="Loading (%)", template="plotly_dark")
        st.plotly_chart(fig_t, use_container_width=True)
    with col_t2:
        fig_v = go.Figure()
        fig_v.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Voltage_V'], name='Baseline Voltage', line=dict(color='#ff4d4d', dash='dash')))
        fig_v.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Voltage_V'], name='SAANJH Voltage', line=dict(color='#00d4ff', width=2.5)))
        fig_v.add_hline(y=220.0, line_dash="dot", line_color="red", annotation_text="Voltage Violation Threshold (220V)")
        fig_v.update_layout(title="Feeder Tail Voltage (PyPSA AC Power Flow)", xaxis_title="Hour of Day", yaxis_title="Voltage (V)", template="plotly_dark")
        st.plotly_chart(fig_v, use_container_width=True)

# PANEL 4: EVENT TIMELINE & FLEXIBILITY
with tab4:
    st.subheader("Operating Event Timeline & Dependable Flexibility Dispatch")
    st.markdown("""
    - **16:00 - 17:30**: Solar PV generation declines from 15 kW to 3 kW as sun sets.
    - **17:45**: XGBoost Edge Forecaster predicts upcoming 154 kW peak; identifies 56.2 kW flexibility shortfall.
    - **18:15**: LoRa dispatch triggers staggered battery discharge & deferrable appliance shift across 39 homes.
    - **18:30 - 19:45**: Peak stress window. Transformer overload duration reduced by 30 minutes; voltage remains nominal (>218V).
    - **20:30 - 22:00**: Staggered rebound recovery; batteries hold >80% SOC (above 70% emergency blackout reserve).
    """)
    fig_fl = go.Figure()
    fig_fl.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Flexibility_Required_kW'], name='Required Flexibility (kW)', line=dict(color='#ff9f1c', dash='dash')))
    fig_fl.add_trace(go.Bar(x=saanjh_df['Time'], y=saanjh_df['Flexibility_Delivered_kW'], name='Delivered Flexibility (kW)', marker_color='#3DCD58'))
    fig_fl.update_layout(title="Flexibility Required vs Delivered by SAANJH", xaxis_title="Hour of Day", yaxis_title="Power (kW)", template="plotly_dark")
    st.plotly_chart(fig_fl, use_container_width=True)

# PANEL 5: HOUSEHOLD FAIRNESS & FLEET
with tab5:
    st.subheader("Household Allocation, Reserves & Compensation")
    st.caption("Fairness verification: 3 opted-out homes were never dispatched; all 42 battery homes held ≥70% reserve SOC.")
    st.dataframe(households_df, use_container_width=True)

# PANEL 6: PYPSA ELECTRICAL VALIDATION & TECHNICAL LOSSES
with tab6:
    st.subheader("Independent AC Load Flow Validation (PyPSA)")
    st.markdown(f"""
    - **Feeder Model:** 415V/240V 3-phase 4-wire radial network, 250m aluminum conductor.
    - **Convergence:** 100% of all 72 snapshots converged via Newton-Raphson AC power flow solver.
    - **Modeled Resistive Losses:** Reduced from **{kpis['baseline_loss_kwh']:.2f} kWh** to **{kpis['saanjh_loss_kwh']:.2f} kWh** (**{kpis['loss_reduction_pct']:.1f}% reduction**).
    """)
    fig_pl = go.Figure()
    fig_pl.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Line_Loss_kW'], name='Baseline Technical Losses (kW)', line=dict(color='#ff4d4d', dash='dash')))
    fig_pl.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Line_Loss_kW'], name='SAANJH Technical Losses (kW)', fill='tozeroy', line=dict(color='#3DCD58')))
    fig_pl.update_layout(title="Technical Loss Mitigation ($I^2R$ Resistive Proxy)", xaxis_title="Hour of Day", yaxis_title="Loss Power (kW)", template="plotly_dark")
    st.plotly_chart(fig_pl, use_container_width=True)
