import streamlit as st
import plotly.graph_objects as go

def render(kpis):
    st.markdown("### Performance vs Baseline")
    
    c1, c2, c3, c4 = st.columns(4)
    
    c1.metric("Peak Load", f"{kpis['saanjh_peak_kw']:.1f} kW", f"-{kpis['peak_reduction_kw']:.1f} kW", delta_color="inverse")
    c2.metric("Overload Duration", f"{kpis['saanjh_overload_minutes']} min", f"-{kpis['baseline_overload_minutes'] - kpis['saanjh_overload_minutes']} min", delta_color="inverse")
    c3.metric("Voltage Violations", f"{kpis['voltage_violations_saanjh']}", f"-{kpis['voltage_violations_baseline'] - kpis['voltage_violations_saanjh']}", delta_color="inverse")
    c4.metric("Dependability Ratio", f"{kpis['dependable_flexibility_ratio']*100:.1f}%")
    
    st.markdown("---")
    st.markdown("### Unit Economics")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown(f"""
        **SAANJH Capital Efficiency**
        * Target Flexibility: 15 kW
        * Measured Dependable Flex: {kpis['flexibility_delivered_kw']:.1f} kW
        * Cost per Dependable kW: **₹ {kpis['cost_per_dependable_kw']:,}**
        """)
        
    with col2:
        # Cost comparison chart
        fig = go.Figure(data=[
            go.Bar(name='Cost / kW', x=['SAANJH Edge', 'Community Battery', 'Transformer Upgrade'], y=[2083, 25000, 8000], marker_color=['#3DCD58', '#E2E8F0', '#E2E8F0'])
        ])
        fig.update_layout(
            title='Cost per Dependable kW Flexibility (₹)',
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='#A0AEC0'),
            yaxis=dict(gridcolor='#2D3748'),
            height=250,
            margin=dict(l=0, r=0, t=30, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)
