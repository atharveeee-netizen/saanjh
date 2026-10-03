import streamlit as st
import plotly.graph_objects as go

def render(saanjh_df, kpis):
    st.markdown("<h3 class='title-green'>EVENT EVT-103</h3>", unsafe_allow_html=True)
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("#### Status")
        st.success("🟢 DISPATCHING")
        st.write("**Start:** 18:30")
        st.write("**Duration:** 90 min")
        
    with col2:
        st.markdown("#### Flexibility Metrics")
        st.write(f"**Required:** {kpis['peak_reduction_kw'] + 1.8:.1f} kW") # simulated req
        st.write(f"**Committed:** {kpis['flexibility_delivered_kw'] * 1.1:.1f} kW")
        st.write(f"**Delivered:** {kpis['flexibility_delivered_kw']:.1f} kW")
        
        st.progress(kpis['dependable_flexibility_ratio'])
        st.caption(f"Dependability Ratio: {kpis['dependable_flexibility_ratio']*100:.1f}%")
        
    with col3:
        st.markdown("#### Node Participation")
        st.write(f"**Active Nodes:** {kpis['homes_participating']} / 42")
        st.write("**Recovery Phase starts:** 20:00")
        
    st.markdown("---")
    st.markdown("#### Real-time Voltage")
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=saanjh_df['Time'], y=saanjh_df['Voltage_V'], mode='lines', line=dict(color='#4299E1', width=2), name='Voltage (V)'))
    fig.add_hline(y=210, line_dash="dash", line_color="red", annotation_text="Low Voltage Threshold (210V)")
    
    fig.update_layout(
        plot_bgcolor='rgba(0,0,0,0)',
        paper_bgcolor='rgba(0,0,0,0)',
        font=dict(color='#A0AEC0'),
        xaxis=dict(title='Time (Hour of Day)', showgrid=False),
        yaxis=dict(title='Voltage (V)', gridcolor='#2D3748', range=[200, 250]),
        height=300,
        margin=dict(l=0, r=0, t=10, b=0)
    )
    
    st.plotly_chart(fig, use_container_width=True)
