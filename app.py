import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Page config ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Metric Name Mapping ---
metric_name_map = {
    # Hazard Metrics
    "Wind_Risk": "Wind Risk Score",
    "Drought_Risk": "Drought Risk Score",
    "Wildfire_Risk": "Wildfire Risk Score",
    "MEAN_low_income_percentage": "Low-Income Population (%)",
    # Community Metrics
    "Identified as disadvantaged": "Disadvantaged Community",
    "Energy burden": "Energy Burden (%)",
    "PM2.5 in the air": "PM2.5 Air Pollution (µg/m³)",
    "Current asthma among adults aged greater than or equal to 18 years": "Adult Asthma Rate (%)",
    "Share of properties at risk of fire in 30 years": "Properties at Fire Risk (%)",
    "Total population": "Total Population",
    # Health Metrics
    "Asthma_Rate____": "Asthma Rate (%)",
    "Diabetes_Rate____": "Diabetes Rate (%)",
    "Heart_Disease_Rate____": "Heart Disease Rate (%)",
    "Life_expectancy__years_": "Life Expectancy (Years)"
}

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
                                "MEAN_low_income_percentage": "MEAN_low_income_percentage", "midcent_median_10yr": risk_col})
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

# --- State Filter ---
st.sidebar.title("Filters")
states = sorted(health_df["State"].unique().tolist())
selected_state = st.sidebar.selectbox("Select State", ["All"] + states, index=0)

# --- Apply State Filter to Datasets ---
def filter_by_state(df, state):
    if state == "All":
        return df
    return df[df["State"] == state]

wind_df_filtered = filter_by_state(wind_df, selected_state)
drought_df_filtered = filter_by_state(drought_df, selected_state)
wildfire_df_filtered = filter_by_state(wildfire_df, selected_state)
census_df_filtered = filter_by_state(census_df, selected_state)
health_df_filtered = filter_by_state(health_df, selected_state)

# --- View Selector ---
st.sidebar.title("Navigation")
view = st.sidebar.selectbox("Choose Section", 
                            ["Hazard Map", "Community Indicators", "Health & Income"],
                            help="Pick a view: Hazard Map for climate risks, Community Indicators for demographics, or Health & Income for disparities.")

# --- Hazard Map View ---
if view == "Hazard Map":
    hazard_options = ["Wind Risk", "Drought Risk", "Wildfire Risk"]
    hazard_raw_map = {"Wind Risk": "Wind_Risk", "Drought Risk": "Drought_Risk", "Wildfire Risk": "Wildfire_Risk"}
    hazards = st.sidebar.multiselect("Hazards", hazard_options, default=["Wind Risk"])
    threshold = st.sidebar.slider("Minimum Risk Level", 0.0, 50.0, 5.0, 1.0)

    st.subheader(f"Hazard Exposure Across Counties ({selected_state if selected_state != 'All' else 'All States'})")
    st.markdown("**Note**: Risk reflects 10-year median projections. Marker size shows low-income %, color intensity shows risk level. Adjust threshold or select multiple hazards to compare.")
    
    fig = go.Figure()
    colors = {"Wind Risk": "Blues", "Drought Risk": "Oranges", "Wildfire Risk": "Reds"}
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if filtered.empty:
            st.warning(f"No counties meet the risk threshold for {metric_name_map[risk_col]} in {selected_state if selected_state != 'All' else 'the selected states'}.")
            continue
        fig.add_trace(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + metric_name_map[risk_col] + ": " + filtered[risk_col].astype(str),
            marker=dict(
                size=filtered["MEAN_low_income_percentage"].clip(0, 100) * 0.15 + 5,
                color=filtered[risk_col],
                colorscale=colors[h],
                showscale=True,
                colorbar=dict(title=metric_name_map[risk_col], tickmode="auto"),
                sizemode="diameter",
                sizemin=5
            ),
            name=metric_name_map[risk_col]
        ))
    fig.update_layout(
        geo=dict(scope="usa", projection_scale=1, center={"lat": 37.1, "lon": -95.7}),
        height=600,
        margin=dict(r=0, l=0, t=30, b=0),
        template="plotly_white",
        font=dict(family="Arial", size=12)
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Top 10 Counties by Risk ({selected_state if selected_state != 'All' else 'All States'})")
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if not filtered.empty:
            display_df = filtered.sort_values(by=risk_col, ascending=False).head(10)[["County", "State", risk_col, "MEAN_low_income_percentage"]]
            display_df.columns = ["County", "State", metric_name_map[risk_col], metric_name_map["MEAN_low_income_percentage"]]
            st.dataframe(display_df)
            st.download_button(f"Download {metric_name_map[risk_col]} Table", filtered.to_csv(index=False), f"top_{h}.csv", "text/csv")
        else:
            st.warning(f"No data to display for {metric_name_map[risk_col]} in {selected_state if selected_state != 'All' else 'the selected states'}.")

# --- Community Metrics View ---
elif view == "Community Indicators":
    st.subheader(f"Community Disadvantage & Demographics ({selected_state if selected_state != 'All' else 'All States'})")
    st.markdown("**Note**: Explore metrics like energy burden or air quality. Higher values indicate greater vulnerability. Adjust 'Top N' to see more counties.")
    raw_metrics = [
        "Identified as disadvantaged", "Energy burden", "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years",
        "Share of properties at risk of fire in 30 years", "Total population"
    ]
    metric_options = [metric_name_map[m] for m in raw_metrics]
    metric = st.sidebar.selectbox("Metric", metric_options)
    raw_metric = [k for k, v in metric_name_map.items() if v == metric][0]
    top_n = st.sidebar.slider("Top N", 5, 50, 10)

    subset = census_df_filtered[census_df_filtered[raw_metric].notna()]
    if raw_metric == "Identified as disadvantaged":
        subset = subset[subset[raw_metric] == True]
    top = subset.sort_values(by=raw_metric, ascending=False).head(top_n)

    if top.empty:
        st.warning(f"No data available for {metric} in {selected_state if selected_state != 'All' else 'the selected states'}.")
    else:
        display_df = top[["County", "State", raw_metric, "Total population"]] if "Total population" in top.columns else top[["County", "State", raw_metric]]
        display_df.columns = [col if col not in metric_name_map else metric_name_map[col] for col in display_df.columns]
        st.dataframe(display_df)
        st.download_button(f"Download {metric} Table", top.to_csv(index=False), f"top_{metric}.csv", "text/csv")

        if raw_metric != "Identified as disadvantaged":
            fig = px.bar(top, x="County", y=raw_metric, color="State", title=f"{metric} by County in {selected_state if selected_state != 'All' else 'All States'}",
                         template="plotly_white")
            fig.update_layout(xaxis_tickangle=-45, font=dict(family="Arial", size=12))
            fig.update_yaxes(title_text=metric)
            st.plotly_chart(fig, use_container_width=True)

# --- Health and Income View ---
else:
    st.subheader(f"Community Health and Income Risks ({selected_state if selected_state != 'All' else 'All States'})")
    st.markdown("This section highlights where low-income populations face the highest health burdens. Adjust the health metric to compare.")

    if health_df_filtered.empty:
        st.warning(f"No health data available for {selected_state if selected_state != 'All' else 'the selected states'}.")
    else:
        hist = px.histogram(
            health_df_filtered,
            x="MEAN_low_income_percentage",
            nbins=30,
            title=f"Low-Income Distribution Across Counties in {selected_state if selected_state != 'All' else 'All States'}",
            color_discrete_sequence=["#1f77b4"],
            template="plotly_white"
        )
        hist.update_layout(font=dict(family="Arial", size=12))
        hist.update_xaxes(title_text=metric_name_map["MEAN_low_income_percentage"])
        st.plotly_chart(hist, use_container_width=True)

        raw_metrics = ["Asthma_Rate____", "Diabetes_Rate____", "Heart_Disease_Rate____", "Life_expectancy__years_"]
        metric_options = [metric_name_map[m] for m in raw_metrics]
        metric = st.selectbox("Health Metric", metric_options)
        raw_metric = [k for k, v in metric_name_map.items() if v == metric][0]
        top = health_df_filtered.sort_values(by=raw_metric, ascending=False).head(10)

        st.subheader(f"Top 10 Counties by {metric} in {selected_state if selected_state != 'All' else 'All States'}")
        if top.empty:
            st.warning(f"No data available for {metric} in {selected_state if selected_state != 'All' else 'the selected states'}.")
        else:
            bar = px.bar(
                top,
                x="County",
                y=raw_metric,
                color="State",
                title=f"Top 10 Counties for {metric} in {selected_state if selected_state != 'All' else 'All States'}",
                hover_data=["MEAN_low_income_percentage"],
                template="plotly_white"
            )
            bar.update_layout(font=dict(family="Arial", size=12))
            bar.update_yaxes(title_text=metric)
            bar.update_traces(hovertemplate="County: %{x}<br>" + metric + ": %{y}<br>" + metric_name_map["MEAN_low_income_percentage"] + ": %{customdata}")
            st.plotly_chart(bar, use_container_width=True)
            display_df = top[["County", "State", raw_metric, "MEAN_low_income_percentage"]]
            display_df.columns = ["County", "State", metric, metric_name_map["MEAN_low_income_percentage"]]
            st.download_button(f"Download {metric} Table", top.to_csv(index=False), f"top_{metric}.csv", "text/csv")
