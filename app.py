import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Data URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"

# --- Load functions ---
@st.cache_data
def load_hazard(url, risk_column):
    df = pd.read_csv(url)
    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "Latitude": "Lat",
        "Longitude": "Lon",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": risk_column
    })
    df["County"] = df["County"].str.title()
    df["State"] = df["State"].str.title()
    return df.dropna(subset=["Lat", "Lon", risk_column])

@st.cache_data
def load_census():
    df = pd.read_csv(census_url)
    df.columns = df.columns.str.strip()
    df = df.rename(columns={
        "County Name": "County",
        "State/Territory": "State",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })
    df["County"] = df["County"].str.title()
    df["State"] = df["State"].str.title()
    return df.dropna(subset=["Lat", "Lon"])

# --- Load datasets ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census()

# --- Sidebar: View toggle ---
view = st.sidebar.radio("Choose View", ["Hazard Map", "Community Map"])

# --- Hazard View ---
if view == "Hazard Map":
    hazard = st.sidebar.selectbox("Hazard Type", ["Wind Risk", "Drought Risk", "Wildfire Risk"])
    min_value = st.sidebar.slider("Minimum Risk", 0.0, 50.0, 5.0, 1.0)
    color_by = "Low_Income_Pct"

    if hazard == "Wind Risk":
        df = wind_df
        risk_col = "Wind_Risk"
        colorscale = "Blues"
    elif hazard == "Drought Risk":
        df = drought_df
        risk_col = "Drought_Risk"
        colorscale = "Oranges"
    else:
        df = wildfire_df
        risk_col = "Wildfire_Risk"
        colorscale = "Reds"

    data = df[df[risk_col] >= min_value]

    fig = go.Figure(go.Scattergeo(
        lon=data["Lon"],
        lat=data["Lat"],
        text=data["County"] + ", " + data["State"] + "<br>Risk: " + data[risk_col].astype(str),
        marker=dict(
            size=data[color_by] * 0.7,
            color=data[risk_col],
            colorscale=colorscale,
            showscale=True,
            colorbar=dict(title=risk_col)
        )
    ))

    fig.update_layout(
        geo=dict(
            scope="usa",
            landcolor="lightgray",
            subunitcolor="white",
            projection_scale=1,
            center={"lat": 37.0902, "lon": -95.7129}
        ),
        height=600,
        margin={"r": 0, "t": 30, "l": 0, "b": 0}
    )

    st.title(f"{hazard} Across U.S. Counties")
    st.plotly_chart(fig, use_container_width=True)

    if not data.empty:
        st.subheader("Top 10 Counties by Risk")
        st.dataframe(data.sort_values(by=risk_col, ascending=False).head(10)[["County", "State", risk_col, "Low_Income_Pct"]])

# --- Community View ---
else:
    metric = st.sidebar.selectbox("Community Metric", [
        "Identified as disadvantaged",
        "Energy burden",
        "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years"
    ])

    community = census_df[census_df[metric].notna()]
    if metric == "Identified as disadvantaged":
        community = community[community[metric] == True]
        color = "black"
    else:
        color = community[metric]

    fig = go.Figure(go.Scattergeo(
        lon=community["Lon"],
        lat=community["Lat"],
        text=community["County"] + ", " + community["State"] + "<br>" + metric + ": " + community[metric].astype(str),
        marker=dict(
            size=6 if metric == "Identified as disadvantaged" else 8,
            color=color,
            colorscale="Viridis" if metric != "Identified as disadvantaged" else None,
            showscale=metric != "Identified as disadvantaged",
            colorbar=dict(title=metric) if metric != "Identified as disadvantaged" else None
        )
    ))

    fig.update_layout(
        geo=dict(
            scope="usa",
            landcolor="lightgray",
            subunitcolor="white",
            projection_scale=1,
            center={"lat": 37.0902, "lon": -95.7129}
        ),
        height=600,
        margin={"r": 0, "t": 30, "l": 0, "b": 0}
    )

    st.title("Community-Level Census Map")
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top Communities")
    top = community.sort_values(by=metric, ascending=False).head(10) if metric != "Identified as disadvantaged" else community.head(10)
    st.dataframe(top[["County", "State", metric, "Total population"]] if "Total population" in top.columns else top[["County", "State", metric]])
