import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# Set page config
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"

# --- Load and clean data ---
@st.cache_data
def load_data(url, risk_column):
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
        required_cols = ["County", "State", "Lat", "Lon", risk_column, "Low_Income_Pct"]
        if not all(col in df.columns for col in required_cols):
            return pd.DataFrame()
        df = df.dropna(subset=["Lat", "Lon", risk_column])
        df["County"] = df["County"].str.title()
        return df
    except:
        return pd.DataFrame()

drought_df = load_data(drought_url, "Drought_Risk")
wind_df = load_data(wind_url, "Wind_Risk")
wildfire_df = load_data(wildfire_url, "Wildfire_Risk")

# --- Sidebar ---
st.sidebar.title("Controls")
hazard = st.sidebar.radio("Hazard", ["Wind Risk", "Drought Risk", "Wildfire Risk"])
show_heatmap = st.sidebar.checkbox("Heatmap Mode", value=False)
min_threshold = st.sidebar.slider("Min Risk", 0.0, 50.0, 5.0, 1.0)
search = st.sidebar.text_input("County Filter").strip().lower()

# --- Filter Logic ---
def filter_data(df, risk_col):
    filtered_df = df[df[risk_col] >= min_threshold]
    if search:
        filtered_df = filtered_df[filtered_df["County"].str.lower().str.contains(search, na=False)]
    return filtered_df

# --- Plot Setup ---
fig = go.Figure()

if hazard == "Wind Risk":
    data = filter_data(wind_df, "Wind_Risk")
    fig_title = "Wind Risk"
    color = "Blues"
    risk_col = "Wind_Risk"
elif hazard == "Drought Risk":
    data = filter_data(drought_df, "Drought_Risk")
    fig_title = "Drought Risk"
    color = "Oranges"
    risk_col = "Drought_Risk"
else:
    data = filter_data(wildfire_df, "Wildfire_Risk")
    fig_title = "Wildfire Risk"
    color = "Reds"
    risk_col = "Wildfire_Risk"

# --- Map ---
if data.empty:
    st.warning("No data")
else:
    if len(data) > 5000:
        data = data.sample(5000, random_state=42)
    
    if show_heatmap:
        fig.add_trace(go.Scattergeo(
            lon=data["Lon"],
            lat=data["Lat"],
            text=data["County"] + ", " + data["State"] + "<br>Risk: " + data[risk_col].astype(str),
            marker=dict(
                size=10,
                color=data[risk_col],
                colorscale=color,
                opacity=0.3,
                showscale=True,
                colorbar=dict(title=fig_title)
            )
        ))
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
                colorbar=dict(title=fig_title)
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
st.title(f"{fig_title} Dashboard")
st.plotly_chart(fig, use_container_width=True)

# --- Table ---
if not data.empty:
    top = data.sort_values(by=risk_col, ascending=False).head(10)
    st.subheader(f"Top 10 {fig_title}")
    st.dataframe(top[["County", "State", risk_col, "Low_Income_Pct"]].style.format({
        risk_col: "{:.1f}",
        "Low_Income_Pct": "{:.2%}"
    }))

# --- Bar Chart ---
if not data.empty:
    top = data.sort_values(by=risk_col, ascending=False).head(10)
    bar_fig = go.Figure()
    bar_fig.add_trace(go.Bar(
        x=top["County"] + ", " + top["State"],
        y=top[risk_col],
        marker_color=["#1f77b4", "#ff7f0e", "#2ca02c", "#d62728", "#9467bd",
                      "#8c564b", "#e377c2", "#7f7f7f", "#bcbd22", "#17becf"]
    ))
    bar_fig.update_layout(
        xaxis_title="County, State",
        yaxis_title=fig_title,
        yaxis=dict(range=[0, max(50.0, top[risk_col].max() * 1.1)]),
        margin={"r":0, "t":30, "l":0, "b":0},
        height=400
    )
    st.plotly_chart(bar_fig, use_container_width=True)
