import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Load data ---
@st.cache_data
def load_data(url):
    try:
        df = pd.read_csv(url)
        df["Census tract 2010 ID"] = df["Census tract 2010 ID"].astype(str)
        df["County Name"] = df["County Name"].str.title()
        df["State/Territory"] = df["State/Territory"].str.title()
        return df.dropna(subset=["Latitude", "Longitude"])
    except:
        return pd.DataFrame()

url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
df = load_data(url)

# --- Sidebar ---
st.sidebar.title("Controls")
metric = st.sidebar.selectbox("Metric", [
    "Identified as disadvantaged", 
    "Share of properties at risk of flood in 30 years", 
    "Share of properties at risk of fire in 30 years", 
    "Energy burden", 
    "PM2.5 in the air", 
    "Current asthma among adults aged greater than or equal to 18 years"
])
show_heatmap = st.sidebar.checkbox("Heatmap Mode", value=False)
min_threshold = st.sidebar.slider("Min Value", 0.0, 100.0, 0.0, 1.0)
search = st.sidebar.text_input("County Filter").strip().lower()

# --- Filter Logic ---
def filter_data(df, metric):
    value_col = metric if metric == "Identified as disadvantaged" else metric
    filtered_df = df[df[value_col].notna()]
    if metric != "Identified as disadvantaged":
        filtered_df = filtered_df[filtered_df[value_col] >= min_threshold]
    if search:
        filtered_df = filtered_df[filtered_df["County Name"].str.lower().str.contains(search, na=False)]
    return filtered_df

data = filter_data(df, metric)

# --- Plot Setup ---
fig = go.Figure()

# --- Map ---
if data.empty:
    st.warning("No data")
else:
    if len(data) > 5000:
        data = data.sample(5000, random_state=42)
    
    if show_heatmap:
        fig.add_trace(go.Scattergeo(
            lon=data["Longitude"],
            lat=data["Latitude"],
            text=data["Census tract 2010 ID"] + "<br>" + data["County Name"] + ", " + data["State/Territory"] + "<br>" + metric + ": " + data[metric].astype(str),
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
            lon=data["Longitude"],
            lat=data["Latitude"],
            text=data["Census tract 2010 ID"] + "<br>" + data["County Name"] + ", " + data["State/Territory"] + "<br>" + metric + ": " + data[metric].astype(str),
            marker=dict(
                size=data["Total population"] / 1000,  # Scale by population
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
    display_cols = ["Census tract 2010 ID", "County Name", "State/Territory", metric, 
                    "Total population", "Percent of individuals below 200% Federal Poverty Line"]
    st.dataframe(top[display_cols].style.format({
        metric: "{:.2f}" if metric != "Identified as disadvantaged" else "{}",
        "Total population": "{:.0f}",
        "Percent of individuals below 200% Federal Poverty Line": "{:.2%}"
    }))

# --- Bar Chart ---
if not data.empty:
    top = data.sort_values(by=metric, ascending=False).head(10)
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=top["Census tract 2010 ID"] + ", " + top["County Name"] + ", " + top["State/Territory"],
        y=top[metric],
        marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                      "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    ))
    bar_fig.update_layout(
        xaxis_title="Census Tract, County, State",
        yaxis_title=metric,
        yaxis=dict(range=[0, 100.0 if metric != "Identified as disadvantaged" else 1.1]),
        margin={"r":0, "t":30, "l":0, "b":0},
        height=400
    )
    st.plotly_chart(bar_fig, use_container_width=True)
