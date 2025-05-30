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
            st.error(f"Missing required columns in data from {url}")
            return pd.DataFrame()
        df = df.dropna(subset=["Lat", "Lon", risk_column])
        df["County"] = df["County"].str.title()
        return df
    except Exception as e:
        st.error(f"Failed to load data from {url}: {str(e)}")
        return pd.DataFrame()

drought_df = load_data(drought_url, "Drought_Risk")
wind_df = load_data(wind_url, "Wind_Risk")
wildfire_df = load_data(wildfire_url, "Wildfire_Risk")

# --- Sidebar ---
st.sidebar.title("Risk Map Controls")
hazard = st.sidebar.radio("Select Hazard Type", ["Wind Risk", "Drought Risk", "Wildfire Risk"])
min_threshold = st.sidebar.slider("Minimum Risk Value", 0.0, 50.0, 5.0, 1.0)
search = st.sidebar.text_input("Filter by County (optional)").strip().lower()

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

# --- Title and Introduction ---
st.title("🌪️ Multi-Hazard Risk Dashboard: Uncovering Community Vulnerability 🌵🔥")
st.markdown("""
**Welcome to the Multi-Hazard Risk Dashboard!**  
Extreme weather events—windstorms, droughts, and wildfires—threaten communities across the U.S., but not all areas are equally prepared. This dashboard maps risk levels and highlights how low-income communities may face greater challenges in recovery.  
- **Explore**: Select a hazard (wind, drought, or wildfire) and adjust the risk threshold.  
- **Discover**: See where risks are highest and how they overlap with vulnerable populations.  
- **Why It Matters**: Understanding these patterns helps policymakers, planners, and residents prioritize resources and build resilience.  
Let’s dive into the story of risk and resilience!
""")

# --- Guide for Visualization ---
st.markdown(f"""
### Exploring {fig_title}
The map below tells the story of {fig_title.lower()} across the U.S. Each point represents a county, with:  
- **Color** showing the intensity of {fig_title.lower()} (darker shades = higher risk).  
- **Size** reflecting the percentage of low-income residents—larger circles highlight areas where vulnerability may be greater.  
Filter by county or adjust the minimum risk value to uncover the story in your area.
""")

# Check if data is empty
if data.empty:
    st.warning("No data matches the selected filters.")
else:
    # Limit data points for performance
    if len(data) > 5000:
        data = data.sample(5000, random_state=42)
    
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
        ),
        name=fig_title
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
st.plotly_chart(fig, use_container_width=True)

# --- Key Insights ---
if not data.empty:
    max_risk = data[risk_col].max()
    max_risk_county = data.loc[data[risk_col] == max_risk, "County"].iloc[0]
    max_risk_state = data.loc[data[risk_col] == max_risk, "State"].iloc[0]
    high_vuln = data[data["Low_Income_Pct"] > 0.5]  # Counties with >50% low-income
    vuln_count = len(high_vuln)
    st.markdown(f"""
    ### Key Insights from the {fig_title} Story
    - **Highest Risk**: {max_risk_county}, {max_risk_state} faces the greatest {fig_title.lower()}, with a risk score of {max_risk:.1f}.  
    - **Vulnerability Alert**: {vuln_count} counties in this view have over 50% low-income residents, potentially amplifying the impact of {fig_title.lower()}.  
    - **What’s at Stake?** High-risk areas with large low-income populations may struggle with preparation, evacuation, or recovery. Explore the map and table below to see where action is needed most!
    """)
else:
    st.markdown("""
    ### No Story to Tell Yet
    No counties match your filters. Try lowering the minimum risk value or clearing the county search to uncover the hidden stories of risk and resilience!
    """)

# --- Table with Context ---
if not data.empty:
    top = data.sort_values(by=risk_col, ascending=False).head(10)
    st.markdown(f"""
    ### The Top 10 Hotspots: A Closer Look
    Below are the 10 counties facing the highest {fig_title.lower()}. Notice how risk intertwines with low-income percentages—counties with higher low-income populations may need extra support to weather the storm (or fire, or drought). Use this table to pinpoint where urgent action can make a difference!
    """)
    st.dataframe(top[["County", "State", risk_col, "Low_Income_Pct"]].style.format({
        risk_col: "{:.1f}",
        "Low_Income_Pct": "{:.2%}"
    }))

# --- Call to Action ---
st.markdown(f"""
### What’s Your Next Step?
The story of {hazard.lower()} is unfolding across the U.S. High-risk areas, especially those with vulnerable populations, need targeted plans—better infrastructure, emergency funding, or community programs.  
- **Explore More**: Adjust the filters in the sidebar to dig deeper.  
- **Act**: Share these insights with local leaders, planners, or friends to spark change.  
Together, we can write a new chapter of resilience!
""")
