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

        # Normalize key fields
        for col in ["CF", "SF", "County Name", "State/Territory"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.title()

        if "Census tract 2010 ID" in df.columns:
            df["Census tract 2010 ID"] = df["Census tract 2010 ID"].astype(str)

        # Detect Latitude/Longitude
        lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
        lon_col = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)

        if not lat_col or not lon_col:
            st.warning(f"⚠️ Missing coordinates in {label}. Skipping.")
            return pd.DataFrame()

        df = df.dropna(subset=[lat_col, lon_col])
        df["Latitude"] = df[lat_col]
        df["Longitude"] = df[lon_col]

        st.write(f"✅ Loaded {label}: {df.shape[0]} rows")
        return df

    except Exception as e:
        st.error(f"Failed to load {label}: {e}")
        return pd.DataFrame()

# --- URLs for All Datasets ---
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"

# --- Load Datasets ---
census_df = load_data(census_url, "Census Tracts")
wind_df = load_data(wind_url, "Wind Risk")
drought_df = load_data(drought_url, "Drought Risk")
wildfire_df = load_data(wildfire_url, "Wildfire Risk")

# --- Sidebar Controls ---
st.sidebar.title("Explore Environmental Risk")
dataset = st.sidebar.radio("Choose a Dataset", ["Census Tracts", "Wind Risk", "Drought Risk", "Wildfire Risk"])

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
min_threshold = st.sidebar.slider("Min Value (Filter)", 0.0, 100.0, 0.0, 1.0)
search = st.sidebar.text_input("Search (County or Community)").strip().lower()
heatmap = st.sidebar.checkbox("Show as Heatmap", value=False)

# --- Dataset Map ---
df_map = {
    "Census Tracts": census_df,
    "Wind Risk": wind_df,
    "Drought Risk": drought_df,
    "Wildfire Risk": wildfire_df
}
df = df_map[dataset]

# --- Filtering ---
def filter_df(df):
    if df.empty or metric not in df.columns:
        st.warning("❌ Metric not found in data.")
        return pd.DataFrame()

    result = df[df[metric].notna()]
    if metric != "Identified as disadvantaged":
        result = result[result[metric] >= min_threshold]

    if search:
        if dataset == "Census Tracts":
            result = result[result["County Name"].str.lower().str.contains(search, na=False)]
        else:
            result = result[result["CF"].str.lower().str.contains(search, na=False)]

    return result

filtered = filter_df(df)

# --- Plotting ---
if not filtered.empty:
    size_col = "Total population" if dataset == "Census Tracts" else "MEAN_low_income_percentage"
    loc_col = "County Name" if dataset == "Census Tracts" else "CF"
    state_col = "State/Territory" if dataset == "Census Tracts" else "SF"

    fig = go.Figure()

    if heatmap:
        fig.add_trace(go.Scattergeo(
            lon=filtered["Longitude"],
            lat=filtered["Latitude"],
            text=filtered[loc_col] + ", " + filtered[state_col] + "<br>" + metric + ": " + filtered[metric].astype(str),
            marker=dict(
                size=10,
                color=filtered[metric],
                colorscale="Viridis",
                opacity=0.3,
                showscale=True,
                colorbar=dict(title=metric)
            )
        ))
    else:
        fig.add_trace(go.Scattergeo(
            lon=filtered["Longitude"],
            lat=filtered["Latitude"],
            text=filtered[loc_col] + ", " + filtered[state_col] + "<br>" + metric + ": " + filtered[metric].astype(str),
            marker=dict(
                size=filtered[size_col] / (1000 if dataset == "Census Tracts" else 2),
                color=filtered[metric],
                colorscale="Viridis",
                showscale=True,
                colorbar=dict(title=metric)
            )
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

    st.title(f"{metric} – {dataset}")
    st.plotly_chart(fig, use_container_width=True)

    # --- Top 10 Table ---
    top10 = filtered.sort_values(by=metric, ascending=False).head(10)
    st.subheader("Top 10 Locations")
    st.dataframe(top10[[loc_col, state_col, metric, size_col]].style.format({
        metric: "{:.2f}" if metric != "Identified as disadvantaged" else "{}",
        size_col: "{:.0f}" if dataset == "Census Tracts" else "{:.2f}"
    }))

    # --- Bar Chart ---
    st.subheader("Top 10 - Bar Chart")
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=top10[loc_col] + ", " + top10[state_col],
        y=top10[metric],
        marker_color='indianred'
    ))
    bar_fig.update_layout(
        xaxis_title="Location",
        yaxis_title=metric,
        yaxis=dict(range=[0, 100.0 if metric != "Identified as disadvantaged" else 1.1]),
        height=400
    )
    st.plotly_chart(bar_fig, use_container_width=True)

    # --- Optional Summary Section ---
    st.markdown("### Story Summary")
    st.markdown(f"""
    You're exploring **{metric}** under the **{dataset}** dataset.
    {len(filtered)} locations met your filters.
    
    The top areas with the highest values are mostly from:  
    **{', '.join(top10[state_col].unique()[:3])}**.
    
    This suggests that environmental or socioeconomic challenges here may require more attention.
    """)
else:
    st.warning("No data found. Try relaxing your filters or changing the metric.")
