import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import seaborn as sns
import matplotlib.pyplot as plt

# --- Page setup ---
st.set_page_config(layout="wide")
st.cache_data.clear()

# --- Data URLs ---
wind_url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?..."
drought_url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?..."
wildfire_url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?..."
census_url = "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?..."
health_url = "https://undivideprojectdata.blob.core.windows.net/gev/health.csv?..."

# --- Load data functions ---
@st.cache_data
def load_hazard(url, risk_column):
    df = pd.read_csv(url)
    df = df.rename(columns={
        "CF": "County", "SF": "State",
        "Latitude": "Lat", "Longitude": "Lon",
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
    df = df.rename(columns={"County Name": "County", "State/Territory": "State"})
    df["County"] = df["County"].str.title()
    df["State"] = df["State"].str.title()
    return df

@st.cache_data
def load_health():
    df = pd.read_csv(health_url)
    df = df.rename(columns={"CF": "County", "SF": "State"})
    df["County"] = df["County"].str.title()
    df["State"] = df["State"].str.title()
    return df

# --- Load datasets ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census()
health_df = load_health()

# --- Intro ---
st.title("Multi-Hazard + Community Vulnerability Dashboard")
st.markdown("""
Welcome to this dashboard for identifying U.S. communities facing overlapping **climate hazards** and **social vulnerabilities**.
""")

# --- Sidebar view toggle ---
view = st.sidebar.radio("Choose View", ["Hazard Map", "Community Data", "Health + Income Analysis"])

# --- Hazard View ---
if view == "Hazard Map":
    hazard = st.sidebar.selectbox("Select Hazard", ["Wind Risk", "Drought Risk", "Wildfire Risk"])
    min_value = st.sidebar.slider("Minimum Risk", 0.0, 50.0, 5.0)

    df, risk_col, colorscale = {
        "Wind Risk": (wind_df, "Wind_Risk", "Blues"),
        "Drought Risk": (drought_df, "Drought_Risk", "Oranges"),
        "Wildfire Risk": (wildfire_df, "Wildfire_Risk", "Reds")
    }[hazard]

    data = df[df[risk_col] >= min_value]

    st.subheader("Hazard Exposure Map")
    if data.empty:
        st.warning("No data meets the threshold.")
    else:
        fig = go.Figure(go.Scattergeo(
            lon=data["Lon"], lat=data["Lat"],
            text=data["County"] + ", " + data["State"] + "<br>Risk: " + data[risk_col].astype(str),
            marker=dict(size=data["Low_Income_Pct"] * 0.7, color=data[risk_col],
                        colorscale=colorscale, showscale=True, colorbar=dict(title=risk_col))
        ))
        fig.update_layout(
            geo=dict(scope="usa", landcolor="lightgray", center={"lat": 37.0902, "lon": -95.7129}),
            margin={"r":0, "t":30, "l":0, "b":0}, height=600
        )
        st.plotly_chart(fig, use_container_width=True)
        st.dataframe(data.sort_values(by=risk_col, ascending=False).head(10)[["County", "State", risk_col, "Low_Income_Pct"]])

# --- Community View ---
elif view == "Community Data":
    metric = st.sidebar.selectbox("Metric", [
        "Identified as disadvantaged", "Energy burden", "PM2.5 in the air",
        "Current asthma among adults aged greater than or equal to 18 years",
        "Share of properties at risk of fire in 30 years", "Total population"
    ])
    top_n = st.sidebar.slider("Top N", 5, 50, 10)

    df = census_df[census_df[metric].notna()].copy()
    if metric == "Identified as disadvantaged":
        df = df[df[metric] == True]

    top = df.sort_values(by=metric, ascending=False).head(top_n)
    st.subheader(f"Top {top_n} Communities by '{metric}'")
    st.dataframe(top[["County", "State", metric, "Total population"]] if "Total population" in top.columns else top[["County", "State", metric]])

    if metric != "Identified as disadvantaged":
        fig = px.bar(top, x="County", y=metric, color="State", title=f"{metric} by County")
        st.plotly_chart(fig, use_container_width=True)

# --- Health + Income Bivariate ---
else:
    st.subheader("Health + Income Bivariate Analysis")
    biv_metric = st.selectbox("Select Health Metric", {
        "Asthma": "Asthma_Rate____",
        "Diabetes": "Diabetes_Rate____",
        "Heart Disease": "Heart_Disease_Rate____",
        "Life Expectancy": "Life_expectancy__years_"
    })

    biv_df = health_df.dropna(subset=[biv_metric, "MEAN_low_income_percentage"]).copy()
    biv_df["Health_Category"] = pd.qcut(biv_df[biv_metric], q=2, labels=["Low", "High"])
    biv_df["Income_Category"] = pd.qcut(biv_df["MEAN_low_income_percentage"], q=2, labels=["Low", "High"])
    biv_df["Class"] = biv_df["Income_Category"] + " LIR / " + biv_df["Health_Category"] + f" {biv_metric.split('_')[0]}"

    class_counts = biv_df["Class"].value_counts().sort_index()
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(x=class_counts.index, y=class_counts.values, palette="Purples", ax=ax)
    ax.set_title(f"{biv_metric.split('_')[0]} vs Low-Income Rate")
    ax.set_ylabel("Number of Counties")
    ax.set_xlabel("Risk Category")
    plt.xticks(rotation=45)
    st.pyplot(fig)
