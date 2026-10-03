import streamlit as st
import pandas as pd
import json
import os
from components import feeder_view, event_view, kpi_view

st.set_page_config(
    page_title="SAANJH Grid Control",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Load data
@st.cache_data
def load_data():
    base_dir = os.path.dirname(os.path.dirname(__file__))
    try:
        baseline = pd.read_csv(os.path.join(base_dir, 'simulation', 'data', 'results', 'baseline_profile.csv'))
        saanjh = pd.read_csv(os.path.join(base_dir, 'simulation', 'data', 'results', 'saanjh_profile.csv'))
        with open(os.path.join(base_dir, 'simulation', 'data', 'results', 'comparison.json'), 'r') as f:
            kpis = json.load(f)
        return baseline, saanjh, kpis
    except FileNotFoundError:
        return None, None, None

baseline_df, saanjh_df, kpis = load_data()

# Styling
st.markdown("""
<style>
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
    }
    .metric-card {
        background-color: #262730;
        border-radius: 10px;
        padding: 15px;
        text-align: center;
        border-top: 4px solid #3DCD58;
    }
    .metric-value {
        font-size: 24px;
        font-weight: bold;
        color: #3DCD58;
    }
    .metric-label {
        font-size: 12px;
        color: #A0AEC0;
        text-transform: uppercase;
    }
    .title-green {
        color: #3DCD58;
    }
</style>
""", unsafe_allow_html=True)

st.title("⚡ SAANJH GRID CONTROL")
st.markdown("### Feeder FDR-021 (Urban Low-Voltage)")

if baseline_df is None:
    st.warning("Simulation data not found. Please run `feeder_sim.py` first.")
    st.stop()

tab1, tab2, tab3 = st.tabs(["Feeder Overview", "Event Control", "KPI Dashboard"])

with tab1:
    feeder_view.render(baseline_df, saanjh_df)
    
with tab2:
    event_view.render(saanjh_df, kpis)

with tab3:
    kpi_view.render(kpis)
