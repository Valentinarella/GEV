import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Page Setup ---
st.set_page_config(layout="wide")

# --- Load and Clean Data ---
@st.cache_data
def load_data(url, label):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        # Basic column clean-up
        if "CF" in df.columns:
            df["CF"] = df["CF"].astype(str).str.title()
        if "SF" in df.columns:
            df["SF"] = df["SF"].astype(str).str.title()
        if "County Name" in df.columns:
            df["County Name"] = df["County Name"].astype(str).str.title()
        if "State/Territory" in df.columns:
            df["State/Territory"] = df["State/Territory"].astype(str).str.title()
        if "Census tract 2010 ID" in df.columns:
            df["Census tract 2010 ID"] = df["Census tract 2010 ID"].astype(str)

        # Attempt to auto-detect latitude/longitude
        lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
        lon_col = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)

        if not lat_col or not lon_col:
            st.warning(f"Missing coordinates in {label}")
            return pd.DataFrame()

        df = df.dropna(subset=[lat_col, lon_col])
        df["Latitude"] = df[lat_col]
        df["Longitude"] = df[lon_col]

        st.write(f"✅ {label} loaded:", df.shape)
        return df
    except Exception as e:
        st.error(f"Failed to load {label}: {e}")
        return pd.DataFrame()

# --- Load All Datasets ---
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"

census_df = load_data(census_url, "Census Tracts")
wind_df = load_data(wind_url, "Wind Risk")
drought_df = load_data(drought_url, "Drought Risk")
wildfire_df = load_data(wildfire_url, "Wildfire Risk")

# --- Sidebar Controls ---
st.sidebar.title("Explore Hazards")
dataset = st.sidebar.radio("Select Dataset", ["Census Tracts", "Wind Risk", "Drought Risk", "Wildfire Risk"])

metric_options = {
    "Census Tracts": [
        "Identified as disadvantaged",
        "Share of properties at risk of flood in 30 years",
        "Share of properties at risk of fire in 30 years",
        "Energy burden",
        "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years"
    ],
    "Wind Risk": ["midcent_median_10yr", "MEAN_low_income_percentage"],
    "Drought Risk": ["midcent_median_10yr", "MEAN_low_income_percentage"],
    "Wildfire Risk": ["midcent_median_10yr", "MEAN_low_income_percentage"]
}

metric = st.sidebar.selectbox("Metric", metric_options[dataset])
min_threshold = st.sidebar.slider("Min Value", 0.0, 100.0, 0.0, 1.0)
search = st.sidebar.text_input("Filter by County/Community").strip().lower()
show_heatmap = st.sidebar.checkbox("Show as Heatmap", value=False)

# --- Dataset Selection ---
df_map = {
    "Census Tracts": census_df,
    "Wind Risk": wind_df,
    "Drought Risk": drought_df,
    "Wildfire Risk": wildfire_df
}

df = df_map[dataset]

# --- Data Filtering ---
def filter_df(df):
    if df.empty or metric not in df.columns:
        st.warning("Selected metric not found in data.")
        return pd.DataFrame()

    filtered = df[df[metric].notna()]
    if metric != "Identified as disadvantaged":
        filtered = filtered[filtered[metric] >= min_threshold]

    if search:
        if dataset == "Census Tracts":
            filtered = filtered[filtered["County Name"].str.lower().str.contains(search, na=False)]
        else:
            filtered = filtered[filtered["CF"].str.lower().str.contains(search, na=False)]

    return filtered

filtered_data = filter_df(df)

# --- Plotting ---
if not filtered_data.empty:
    size_col = "Total population" if dataset == "Census Tracts" else "MEAN_low_income_percentage"
    loc_col = "County Name" if dataset == "Census Tracts" else "CF"
    state_col = "State/Territory" if dataset == "Census Tracts" else "SF"

    fig = go.Figure()

    if show_heatmap:
        fig.add_trace(go.Scattergeo(
            lon=filtered_data["Longitude"],
            lat=filtered_data["Latitude"],
            text=filtered_data[loc_col] + ", " + filtered_data[state_col] + "<br>" + metric + ": " + filtered_data[metric].astype(str),
            marker=dict(
                size=10,
                color=filtered_data[metric],
                colorscale="Viridis",
                opacity=0.3,
                showscale=True,
                colorbar=dict(title=metric)
            )
        ))
    else:
        fig.add_trace(go.Scattergeo(
            lon=filtered_data["Longitude"],
            lat=filtered_data["Latitude"],
            text=filtered_data[loc_col] + ", " + filtered_data[state_col] + "<br>" + metric + ": " + filtered_data[metric].astype(str),
            marker=dict(
                size=filtered_data[size_col] / (1000 if dataset == "Census Tracts" else 2),
                color=filtered_data[metric],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title=metric)
            )
        ))

    fig.update_layout(
        geo=dict(scope="usa", landcolor="lightgray", subunitcolor="white", projection_scale=1),
        margin={"r":0,"t":30,"l":0,"b":0},
        height=600,
        showlegend=False
    )

    st.title(f"{metric} - {dataset}")
    st.plotly_chart(fig, use_container_width=True)

    # --- Top 10 Table ---
    top10 = filtered_data.sort_values(by=metric, ascending=False).head(10)
    st.subheader("Top 10 Locations")
    st.dataframe(top10[[loc_col, state_col, metric, size_col]])

else:
    st.warning("No data to display. Adjust your filters or try a different metric.")
