# views.py
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go

def show_introduction():
    st.markdown("""
    ### Introduction
    The "Ten State Project" is a research initiative focused on evaluating climate risk vulnerabilities across ten U.S. states, emphasizing the interplay between environmental hazards, socioeconomic challenges, and health outcomes. By integrating advanced climate modeling with socioeconomic and health data, the project identifies regions most susceptible to extreme weather events like droughts, wildfires, and windstorms, particularly in low-income and marginalized communities. It aims to raise awareness among local populations about the compounded risks they face, such as increased asthma prevalence due to environmental stressors, and to provide data-driven insights for building resilience. The project uses tools like the Generalized Extreme Value (GEV) model to forecast future climate risks and overlays this with health and economic indicators to highlight disparities, enabling targeted interventions for at-risk areas.

    Our project, the "Multi-Hazard + Community Vulnerability Dashboard," builds on the "Ten State Project" by offering an interactive tool to explore these vulnerabilities at the county level across the U.S. We utilize datasets from AT&T Climate Resiliency, covering drought, wildfire, and wind risks, alongside U.S. Census Bureau data on socioeconomic factors and health metrics like asthma and diabetes rates. The dashboard allows users to filter by state, hazard type, and health indicators, providing a granular view of how climate risks intersect with economic and health challenges. For instance, users can filter for Texas to see counties with high asthma rates and low-income populations, or examine Georgia for life expectancy disparities. By making this data accessible, we aim to empower community leaders, policymakers, and residents to address climate risks equitably, bridging the gap between complex data and actionable insights for vulnerable populations.

    ---
    """)

def hazard_map_view(wind_df_filtered, drought_df_filtered, wildfire_df_filtered, selected_state, metric_name_map):
    hazard_options = ["Wind Risk", "Drought Risk", "Wildfire Risk"]
    hazard_raw_map = {"Wind Risk": "Wind_Risk", "Drought Risk": "Drought_Risk", "Wildfire Risk": "Wildfire_Risk"}
    hazards = st.sidebar.multiselect("Hazards", hazard_options, default=["Wind Risk"])
    threshold = st.sidebar.slider("Minimum Risk Level", 0.0, 50.0, 5.0, 1.0)

    st.subheader(f"Hazard Exposure Across Counties ({selected_state if selected_state != 'All' else 'All States'})")
    st.markdown("**Note**: Risk reflects 10-year median projections. Marker size shows low-income %, color intensity shows risk level. Adjust threshold or select multiple hazards to compare.")
    
    fig = go.Figure()
    colors = {"Wind Risk": "Blues", "Drought Risk": "Oranges", "Wildfire Risk": "Reds"}
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if filtered.empty:
            st.warning(f"No counties meet the risk threshold for {metric_name_map[risk_col]} in {selected_state if selected_state != 'All' else 'the selected states'}.")
            continue
        fig.add_trace(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + metric_name_map[risk_col] + ": " + filtered[risk_col].astype(str),
            marker=dict(
                size=filtered["MEAN_low_income_percentage"].clip(0, 100) * 0.15 + 5,
                color=filtered[risk_col],
                colorscale=colors[h],
                showscale=False,
                sizemode="diameter",
                sizemin=5
