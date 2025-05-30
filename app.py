import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Load data ---
@st.cache_data
def load_data(url, risk_column=None):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        st.write(f"Columns for {url.split('/')[-1]}:", df.columns.tolist())  # Debug: show columns
        if "CF" in df.columns and "SF" in df.columns:
            df["CF"] = df["CF"].str.title()
            df["SF"] = df["SF"].str.title()
        if "Census tract 2010 ID" in df.columns:
            df["Census tract 2010 ID"] = df["Census tract 2010 ID"].astype(str)
        if "County Name" in df.columns and "State/Territory" in df.columns:
            df["County Name"] = df["County Name"].str.title()
            df["State/Territory"] = df["State/Territory"].str.title()
        lat_col, lon_col = "Latitude", "Longitude"  # Adjust based on debug output
        if lat_col not in df.columns or lon_col not in df.columns:
            st.error(f"Missing '{lat_col}' or '{lon_col}' in {url.split('/')[-1]}")
            return pd.DataFrame()
        return df.dropna(subset=[lat_col, lon_col])
    except Exception as e:
        st.error(f"Load failed for {url.split('/')[-1]}: {str(e)}")
        return pd.DataFrame()

# URLs from your input
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"

census_df = load_data(census_url)
wind_df = load_data(wind_url, "Wind_Risk")
drought_df = load_data(drought_url, "Drought_Risk")
wildfire_df = load_data(wildfire_url, "Wildfire_Risk")

# --- Sidebar ---
st.sidebar.title("Controls")
dataset = st.sidebar.radio("Dataset", ["Census Tracts", "Wind Risk", "Drought Risk", "Wildfire Risk"])
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
show_heatmap = st.sidebar.checkbox("Heatmap Mode", value=False)
min_threshold = st.sidebar.slider("Min Value", 0.0, 100.0, 0.0, 1.0)
search = st.sidebar.text_input("Filter (County/State)").strip().lower()

# --- Filter Logic ---
def filter_data(df, metric, dataset):
    if df.empty or metric not in df.columns:
        st.warning(f"Metric '{metric}' not found")
        return pd.DataFrame()
    filtered_df = df[df[metric].notna()]
    if metric != "Identified as disadvantaged":
        filtered_df = filtered_df[filtered_df[metric] >= min_threshold]
    if search:
        if dataset == "Census Tracts":
            filtered_df = filtered_df[filtered_df["County Name"].str.lower().str.contains(search, na=False)]
        else:
            filtered_df = filtered_df[filtered_df["CF"].str.lower().str.contains(search, na=False)]
    return filtered_df

# --- Check data and filter ---
if dataset == "Census Tracts":
    df, lat_col, lon_col, loc_col = census_df, "Latitude", "Longitude", "County Name"
    size_col = "Total population"
elif dataset == "Wind Risk":
    df, lat_col, lon_col, loc_col = wind_df, "Latitude", "Longitude", "CF"
    size_col = "MEAN_low_income_percentage"
elif dataset == "Drought Risk":
    df, lat_col, lon_col, loc_col = drought_df, "Latitude", "Longitude", "CF"
    size_col = "MEAN_low_income_percentage"
else:
    df, lat_col, lon_col, loc_col = wildfire_df, "Latitude", "Longitude", "CF"
    size_col = "MEAN_low_income_percentage"

if df.empty:
    st.warning("No data loaded")
else:
    data = filter_data(df, metric, dataset)

    # --- Plot Setup ---
    fig = go.Figure()

    # --- Map ---
    if data.empty:
        st.warning("No data for filters")
    else:
        if len(data) > 5000:
            data = data.sample(5000, random_state=42)
        
        if show_heatmap:
            fig.add_trace(go.Scattergeo(
                lon=data[lon_col],
                lat=data[lat_col],
                text=data[loc_col] + ", " + data["State/Territory" if dataset == "Census Tracts" else "SF"] + "<br>" + metric + ": " + data[metric].astype(str),
                marker=dict(
                    size=10,
                    color=data[metric],
                    colorscale="Viridis",
                    opacity=0.3,
                    showscale=True,
                    colorbar=dict(title=metric)
                )
            ))
        else:
            fig.add_trace(go.Scattergeo(
                lon=data[lon_col],
                lat=data[lat_col],
                text=data[loc_col] + ", " + data["State/Territory" if dataset == "Census Tracts" else "SF"] + "<br>" + metric + ": " + data[metric].astype(str),
                marker=dict(
                    size=data[size_col] / (1000 if dataset == "Census Tracts" else 2),
                    color=data[metric],
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
            margin={"r":0, "t":30, "l":0, "b":0},
            height=600,
            showlegend=False
        )

    # --- Render Map ---
    st.title(f"{metric} Dashboard")
    st.plotly_chart(fig, use_container_width=True)

    # --- Table ---
    if not data.empty:
        top = data.sort_values(by=metric, ascending=False).head(10)
        st.subheader(f"Top 10 {metric}")
        display_cols = [loc_col, "State/Territory" if dataset == "Census Tracts" else "SF", metric, size_col]
        st.dataframe(top[display_cols].style.format({
            metric: "{:.2f}" if metric != "Identified as disadvantaged" else "{}",
            size_col: "{:.0f}" if dataset == "Census Tracts" else "{:.2f}"
        }))

    # --- Bar Chart ---
    if not data.empty:
        top = data.sort_values(by=metric, ascending=False).head(10)
        bar_fig = go.Figure()
        bar_fig.add_trace(go.Bar(
            x=top[loc_col] + ", " + top["State/Territory" if dataset == "Census Tracts" else "SF"],
            y=top[metric],
            marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                          "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
        ))
        bar_fig.update_layout(
            xaxis_title="Location",
            yaxis_title=metric,
            yaxis=dict(range=[0, 100.0 if metric != "Identified as disadvantaged" else 1.1]),
            margin={"r":0, "t":30, "l":0, "b":0},
            height=400
        )
        st.plotly_chart(bar_fig, use_container_width=True)
