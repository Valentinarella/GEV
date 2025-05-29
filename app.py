# app.py
import dash
from dash import dcc, html, Input, Output
import dash_bootstrap_components as dbc
import plotly.express as px

# Load your custom loaders
from app1 import load_drought_data
from app2 import load_wind_data
from app3 import load_wildfire_data  # create this if wildfire is not split yet

# Load datasets
drought_df = load_drought_data()
wind_df = load_wind_data()
wildfire_df = load_wildfire_data()

# Start app
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.LUX])
app.title = "Multi-Hazard Risk Dashboard"

app.layout = dbc.Container([
    html.H2("USA Climate Risk Map", className="text-center text-primary mb-4"),

    dbc.Row([
        dbc.Col(dcc.Dropdown(
            id="hazard-selector",
            options=[
                {"label": "Drought Risk", "value": "drought"},
                {"label": "Wind Risk", "value": "wind"},
                {"label": "Wildfire Risk", "value": "wildfire"},
            ],
            value="drought",
            clearable=False
        ), width=6),
    ], className="mb-4 justify-content-center"),

    dbc.Row([
        dbc.Col(dcc.Graph(id="hazard-map", style={"height": "600px"}), width=12)
    ])
], fluid=True)

@app.callback(
    Output("hazard-map", "figure"),
    Input("hazard-selector", "value")
)
def update_map(hazard):
    if hazard == "drought":
        df = drought_df
        risk_col = "Drought_Risk"
        title = "Drought Risk (10-year Median)"
    elif hazard == "wind":
        df = wind_df
        risk_col = "Wind_Risk"
        title = "Wind Risk (10-year Median)"
    else:
        df = wildfire_df
        risk_col = "Wildfire_Risk"
        title = "Wildfire Risk (10-year Median)"

    fig = px.scatter_mapbox(
        df,
        lat="Lat",
        lon="Lon",
        color=risk_col,
        hover_name="County",
        hover_data=["State", "Low_Income_Pct"],
        color_continuous_scale="OrRd",
        zoom=3
    )
    fig.update_layout(
        mapbox_style="carto-positron",
        margin={"r":0, "t":40, "l":0, "b":0},
        title=title
    )
    return fig

if __name__ == "__main__":
    app.run(debug=True)

