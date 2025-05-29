# app2.py
import pandas as pd

def load_wind_data():
    url = "https://undivideprojectdata.blob.core.windows.net/gev/wind.csv?sp=r&st=2025-05-29T02:38:12Z&se=2090-05-29T10:38:12Z&spr=https&sv=2024-11-04&sr=b&sig=ULQfBKey%2BI5%2BNDyRnvkREtbbKshrFWjwHrNmzVzayOk%3D"
    df = pd.read_csv(url)

    df = df.rename(columns={
        "CF": "County",
        "SF": "State",
        "MEAN_low_income_percentage": "Low_Income_Pct",
        "midcent_median_10yr": "Wind_Risk",
        "Latitude": "Lat",
        "Longitude": "Lon"
    })

    df = df.dropna(subset=["Lat", "Lon", "Wind_Risk"])
    df["County"] = df["County"].str.title()
    return df
