import streamlit as st
import plotly.graph_objects as go
import pandas as pd
import time

def render(baseline_df, saanjh_df):
    col1, col2, col3, col4 = st.columns(4)
    
    # We'll pick a specific time to display current stats (e.g. 19:30)
    current_idx = 42 # 19:30
    if current_idx >= len(saanjh_df):
        current_idx = len(saanjh_df) - 1
        
    current_time = saanjh_df.iloc[current_idx]['Time']
    current_load = saanjh_df.iloc[current_idx]['Load_kW']
    forecast_peak = baseline_df['Load_kW'].max()
    flex_delivered = saanjh_df.iloc[current_idx]['Flexibility_Delivered_kW']
    dt_loading = saanjh_df.iloc[current_idx]['Transformer_Loading_%']
    
    with col1:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Current Load</div><div class='metric-value'>{current_load:.1f} kW</div></div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Forecast Peak</div><div class='metric-value'>{forecast_peak:.1f} kW</div></div>", unsafe_allow_html=True)
    with col3:
        st.markdown(f"<div class='metric-card'><div class='metric-label'>Active Flexibility</div><div class='metric-value'>{flex_delivered:.1f} kW</div></div>", unsafe_allow_html=True)
    with col4:
        color = "#E53E3E" if dt_loading > 95 else "#3DCD58"
        st.markdown(f"<div class='metric-card' style='border-color: {color}'><div class='metric-label'>DT Loading</div><div class='metric-value' style='color: {color}'>{dt_loading:.1f}%</div></div>", unsafe_allow_html=True)
        
    st.markdown("### Load Profile")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=baseline_df['Time'], y=baseline_df['Load_kW'], mode='lines', line=dict(color='gray', dash='dash'), name='Baseline Forecast'))
    fig.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Load_kW'], mode='lines', line=dict(color='#3DCD58', width=3), name='SAANJH Actual Load'))
    
    # Fill between
    fig.add_trace(go.Scatter(
        x=pd.concat([saanjh_df['Time'], saanjh_df['Time'][::-1]]),
        y=pd.concat([saanjh_df['Load_kW'], baseline_df['Load_kW'][::-1]]),
        fill='toself',
        fillcolor='rgba(61, 205, 88, 0.2)',
        line=dict(color='rgba(255,255,255,0)'),
        hoverinfo="skip",
        showlegend=True,
        name='Flexibility Dispatched'
    ))
    
    fig.add_hline(y=100*0.95, line_dash="dot", line_color="orange", annotation_text="DT 100% Rating")
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#A0AEC0'),
        xaxis=dict(title='Time (Hour of Day)', showgrid=False),
        yaxis=dict(title='Load (kW)', gridcolor='#2D3748'),
        margin=dict(l=0, r=0, t=30, b=0),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    
    st.plotly_chart(fig, use_container_width=True)
