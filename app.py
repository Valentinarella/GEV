import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page setup ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Data URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"

# --- Load hazard data ---
@st.cache_data
def load_hazard_data(url, risk_column):
    try:
        df = pd.read_csv(url)
        df = df.rename(columns={
            "CF": "County",
            "SF": "State",
            "MEAN_low_income_percentage": "Low_Income_Pct",
            "Latitude": "Lat",
            "Longitude": "Lon",
            "midcent_median_10yr": risk_column
        })
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        required = ["County", "State", "Lat", "Lon", risk_column]
        return df.dropna(subset=required)
    except Exception as e:
        st.error(f"Failed to load hazard data: {e}")
        return pd.DataFrame()

# --- Load census data ---
@st.cache_data
def load_census_data():
    try:
        df = pd.read_csv(census_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={
            "County Name": "County",
            "State/Territory": "State"
        })
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df
    except Exception as e:
        st.error(f"Failed to load census data: {e}")
        return pd.DataFrame()

# --- Load all datasets ---
drought_df = load_hazard_data(drought_url, "Drought_Risk")
wind_df = load_hazard_data(wind_url, "Wind_Risk")
wildfire_df = load_hazard_data(wildfire_url, "Wildfire_Risk")
census_df = load_census_data()

# --- Sidebar ---
st.sidebar.title("Risk Map Controls")
hazard = st.sidebar.radio("Select Hazard Type", ["Wind Risk", "Drought Risk", "Wildfire Risk"])
show_heatmap = st.sidebar.checkbox("Show Heatmap", value=False)
show_communities = st.sidebar.checkbox("Show Disadvantaged Communities", value=True)
min_threshold = st.sidebar.slider("Minimum Risk Value", 0.0, 50.0, 5.0, 1.0)
search = st.sidebar.text_input("Filter by County (optional)").strip().lower()

# --- Select hazard data ---
if hazard == "Wind Risk":
    data = wind_df
    risk_col = "Wind_Risk"
    color = "Blues"
elif hazard == "Drought Risk":
    data = drought_df
    risk_col = "Drought_Risk"
    color = "Oranges"
else:
    data = wildfire_df
    risk_col = "Wildfire_Risk"
    color = "Reds"

# --- Filter hazard data ---
data = data[data[risk_col] >= min_threshold]
if search:
    data = data[data["County"].str.lower().str.contains(search)]

# --- Limit size for performance ---
if len(data) > 5000:
    data = data.sample(5000, random_state=42)

# --- Plotting ---
fig = go.Figure()

if data.empty:
    st.warning("No hazard data matches the selected filters.")
else:
    if show_heatmap:
        fig.add_trace(go.Densitymapbox(
            lat=data["Lat"],
            lon=data["Lon"],
            z=data[risk_col],
            radius=20,
            colorscale=color,
            showscale=True,
            name=f"{hazard} Heatmap"
        ))
        fig.update_layout(
            mapbox=dict(
                accesstoken="your_mapbox_access_token_here",  # Replace with your actual token
                style="carto-positron",
                center={"lat": 37.0902, "lon": -95.7129},
                zoom=3
            ),
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            height=600
        )
    else:
        fig.add_trace(go.Scattergeo(
            lon=data["Lon"],
            lat=data["Lat"],
            text=data["County"] + ", " + data["State"] + "<br>Risk: " + data[risk_col].astype(str),
            marker=dict(
                size=data["Low_Income_Pct"] * 0.7,
                color=data[risk_col],
                colorscale=color,
                showscale=True,
                colorbar=dict(title=risk_col)
            ),
            name=hazard
        ))
        fig.update_layout(
            geo=dict(
                scope="usa",
                landcolor="lightgray",
                subunitcolor="white",
                center={"lat": 37.0902, "lon": -95.7129},
                projection_scale=1
            ),
            margin={"r": 0, "t": 30, "l": 0, "b": 0},
            height=600,
            showlegend=False
        )

# --- Add disadvantaged communities ---
if show_communities and not census_df.empty:
    disadvantaged = census_df[census_df["Identified as disadvantaged"] == True]
    if "Latitude" in disadvantaged.columns and "Longitude" in disadvantaged.columns:
        disadvantaged = disadvantaged.rename(columns={"Latitude": "Lat", "Longitude": "Lon"})
    elif "Lat" not in disadvantaged.columns or "Lon" not in disadvantaged.columns:
        st.warning("Community data does not have latitude/longitude. Map overlay skipped.")
    else:
        fig.add_trace(go.Scattergeo(
            lon=disadvantaged["Lon"],
            lat=disadvantaged["Lat"],
            text=disadvantaged["County"] + ", " + disadvantaged["State"] + "<br>Disadvantaged Tract",
            marker=dict(
                size=6,
                color="black",
                symbol="x",
                opacity=0.6
            ),
            name="Disadvantaged Communities"
        ))

# --- Show Map ---
st.title("Multi-Hazard Risk Dashboard")
st.plotly_chart(fig, use_container_width=True)

# --- Top 10 table ---
if not data.empty:
    st.subheader(f"Top 10 Highest {hazard} Counties")
    top = data.sort_values(by=risk_col, ascending=False).head(10)
    st.dataframe(top[["County", "State", risk_col, "Low_Income_Pct"]])

# --- Storytelling ---
if not data.empty:
    top_states = data["State"].value_counts().head(3).index.tolist()
    top_counties = data.sort_values(by=risk_col, ascending=False).head(3)[["County", "State"]].agg(", ".join, axis=1).tolist()

    st.markdown("### 📖 Story Snapshot")
    st.markdown(f"""
**You're viewing {hazard.lower()} risk across U.S. counties.**

Highest levels of **{hazard.lower()}** are concentrated in: **{', '.join(top_states)}**.

Top impacted counties include: **{', '.join(top_counties)}**.

Many of these places also show high rates of **low-income households**, suggesting that climate vulnerability and social vulnerability overlap in critical ways.

Use the map and data to explore where these challenges intersect.
""")
