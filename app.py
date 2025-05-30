import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- Setup ---
st.set_page_config(layout="wide")

# --- Load Data ---
@st.cache_data
def load_data(url, label):
    try:
        df = pd.read_csv(url)
        df.columns = df.columns.str.strip()

        for col in ["CF", "SF", "County Name", "State/Territory"]:
            if col in df.columns:
                df[col] = df[col].astype(str).str.title()

        lat_col = next((c for c in df.columns if "lat" in c.lower()), None)
        lon_col = next((c for c in df.columns if "lon" in c.lower() or "lng" in c.lower()), None)

        if not lat_col or not lon_col:
            st.warning(f"Missing coordinates in {label}")
            return pd.DataFrame()

        df["Latitude"] = df[lat_col]
        df["Longitude"] = df[lon_col]
        df = df.dropna(subset=["Latitude", "Longitude"])

        return df
    except Exception as e:
        st.error(f"Error loading {label}: {e}")
        return pd.DataFrame()

# --- Choose which dataset to load ---
dataset_name = st.sidebar.selectbox("Dataset", ["Census Tracts", "Wind Risk", "Drought Risk", "Wildfire Risk"])

dataset_urls = {
    "Census Tracts": "https://undivideprojectdata.blob.core.windows.net/gev/1.0-communities.csv?sp=r&st=2025-05-30T23:23:50Z&se=2090-05-31T07:23:50Z&spr=https&sv=2024-11-04&sr=b&sig=qC7ouZhUV%2BOMrZJ4tvHslvQeKUdXdA15arv%2FE2pPxEI%3D",
    "Wind Risk": "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T03:41:03Z&se=2090-05-29T11:41:03Z&spr=https&sv=2024-11-04&sr=b&sig=iHyfpuXMWL7L59fxz1X8lcgcM4Wiqlaf2ybA%2FTX14Bg%3D",
    "Drought Risk": "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T03:49:51Z&se=2090-05-29T11:49:51Z&spr=https&sv=2024-11-04&sr=b&sig=UCvT2wK1gzScGOYyK0WWAwtWZSmmVf3T1HGjyOkaeZk%3D",
    "Wildfire Risk": "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
}

df = load_data(dataset_urls[dataset_name], dataset_name)

# --- Plot the Map ---
if not df.empty:
    loc_col = "County Name" if "County Name" in df.columns else "CF"
    state_col = "State/Territory" if "State/Territory" in df.columns else "SF"

    fig = go.Figure(go.Scattergeo(
        lon=df["Longitude"],
        lat=df["Latitude"],
        text=df[loc_col] + ", " + df[state_col],
        marker=dict(
            size=6,
            color="royalblue",
            opacity=0.7
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

    st.title(f"{dataset_name} Locations")
    st.plotly_chart(fig, use_container_width=True)

else:
    st.warning("No data to display.")
