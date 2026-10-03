import streamlit as st
import pandas as pd
import json
import os
import plotly.graph_objects as go
from plotly.subplots import make_subplots

st.set_page_config(
    page_title="SAANJH | Digital Twin Control Center",
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
        border: 1px solid rgba(255, 255, 255, 0.05);
        border-radius: 8px;
        padding: 15px;
        border-left: 4px solid #3DCD58;
    }
    .stMetric[data-testid="stMetricValue"] {
        color: #3DCD58 !important;
    }
</style>
""", unsafe_allow_html=True)

# Load data with provenance
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    res_dir = os.path.join(base_dir, 'simulation', 'data', 'results')
    
    baseline = pd.read_csv(os.path.join(res_dir, 'baseline_profile.csv'))
    saanjh = pd.read_csv(os.path.join(res_dir, 'saanjh_profile.csv'))
    
    with open(os.path.join(res_dir, 'comparison.json'), 'r') as f:
        kpis = json.load(f)
        
    # Attempt to load pypsa validation
    pypsa_path = os.path.join(res_dir, 'pypsa_saanjh_validation.csv')
    if os.path.exists(pypsa_path):
        pypsa = pd.read_csv(pypsa_path)
    else:
        pypsa = None
        
    return baseline, saanjh, kpis, pypsa

baseline_df, saanjh_df, kpis, pypsa_df = load_data()

st.title("⚡ SAANJH Digital Twin Control Center")
st.markdown("### Neighbourhood LV Edge Flexibility Layer")

if baseline_df is None:
    st.error("No simulation data found. Please run the simulation pipeline.")
    st.stop()

# --- SIDEBAR (System Status) ---
st.sidebar.title("📡 System Status")
st.sidebar.markdown("**Node:** RPi CM4 Edge Gateway")
st.sidebar.markdown("**Network:** LoRaWAN Mesh")
st.sidebar.markdown("**Transformer:** 100 kVA (FDR-021)")
st.sidebar.divider()
st.sidebar.metric("Current Mode", "SAANJH Active")
st.sidebar.metric("Homes Online", f"{kpis['homes_participating']} / 60")
st.sidebar.metric("Available Flexibility", f"{kpis['flexibility_delivered_kw']:.1f} kW")

# --- MAIN DASHBOARD TABS ---
tab1, tab2, tab3, tab4 = st.tabs([
    "Virtual Battery & Dispatch", 
    "Grid State & Transformer", 
    "Event Timeline",
    "Independent Physics Validation (PyPSA)"
])

# --- TAB 1: VIRTUAL BATTERY ---
with tab1:
    st.subheader("Virtual Battery Aggregation Layer")
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Peak Load (Baseline)", f"{kpis['baseline_peak_kw']:.1f} kW")
    col2.metric("Peak Load (SAANJH)", f"{kpis['saanjh_peak_kw']:.1f} kW", delta=f"-{kpis['peak_reduction_kw']:.1f} kW", delta_color="normal")
    col3.metric("Peak Reduction", f"{kpis['peak_reduction_pct']:.1f} %")
    col4.metric("Dependable Flex Ratio", f"{kpis['dependable_flexibility_ratio']*100:.1f} %")
    
    fig1 = go.Figure()
    fig1.add_trace(go.Scatter(x=saanjh_df['Time'], y=baseline_df['Load_kW'], name='Baseline (Unmanaged)', line=dict(color='#ff4d4d', dash='dash')))
    fig1.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Load_kW'], name='SAANJH (Managed)', fill='tonexty', line=dict(color='#3DCD58')))
    fig1.add_trace(go.Scatter(x=saanjh_df['Time'], y=[85]*len(saanjh_df), name='Safe Threshold', line=dict(color='#A0AEC0', dash='dot')))
    fig1.update_layout(title="Feeder Active Power Dispatch", xaxis_title="Time (Hour)", yaxis_title="Load (kW)", template="plotly_dark")
    st.plotly_chart(fig1, use_container_width=True)

# --- TAB 2: GRID STATE ---
with tab2:
    st.subheader("Transformer & Voltage State")
    c1, c2 = st.columns(2)
    c1.metric("Baseline Overload Time", f"{kpis['baseline_overload_minutes']} min")
    c2.metric("SAANJH Overload Time", f"{kpis['saanjh_overload_minutes']} min")
    
    fig2 = go.Figure()
    fig2.add_trace(go.Scatter(x=saanjh_df['Time'], y=baseline_df['Transformer_Loading_%'], name='Baseline Loading %', line=dict(color='#ff4d4d')))
    fig2.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Transformer_Loading_%'], name='SAANJH Loading %', fill='tozeroy', line=dict(color='#3DCD58')))
    fig2.update_layout(title="Transformer Thermal Stress", xaxis_title="Time (Hour)", yaxis_title="Loading (%)", template="plotly_dark")
    st.plotly_chart(fig2, use_container_width=True)

# --- TAB 3: EVENT TIMELINE ---
with tab3:
    st.subheader("Operational Event Timeline")
    st.markdown("""
    - **16:00**: Normal Grid State. Solar generation declining.
    - **17:45**: Forecast Engine detects impending >85% transformer load via XGBoost ML model.
    - **18:00**: SAANJH Virtual Battery Aggregator locks flexibility pool.
    - **18:15**: Precision Dispatch begins. Distributed batteries offset critical peak.
    - **20:30**: Grid stress abates. Safe stagger recovery initiated.
    - **22:00**: Event concluded.
    """)
    
    fig3 = go.Figure()
    fig3.add_trace(go.Bar(x=saanjh_df['Time'], y=saanjh_df['Flexibility_Delivered_kW'], name='Flexibility Dispatched (kW)', marker_color='#3DCD58'))
    fig3.update_layout(title="Virtual Battery Dispatch Volume", xaxis_title="Time (Hour)", yaxis_title="Power (kW)", template="plotly_dark")
    st.plotly_chart(fig3, use_container_width=True)

# --- TAB 4: PYPSA VALIDATION ---
with tab4:
    st.subheader("Independent PyPSA Physics Validation")
    if pypsa_df is not None:
        st.markdown("The SAANJH simulated timeseries was pushed through a formal non-linear AC Newton-Raphson load flow solver to verify physical plausibility.")
        
        fig4 = go.Figure()
        fig4.add_trace(go.Scatter(x=pypsa_df['Time'], y=pypsa_df['PyPSA_Voltage_V'], name='Feeder Node Voltage (V)', line=dict(color='#00d4ff')))
        fig4.add_trace(go.Scatter(x=pypsa_df['Time'], y=[240]*len(pypsa_df), name='Nominal (240V)', line=dict(color='white', dash='dash')))
        fig4.update_layout(title="Validated Feeder Voltage Profile", xaxis_title="Time (Hour)", yaxis_title="Voltage (V)", template="plotly_dark")
        st.plotly_chart(fig4, use_container_width=True)
    else:
        st.warning("PyPSA validation results not found. Please run the validation script.")
