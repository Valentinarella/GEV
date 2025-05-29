# app1.py
import pandas as pd

def load_drought_data():
    url = "https://undivideprojectdata.blob.core.windows.net/gev/drought_analysis.csv?sp=r&st=2025-05-29T02:27:37Z&se=2090-05-29T10:27:37Z&spr=https&sv=2024-11-04&sr=b&sig=7MMjLjaGCp0QnBzF1jSYnJK6OWuaaBrvJPJbiwICfIw%3D"
    df = pd.read_csv(url)

    # Clean and rename for clarity
    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": "Drought_Risk",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })

    # Drop rows without lat/lon or drought risk
    df = df.dropna(subset=["Lat", "Lon", "Drought_Risk"])

    # Capitalize county names for display
    df["County"] = df["County"].str.title()

    return df
