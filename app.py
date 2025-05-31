import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D"
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D"
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D"
health_url = "https://undivideprojectdata.blob.core.windows.net/gev/health.csv?sp=r&st=2025-05-31T00:13:59Z&se=2090-05-31T08:13:59Z&spr=https&sv=2024-11-04&sr=b&sig=8epnZK%2FXbnblTCiYlmtuYHgBy43yxCHTtS7FqLu134k%3D"

# --- Loaders ---
@st.cache_data
def load_hazard(url, risk_col):
    try:
        df = pd.read_csv(url, usecols=["CF", "SF", "Latitude", "Longitude", "MEAN_low_income_percentage", "midcent_median_10yr"])
        df = df.rename(columns={"CF": "County", "SF": "State", "Latitude": "Lat", "Longitude": "Lon", 
                                "MEAN_low_income_percentage": "Low_Income_Pct", "midcent_median_10yr": risk_col})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df.dropna(subset=["Lat", "Lon", risk_col])
    except Exception as e:
        st.error(f"Error loading data from {url}: {e}")
        return pd.DataFrame()

@st.cache_data
def load_census():
    try:
        df = pd.read_csv(census_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"County Name": "County", "State/Territory": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df
    except Exception as e:
        st.error(f"Error loading census data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_health_data():
    try:
        df = pd.read_csv(health_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"CF": "County", "SF": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df.dropna(subset=["MEAN_low_income_percentage"])
    except Exception as e:
        st.error(f"Error loading health data: {e}")
        return pd.DataFrame()

@st.cache_data
def filter_hazard_data(df, risk_col, threshold):
    return df[df[risk_col] >= threshold]

# --- Load data ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census()
health_df = load_health_data()

# --- UI Setup ---
st.title("📊 Multi-Hazard + Community Vulnerability Dashboard")
st.markdown("""
Welcome to this dashboard for identifying **climate risk** and **community vulnerability**.

It brings together:
- Hazard exposure (wind, drought, wildfire)
- Demographic and economic burdens
- Health disparities

Use this tool to **inform action, investment, and policy**.

---
""")

# --- View Selector ---
st.sidebar.title("Navigation")
view = st.sidebar.selectbox("Choose Section", 
                            ["Hazard Map", "Community Indicators", "Health & Income"],
                            help="Pick a view: Hazard Map for climate risks, Community Indicators for demographics, or Health & Income for disparities.")

# --- Hazard Map View ---
if view == "Hazard Map":
    hazards = st.sidebar.multiselect("Hazards", ["Wind Risk", "Drought Risk", "Wildfire Risk"], default=["Wind Risk"])
    threshold = st.sidebar.slider("Minimum Risk Level", 0.0, 50.0, 5.0, 1.0)

    st.subheader("Hazard Exposure Across Counties")
    st.markdown("**Note**: Risk reflects 10-year median projections. Marker size shows low-income %, color intensity shows risk level. Adjust threshold or select multiple hazards to compare.")
    
    fig = go.Figure()
    colors = {"Wind Risk": "Blues", "Drought Risk": "Oranges", "Wildfire Risk": "Reds"}
    for h in hazards:
        df, risk_col = (wind_df, "Wind_Risk") if h == "Wind Risk" else (drought_df, "Drought_Risk") if h == "Drought Risk" else (wildfire_df, "Wildfire_Risk")
        filtered = filter_hazard_data(df, risk_col, threshold)
        if filtered.empty:
            st.warning(f"No counties meet the risk threshold for {h}.")
            continue
        fig.add_trace(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + h + ": " + filtered[risk_col].astype(str),
            marker=dict(
                size=filtered["Low_Income_Pct"].clip(0, 100) * 0.15 + 5,  # Cap and scale size
                color=filtered[risk_col],
                colorscale=colors[h],
                showscale=True,
                colorbar=dict(title=risk_col, tickmode="auto"),
                sizemode="diameter",
                sizemin=5
            ),
            name=h
        ))
    fig.update_layout(
        geo=dict(scope="usa", projection_scale=1, center={"lat": 37.1, "lon": -95.7}),
        height=600,
        margin=dict(r=0, l=0, t=30, b=0),
        template="plotly_white",
        font=dict(family="Arial", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Top 10 Counties by Risk")
    for h in hazards:
        df, risk_col = (wind_df, "Wind_Risk") if h == "Wind Risk" else (drought_df, "Drought_Risk") if h == "Drought Risk" else (wildfire_df, "Wildfire_Risk")
        filtered = filter_hazard_data(df, risk_col, threshold)
        if not filtered.empty:
            st.dataframe(filtered.sort_values(by=risk_col, ascending=False).head(10)[["County", "State", risk_col, "Low_Income_Pct"]])
            st.download_button(f"Download {h} Table", filtered.to_csv(index=False), f"top_{h}.csv", "text/csv")
        else:
            st.warning(f"No data to display for {h}.")

# --- Community Metrics View ---
elif view == "Community Indicators":
    st.subheader("Community Disadvantage & Demographics")
    st.markdown("**Note**: Explore metrics like energy burden or air quality. Higher values indicate greater vulnerability. Adjust 'Top N' to see more counties.")
    metric = st.sidebar.selectbox("Metric", [
        "Identified as disadvantaged",
        "Energy burden",
        "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years",
        "Share of properties at risk of fire in 30 years",
        "Total population"
    ])
    top_n = st.sidebar.slider("Top N", 5, 50, 10)

    subset = census_df[census_df[metric].notna()]
    if metric == "Identified as disadvantaged":
        subset = subset[subset[metric] == True]
    top = subset.sort_values(by=metric, ascending=False).head(top_n)

    st.dataframe(top[["County", "State", metric, "Total population"]] if "Total population" in top.columns else top[["County", "State", metric]])
    st.download_button(f"Download {metric} Table", top.to_csv(index=False), f"top_{metric}.csv", "text/csv")

    if metric != "Identified as disadvantaged":
        fig = px.bar(top, x="County", y=metric, color="State", title=f"{metric} by County",
                     template="plotly_white")
        fig.update_layout(xaxis_tickangle=-45, font=dict(family="Arial", size=12))
        st.plotly_chart(fig, use_container_width=True)

# --- Health and Income View ---
else:
    st.subheader("Community Health and Income Risks")
    st.markdown("This section highlights where low-income populations face the highest health burdens. Adjust the health metric to compare.")

    hist = px.histogram(
        health_df,
        x="MEAN_low_income_percentage",
        nbins=30,
        title="Low-Income Distribution Across Counties",
        color_discrete_sequence=["#1f77b4"],
        template="plotly_white"
    )
    hist.update_layout(font=dict(family="Arial", size=12))
    st.plotly_chart(hist, use_container_width=True)

    metric = st.selectbox("Health Metric", [
        "Asthma_Rate____", "Diabetes_Rate____", "Heart_Disease_Rate____", "Life_expectancy__years_"
    ])
    top = health_df.sort_values(by=metric, ascending=False).head(10)

    st.subheader(f"Top 10 Counties by {metric.replace('_', ' ').replace('____', '')}")
    bar = px.bar(
        top,
        x="County",
        y=metric,
        color="State",
        title=metric.replace("_", " ").replace("____", ""),
        hover_data=["MEAN_low_income_percentage"],
        template="plotly_white"
    )
    bar.update_layout(font=dict(family="Arial", size=12))
    st.plotly_chart(bar, use_container_width=True)
    st.download_button(f"Download {metric} Table", top.to_csv(index=False), f"top_{metric}.csv", "text/csv")
