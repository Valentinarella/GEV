import streamlit as st
import pandas as pd
import plotly.graph_objects as go

st.set_page_config(layout="wide")
st.title("🌎 U.S. Climate Risk Map")

# Sidebar with radio buttons
selected_layer = st.sidebar.radio(
    "Select Hazard Layer",
    ["Wind Risk", "Drought", "Wildfire"],
    index=0
)

# Load Wind Risk data
@st.cache_data
def load_wind_data():
    url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
    df = pd.read_csv(url)
    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": "Wind_Risk",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })
    df = df.dropna(subset=["Lat", "Lon", "Wind_Risk"])
    df["County"] = df["County"].str.title()
    return df

# Load Drought Risk data
@st.cache_data
def load_drought_data():
    url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
    df = pd.read_csv(url)
    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": "Drought_Risk",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })
    df = df.dropna(subset=["Lat", "Lon", "Drought_Risk"])
    df["County"] = df["County"].str.title()
    return df

# Load Wildfire Risk data
@st.cache_data
def load_wildfire_data():
    url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
    df = pd.read_csv(url)
    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": "Wildfire_Risk",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })
    df = df.dropna(subset=["Lat", "Lon", "Wildfire_Risk"])
    df["County"] = df["County"].str.title()
    return df

# Load data
wind_df = load_wind_data()
drought_df = load_drought_data()
wildfire_df = load_wildfire_data()

# Create base map
fig = go.Figure()

# Plot layer based on selected hazard
if selected_layer == "Wind Risk" and not wind_df.empty:
    fig.add_trace(go.Scattergeo(
        lon=wind_df["Lon"],
        lat=wind_df["Lat"],
        text=wind_df["County"] + ", " + wind_df["State"] +
             "<br>Wind Risk: " + wind_df["Wind_Risk"].astype(str),
        marker=dict(
            size=wind_df["Low_Income_Pct"] * 0.5,
            color=wind_df["Wind_Risk"],
            colorscale="Blues",
            showscale=True,
            colorbar=dict(title="Wind Risk")
        ),
        name="Wind Risk"
    ))

elif selected_layer == "Drought" and not drought_df.empty:
    fig.add_trace(go.Scattergeo(
        lon=drought_df["Lon"],
        lat=drought_df["Lat"],
        text=drought_df["County"] + ", " + drought_df["State"] +
             "<br>Drought Risk: " + drought_df["Drought_Risk"].astype(str),
        marker=dict(
            size=drought_df["Low_Income_Pct"] * 0.5,
            color=drought_df["Drought_Risk"],
            colorscale="Oranges",
            showscale=True,
            colorbar=dict(title="Drought Risk")
        ),
        name="Drought"
    ))

elif selected_layer == "Wildfire" and not wildfire_df.empty:
    fig.add_trace(go.Scattergeo(
        lon=wildfire_df["Lon"],
        lat=wildfire_df["Lat"],
        text=wildfire_df["County"] + ", " + wildfire_df["State"] +
             "<br>Wildfire Risk: " + wildfire_df["Wildfire_Risk"].astype(str),
        marker=dict(
            size=wildfire_df["Low_Income_Pct"] * 0.5,
            color=wildfire_df["Wildfire_Risk"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(title="Wildfire Risk")
        ),
        name="Wildfire"
    ))

# Map layout
fig.update_layout(
    geo=dict(
        scope="usa",
        landcolor="rgb(230, 230, 230)",
        lakecolor="rgb(255, 255, 255)",
        subunitcolor="rgb(255, 255, 255)",
        showland=True
    ),
    showlegend=False,
    height=700,
    margin=dict(l=0, r=0, t=20, b=0)
)

# Display map
st.plotly_chart(fig, use_container_width=True)
