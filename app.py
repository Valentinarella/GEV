import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

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
        "State/Territory": "State"
    })
    df["County"] = df["County"].str.title()
    df["State"] = df["State"].str.title()
    return df

# --- Load datasets ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census()

# --- Sidebar view toggle ---
view = st.sidebar.radio("Choose View", ["Hazard Map", "Community Data"])

# --- View: Hazard Map ---
if view == "Hazard Map":
    hazard = st.sidebar.selectbox("Hazard Type", ["Wind Risk", "Drought Risk", "Wildfire Risk"])
    min_value = st.sidebar.slider("Minimum Risk", 0.0, 50.0, 5.0, 1.0)

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
            size=data["Low_Income_Pct"] * 0.7,
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

# --- View: Community Data (no map) ---
else:
    st.title("Community Data Viewer")
    metric = st.sidebar.selectbox("Select Community Metric", [
        "Identified as disadvantaged",
        "Energy burden",
        "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years",
        "Share of properties at risk of fire in 30 years",
        "Total population"
    ])

    show_top_n = st.sidebar.slider("Top N Communities", 5, 50, 10)

    community = census_df[census_df[metric].notna()].copy()
    if metric == "Identified as disadvantaged":
        community = community[community[metric] == True]

    st.subheader(f"Top {show_top_n} Communities by '{metric}'")

    top = community.sort_values(by=metric, ascending=False).head(show_top_n) if metric != "Identified as disadvantaged" else community.head(show_top_n)
    st.dataframe(top[["County", "State", metric, "Total population"]] if "Total population" in top.columns else top[["County", "State", metric]])

    # --- Bar chart ---
    if metric != "Identified as disadvantaged":
        st.subheader("Bar Chart")
        fig = px.bar(
            top,
            x="County",
            y=metric,
            color="State",
            title=f"{metric} by County",
            labels={"County": "County"},
        )
        st.plotly_chart(fig, use_container_width=True)

    # --- Storytelling section ---
    st.markdown("### 📖 Story Snapshot")
    top_states = top["State"].value_counts().head(3).index.tolist()
    st.markdown(f"""
Communities with the highest **{metric}** are concentrated in: **{', '.join(top_states)}**.

These areas may be disproportionately affected by social, health, or environmental burdens.  
Use this data to understand where need is greatest and where support may have the most impact.
""")
