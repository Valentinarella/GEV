# data_loader.py
import streamlit as st
import pandas as pd

@st.cache_data
def load_hazard(url, risk_col):
    try:
        df = pd.read_csv(url, usecols=["CF", "SF", "Latitude", "Longitude", "MEAN_low_income_percentage", "midcent_median_10yr"])
        df = df.rename(columns={"CF": "County", "SF": "State", "Latitude": "Lat", "Longitude": "Lon", 
                                "MEAN_low_income_percentage": "MEAN_low_income_percentage", "midcent_median_10yr": risk_col})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        df[risk_col] = pd.to_numeric(df[risk_col], errors='coerce')
        df["MEAN_low_income_percentage"] = pd.to_numeric(df["MEAN_low_income_percentage"], errors='coerce')
        return df.dropna(subset=["Lat", "Lon", risk_col])
    except Exception as e:
        st.error(f"Error loading data from {url}: {e}")
        return pd.DataFrame()

@st.cache_data
def load_census(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"County Name": "County", "State/Territory": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df
    except Exception as e:
        st.error(f"Error loading census data: {e}")
        return pd.DataFrame()

@st.cache_data
def load_health_data(url):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"CF": "County", "SF": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        df["MEAN_low_income_percentage"] = pd.to_numeric(df["MEAN_low_income_percentage"], errors='coerce')
        return df.dropna(subset=["MEAN_low_income_percentage"])
    except Exception as e:
        st.error(f"Error loading health data: {e}")
        return pd.DataFrame()

@st.cache_data
def filter_hazard_data(df, risk_col, threshold):
    filtered_df = df[df[risk_col] >= threshold]
    filtered_df[risk_col] = pd.to_numeric(filtered_df[risk_col], errors='coerce')
    return filtered_df.dropna(subset=[risk_col])

def filter_by_state(df, state):
    if state == "All":
        return df
    return df[df["State"] == state]
