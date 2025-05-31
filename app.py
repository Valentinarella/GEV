# app.py
import streamlit as st
from data_loader import load_hazard, load_census, load_health_data, filter_hazard_data, filter_by_state
from constants import metric_name_map, wind_url, drought_url, wildfire_url, census_url, health_url
from views import show_introduction, hazard_map_view, community_indicators_view, health_income_view, show_key_findings

# --- Page config ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Load data ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census(census_url)
health_df = load_health_data(health_url)

# --- UI Setup ---
st.title("📊 Multi-Hazard + Community Vulnerability Dashboard")

# --- Introduction ---
show_introduction()

# --- State Filter ---
st.sidebar.title("Filters")
states = sorted(health_df["State"].unique().tolist())
selected_state = st.sidebar.selectbox("Select State", ["All"] + states, index=0)

# --- Apply State Filter to Datasets ---
wind_df_filtered = filter_by_state(wind_df, selected_state)
drought_df_filtered = filter_by_state(drought_df, selected_state)
wildfire_df_filtered = filter_by_state(wildfire_df, selected_state)
census_df_filtered = filter_by_state(census_df, selected_state)
health_df_filtered = filter_by_state(health_df, selected_state)

# --- View Selector ---
st.sidebar.title("Navigation")
view = st.sidebar.selectbox("Choose Section", 
                            ["Hazard Map", "Community Indicators", "Health & Income"],
                            help="Pick a view: Hazard Map for climate risks, Community Indicators for demographics, or Health & Income for disparities.")

# --- Render Views ---
if view == "Hazard Map":
    hazard_map_view(wind_df_filtered, drought_df_filtered, wildfire_df_filtered, selected_state, metric_name_map)
elif view == "Community Indicators":
    community_indicators_view(census_df_filtered, selected_state, metric_name_map)
else:
    health_income_view(health_df_filtered, selected_state, metric_name_map)

# --- Key Findings ---
show_key_findings()
