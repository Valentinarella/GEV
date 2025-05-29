import streamlit as st
import plotly.express as px

# Load data from separate files
from app1 import load_drought_data
from app2 import load_wind_data
from app3 import load_wildfire_data

# Load datasets
drought_df = load_drought_data()
wind_df = load_wind_data()
wildfire_df = load_wildfire_data()

# App title
st.set_page_config(page_title="Climate Risk Dashboard", layout="wide")
st.title("🌍 Climate Risk Dashboard (USA)")
st.markdown("Compare projected **Drought**, **Wind**, and **Wildfire** risks across U.S. counties.")

# Tabs for each hazard
tab1, tab2, tab3 = st.tabs(["💧 Drought", "🌪️ Wind", "🔥 Wildfire"])

# Drought Map
with tab1:
    st.subheader("Drought Risk (10-Year Median)")
    fig1 = px.scatter_mapbox(
        drought_df,
        lat="Lat",
        lon="Lon",
        color="Drought_Risk",
        hover_name="County",
        hover_data=["State", "Low_Income_Pct"],
        color_continuous_scale="YlGnBu",
        zoom=3
    )
    fig1.update_layout(mapbox_style="carto-positron", margin={"r":0, "t":0, "l":0, "b":0})
    st.plotly_chart(fig1, use_container_width=True)

# Wind Map
with tab2:
    st.subheader("Wind Risk (10-Year Median)")
    fig2 = px.scatter_mapbox(
        wind_df,
        lat="Lat",
        lon="Lon",
        color="Wind_Risk",
        hover_name="County",
        hover_data=["State", "Low_Income_Pct"],
        color_continuous_scale="Viridis",
        zoom=3
    )
    fig2.update_layout(mapbox_style="white-bg", margin={"r":0, "t":0, "l":0, "b":0})
    st.plotly_chart(fig2, use_container_width=True)

# Wildfire Map
with tab3:
    st.subheader("Wildfire Risk (10-Year Median)")
    fig3 = px.scatter_mapbox(
        wildfire_df,
        lat="Lat",
        lon="Lon",
        color="Wildfire_Risk",
        hover_name="County",
        hover_data=["State", "Low_Income_Pct"],
        color_continuous_scale="OrRd",
        zoom=3
    )
    fig3.update_layout(mapbox_style="open-street-map", margin={"r":0, "t":0, "l":0, "b":0})
    st.plotly_chart(fig3, use_container_width=True)
