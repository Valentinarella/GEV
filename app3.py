# app3.py
import pandas as pd

def load_wildfire_data():
    url = "https://undivideprojectdata.blob.core.windows.net/gev/wildfire.csv?sp=r&st=2025-05-29T03:04:38Z&se=2090-05-29T11:04:38Z&spr=https&sv=2024-11-04&sr=b&sig=Vd%2FhCXRq3gQF2WmdI3wjoksdl0nPTmCWUSrYodobDyw%3D"
    df = pd.read_csv(url)

    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": "Wildfire_Risk",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })

    df = df.dropna(subset=["Lat", "Lon", "Wildfire_Risk"])
    df["County"] = df["County"].str.title()

    return df
