import streamlit as st
import pandas as pd
import plotly.graph_objects as go
st.cache_data.clear()

# Sidebar controls
st.sidebar.header("Filter Options")

# Radio button to choose hazard layer
selected_layer = st.sidebar.radio(
    "Select Hazard Layer",
    ["Wind Risk", "Drought", "Wildfire"],
    index=0
)

# Slider for minimum risk threshold
threshold = st.sidebar.slider(
    f"Minimum {selected_layer} Risk",
    min_value=0.0,
    max_value=50.0,
    value=5.0,
    step=1.0
)

# Optional county search
county_search = st.sidebar.text_input("Search County (optional)").strip().lower()

# --- Load data ---
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

# Load datasets
wind_df = load_wind_data()
drought_df = load_drought_data()
wildfire_df = load_wildfire_data()

# Filter by county search and threshold
def filter_df(df, risk_col):
    if county_search:
        df = df[df["County"].str.lower().str.contains(county_search)]
    return df[df[risk_col] >= threshold]

# Plot setup
fig = go.Figure()

if selected_layer == "Wind Risk":
    df = filter_df(wind_df, "Wind_Risk")
    fig.add_trace(go.Scattergeo(
        lon=df["Lon"],
        lat=df["Lat"],
        text=df["County"] + ", " + df["State"] + "<br>Wind Risk: " + df["Wind_Risk"].astype(str),
        marker=dict(
            size=df["Low_Income_Pct"] * 0.7,
            color=df["Wind_Risk"],
            colorscale="Blues",
            showscale=True,
            colorbar=dict(title="Wind Risk")
        ),
        name="Wind Risk"
    ))

elif selected_layer == "Drought":
    df = filter_df(drought_df, "Drought_Risk")
    fig.add_trace(go.Scattergeo(
        lon=df["Lon"],
        lat=df["Lat"],
        text=df["County"] + ", " + df["State"] + "<br>Drought Risk: " + df["Drought_Risk"].astype(str),
        marker=dict(
            size=df["Low_Income_Pct"] * 0.7,
            color=df["Drought_Risk"],
            colorscale="Oranges",
            showscale=True,
            colorbar=dict(title="Drought Risk")
        ),
        name="Drought"
    ))

elif selected_layer == "Wildfire":
    df = filter_df(wildfire_df, "Wildfire_Risk")
    fig.add_trace(go.Scattergeo(
        lon=df["Lon"],
        lat=df["Lat"],
        text=df["County"] + ", " + df["State"] + "<br>Wildfire Risk: " + df["Wildfire_Risk"].astype(str),
        marker=dict(
            size=df["Low_Income_Pct"] * 0.7,
            color=df["Wildfire_Risk"],
            colorscale="Reds",
            showscale=True,
            colorbar=dict(title="Wildfire Risk")
        ),
        name="Wildfire"
    ))

# Layout settings
fig.update_layout(
    geo=dict(
        scope="usa",
        landcolor="rgb(217, 217, 217)",
        subunitcolor="white"
    ),
    margin={"r": 0, "t": 30, "l": 0, "b": 0},
    height=600,
    showlegend=True,
    title=selected_layer
)

# Display chart
st.title("Multi-Hazard Risk Map")
st.plotly_chart(fig, use_container_width=True)
