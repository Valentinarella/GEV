import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Metric Name Mapping ---
metric_name_map = {
    "Wind_Risk": "Wind Risk Score",
    "Drought_Risk": "Drought Risk Score",
    "Wildfire_Risk": "Wildfire Risk Score",
    "MEAN_low_income_percentage": "Low-Income Population (%)",
    "Identified as disadvantaged": "Disadvantaged Community",
    "Energy burden": "Energy Burden (%)",
    "PM2.5 in the air": "PM2.5 Air Pollution (µg/m³)",
    "Current asthma among adults aged greater than or equal to 18 years": "Adult Asthma Rate (%)",
    "Share of properties at risk of fire in 30 years": "Properties at Fire Risk (%)",
    "Total population": "Total Population",
    "Asthma_Rate____": "Asthma Rate (%)",
    "Diabetes_Rate____": "Diabetes Rate (%)",
    "Heart_Disease_Rate____": "Heart Disease Rate (%)",
    "Life_expectancy__years_": "Life Expectancy (Years)"
}

# --- URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
health_url = "https://undivideprojectdata.blob.core.windows.net/gev/health.csv?sp=r&st=2025-05-31T00:13:59Z&se=2090-05-31T08:13:59Z&spr=https&sv=2024-11-04&sr=b&sig=8epnZK%2FXbnblTCiYlmtuYHgBy43yxCHTtS7FqLu134k%3D"

# --- Loaders ---
@st.cache_data
def load_hazard(url, risk_col):
    try:
        df = pd.read_csv(url, usecols=["CF", "SF", "Latitude", "Longitude", "MEAN_low_income_percentage", "midcent_median_10yr"])
        df = df.rename(columns={"CF": "County", "SF": "State", "Latitude": "Lat", "Longitude": "Lon", 
                                "MEAN_low_income_percentage": "MEAN_low_income_percentage", "midcent_median_10yr": risk_col})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        # Ensure risk_col and MEAN_low_income_percentage are numeric
        df[risk_col] = pd.to_numeric(df[risk_col], errors='coerce')
        df["MEAN_low_income_percentage"] = pd.to_numeric(df["MEAN_low_income_percentage"], errors='coerce')
        return df.dropna(subset=["Lat", "Lon", risk_col])
    except Exception as e:
        st.error(f"Error loading data from {url}: {e}")
        return pd.DataFrame()

@st.cache_data
def load_census():
    try:
        df = pd.read_csv(census_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"County Name": "County", "State/Territory": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df
    except Exception as e:
        st.error(f"Error loading census data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_health_data():
    try:
        df = pd.read_csv(health_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"CF": "County", "SF": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df.dropna(subset=["MEAN_low_income_percentage"])
    except Exception as e:
        st.error(f"Error loading health data: {e}")
        return pd.DataFrame()

@st.cache_data
def filter_hazard_data(df, risk_col, threshold):
    filtered_df = df[df[risk_col] >= threshold]
    # Re-ensure risk_col is numeric after filtering
    filtered_df[risk_col] = pd.to_numeric(filtered_df[risk_col], errors='coerce')
    return filtered_df.dropna(subset=[risk_col])

# --- Load data ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census()
health_df = load_health_data()

# --- UI Setup ---
st.title("📊 Multi-Hazard + Community Vulnerability Dashboard")

# --- Introduction ---
st.markdown("""
### Introduction
The "Ten State Project" is a research initiative focused on evaluating climate risk vulnerabilities across ten U.S. states, emphasizing the interplay between environmental hazards, socioeconomic challenges, and health outcomes. By integrating advanced climate modeling with socioeconomic and health data, the project identifies regions most susceptible to extreme weather events like droughts, wildfires, and windstorms, particularly in low-income and marginalized communities. It aims to raise awareness among local populations about the compounded risks they face, such as increased asthma prevalence due to environmental stressors, and to provide data-driven insights for building resilience. The project uses tools like the Generalized Extreme Value (GEV) model to forecast future climate risks and overlays this with health and economic indicators to highlight disparities, enabling targeted interventions for at-risk areas.

Our project, the "Multi-Hazard + Community Vulnerability Dashboard," builds on the "Ten State Project" by offering an interactive tool to explore these vulnerabilities at the county level across the U.S. We utilize datasets from AT&T Climate Resiliency, covering drought, wildfire, and wind risks, alongside U.S. Census Bureau data on socioeconomic factors and health metrics like asthma and diabetes rates. The dashboard allows users to filter by state, hazard type, and health indicators, providing a granular view of how climate risks intersect with economic and health challenges. For instance, users can filter for Texas to see counties with high asthma rates and low-income populations, or examine Georgia for life expectancy disparities. By making this data accessible, we aim to empower community leaders, policymakers, and residents to address climate risks equitably, bridging the gap between complex data and actionable insights for vulnerable populations.

---
""")

# --- State Filter ---
st.sidebar.title("Filters")
states = sorted(health_df["State"].unique().tolist
