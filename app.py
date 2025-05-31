import dash
from dash import dcc, html
from dash.dependencies import Input, Output
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# --- Metric Name Mapping ---
metric_name_map = {
    "Wind_Risk": "Wind Risk Score",
    "Drought_Risk": "Drought Risk Score",
    "Wildfire_Risk": "Wildfire Risk Score",
    "MEAN_low_income_percentage": "Low-Income Population (%)",
    "Identified as disadvantaged": "Disadvantaged Community",
    "Energy burden": "Energy Burden (%)",
    "PM2.5 in the air": "PM2.5 Air Pollution (µg/m³)",
    "Current asthma among adults aged greater than or equal to 18 years": "Adult Asthma Rate (%)",
    "Share of properties at risk of fire in 30 years": "Properties at Fire Risk (%)",
    "Total population": "Total Population",
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
        print(f"Error loading data from {url}: {e}")
        return pd.DataFrame()

def load_census():
    try:
        df = pd.read_csv(census_url)
        df.to_csv("census_data.csv", index=False)  # Optional: Save census data locally
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"County Name": "County", "State/Territory": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        return df
    except Exception as e:
        print(f"Error loading census data: {e}")
        return pd.DataFrame()

def load_health_data():
    try:
        df = pd.read_csv(health_url)
        df.columns = df.columns.str.strip()
        df = df.rename(columns={"CF": "County", "SF": "State"})
        df["County"] = df["County"].str.title()
        df["State"] = df["State"].str.title()
        df["MEAN_low_income_percentage"] = pd.to_numeric(df["MEAN_low_income_percentage"], errors='coerce')
        df["Asthma_Rate____"] = pd.to_numeric(df["Asthma_Rate____"], errors='coerce')
        return df.dropna(subset=["MEAN_low_income_percentage"])
    except Exception as e:
        print(f"Error loading health data: {e}")
        return pd.DataFrame()

def filter_hazard_data(df, risk_col, threshold):
    filtered_df = df[df[risk_col] >= threshold]
    filtered_df[risk_col] = pd.to_numeric(filtered_df[risk_col], errors='coerce')
    return filtered_df.dropna(subset=[risk_col])

def filter_by_state(df, state):
    if state == "All":
        return df
    return df[df["State"] == state]

# --- Load data ---
wind_df = load_hazard(wind_url, "Wind_Risk")
drought_df = load_hazard(drought_url, "Drought_Risk")
wildfire_df = load_hazard(wildfire_url, "Wildfire_Risk")
census_df = load_census()
health_df = load_health_data()

# --- Compute Key Findings ---
# Asthma and Low-Income: Top counties across all states
if not health_df.empty:
    top_asthma = health_df.sort_values(by="Asthma_Rate____", ascending=False).head(10)
    if len(top_asthma) >= 2:
        county1, county2 = top_asthma.iloc[0], top_asthma.iloc[1]
        asthma_finding = (
            f"For example, {county1['County']}, {county1['State']} has an asthma rate of {county1['Asthma_Rate____']:.1f}% "
            f"and a low-income population percentage of {county1['MEAN_low_income_percentage']:.1f}%, "
            f"while {county2['County']}, {county2['State']} shows an asthma rate of {county2['Asthma_Rate____']:.1f}% "
            f"with a low-income percentage of {county2['MEAN_low_income_percentage']:.1f}%. "
            "These counties rank among the top 10 for asthma prevalence, indicating a strong correlation "
            "between economic disadvantage and respiratory health challenges. Users can filter by state "
            "and select 'Asthma Rate (%)' to explore these patterns."
        )
    else:
        asthma_finding = "Insufficient data to identify top asthma counties across states."
else:
    asthma_finding = "No health data available."

# Wildfire Risk: Top counties across all states with risk >= 50
high_wildfire = wildfire_df[wildfire_df["Wildfire_Risk"] >= 50]
if not high_wildfire.empty:
    top_wildfire = high_wildfire.sort_values(by="Wildfire_Risk", ascending=False).head(10)
    if len(top_wildfire) >= 2:
        county1, county2 = top_wildfire.iloc[0], top_wildfire.iloc[1]
        max_risk = top_wildfire["Wildfire_Risk"].max()
        avg_low_income = top_wildfire["MEAN_low_income_percentage"].mean()
        wildfire_finding = (
            f"Counties like {county1['County']}, {county1['State']} and {county2['County']}, {county2['State']}, "
            f"which have low-income populations around {avg_low_income:.1f}%, also face elevated wildfire risks, "
            f"with scores reaching up to {max_risk:.1f}. This suggests a compounded vulnerability in these areas. "
            "Users can filter by state, choose 'Wildfire Risk,' and set the risk threshold to 50 to see similar results."
        )
    else:
        wildfire_finding = "Insufficient data to identify high wildfire risk counties."
else:
    wildfire_finding = "No wildfire data available with risk >= 50."

# --- Initialize Dash app ---
app = dash.Dash(__name__)

# --- State options for dropdown ---
states = ["All"] + sorted(health_df["State"].unique().tolist())

# --- Layout ---
app.layout = html.Div([  # Main Div open
    html.H1("GEV Analysis Dashboard", style={'textAlign': 'center', 'fontFamily': 'Arial'}),

    # Introduction
    html.Div([  # Intro Div open
        html.H3("Introduction", style={'fontFamily': 'Arial'}),
        html.P(
            "The 'Ten State Project' is a research initiative focused on evaluating climate risk vulnerabilities across ten U.S. states, emphasizing the interplay between environmental hazards, socioeconomic challenges, and health outcomes. By integrating advanced climate modeling with socioeconomic and health data, the project identifies regions most susceptible to extreme weather events like droughts, wildfires, and windstorms, particularly in low-income and marginalized communities. It aims to raise awareness among local populations about the compounded risks they face, such as increased asthma prevalence due to environmental stressors, and to provide data-driven insights for building resilience. The project uses tools like the Generalized Extreme Value (GEV) model to forecast future climate risks and overlays this with health and economic indicators to highlight disparities, enabling targeted interventions for at-risk areas.",
            style={'fontFamily': 'Arial', 'fontSize': '14px'}
        ),
        html.P(
            "Our project, the 'GEV Analysis Dashboard,' builds on the 'Ten State Project' by offering an interactive tool to explore these vulnerabilities at the county level across the U.S. We utilize datasets from AT&T Climate Resiliency, covering drought, wildfire, and wind risks, alongside U.S. Census Bureau data on socioeconomic factors and health metrics like asthma and diabetes rates. The dashboard allows users to filter by state, hazard type, and health indicators, providing a granular view of how climate risks intersect with economic and health challenges. By making this data accessible, we aim to empower community leaders, policymakers, and residents to address climate risks equitably, bridging the gap between complex data and actionable insights for vulnerable populations.",
            style={'fontFamily': 'Arial', 'fontSize': '14px'}
        ),
        html.Hr()
    ]),  # Intro Div close

    # Sidebar equivalent
    html.Div([  # Sidebar Div open
        html.H3("Filters", style={'fontFamily': 'Arial'}),
        dcc.Dropdown(
            id='state-dropdown',
            options=[{'label': s, 'value': s} for s in states],
            value='All',
            style={'width': '100%', 'fontFamily': 'Arial'}
        ),
        html.H3("Navigation", style={'fontFamily': 'Arial', 'marginTop': '20px'}),
        dcc.Dropdown(
            id='view-dropdown',
            options=[
                {'label': 'Hazard Map', 'value': 'Hazard Map'},
                {'label': 'Community Indicators', 'value': 'Community Indicators'},
                {'label': 'Health & Income', 'value': 'Health & Income'}
            ],
            value='Hazard Map',
            style={'width': '100%', 'fontFamily': 'Arial'}
        )
    ], style={'width': '20%', 'float': 'left', 'padding': '20px', 'boxSizing': 'border-box'}),  # Sidebar Div close

    # Main content
    html.Div([  # Main Content Div open
        # Hazard Map View
        html.Div(id='hazard-map-view', style={'display': 'none'}),
        html.Div([  # Hazard Content Div open
            dcc.Dropdown(
                id='hazard-dropdown',
                options=[
                    {'label': 'Wind Risk', 'value': 'Wind Risk'},
                    {'label': 'Drought Risk', 'value': 'Drought Risk'},
                    {'label': 'Wildfire Risk', 'value': 'Wildfire Risk'}
                ],
                value=['Wind Risk'],
                multi=True,
                style={'width': '100%', 'fontFamily': 'Arial'}
            ),
            dcc.Slider(
                id='threshold-slider',
                min=0.0,
                max=50.0,
                step=1.0,
                value=5.0,
                marks={i: str(i) for i in range(0, 51, 10)},
                tooltip={'placement': 'bottom'}
            ),
            html.H3(id='hazard-title', style={'fontFamily': 'Arial'}),
            html.P(
                "Note: Risk reflects 10-year median projections. Marker size shows low-income %, color shows hazard type. Adjust threshold or select multiple hazards to compare.",
                style={'fontFamily': 'Arial', 'fontStyle': 'italic'}
            ),
            dcc.Graph(id='hazard-map'),
            html.H3(id='hazard-top-title', style={'fontFamily': 'Arial'}),
            html.Div(id='hazard-plots')
        ], id='hazard-content', style={'display': 'none'}),  # Hazard Content Div close

        # Community Indicators View
        html.Div(id='community-indicators-view', style={'display': 'none'}),
        html.Div([  # Community Content Div open
            dcc.Dropdown(
                id='metric-dropdown',
                options=[{'label': metric_name_map[m], 'value': m} for m in [
                    "Identified as disadvantaged", "Energy burden", "PM2.5 in the air",
                    "Current asthma among adults aged greater than or equal to 18 years",
                    "Share of properties at risk of fire in 30 years", "Total population"
                ]],
                value="Energy burden",
                style={'width': '100%', 'fontFamily': 'Arial'}
            ),
            dcc.Slider(
                id='top-n-slider',
                min=5,
                max=50,
                step=5,
                value=10,
                marks={i: str(i) for i in range(5, 51, 10)},
                tooltip={'placement': 'bottom'}
            ),
            html.H3(id='community-title', style={'fontFamily': 'Arial'}),
            html.P(
                "Note: Explore metrics like energy burden or air quality. Higher values indicate greater vulnerability. Adjust 'Top N' to see more counties.",
                style={'fontFamily': 'Arial', 'fontStyle': 'italic'}
            ),
            html.Div(id='community-table'),
            dcc.Graph(id='community-bar')
        ], id='community-content', style={'display': 'none'}),  # Community Content Div close

        # Health & Income View
        html.Div(id='health-income-view', style={'display': 'none'}),
        html.Div([  # Health Content Div open
            dcc.Graph(id='income-histogram'),
            dcc.Dropdown(
                id='health-metric-dropdown',
                options=[{'label': metric_name_map[m], 'value': m} for m in [
                    "Asthma_Rate____", "Diabetes_Rate____", "Heart_Disease_Rate____", "Life_expectancy__years_"
                ]],
                value="Asthma_Rate____",
                style={'width': '100%', 'fontFamily': 'Arial'}
            ),
            html.H3(id='health-top-title', style={'fontFamily': 'Arial'}),
            dcc.Graph(id='health-bar'),
            html.Div(id='health-table')
        ], id='health-content', style={'display': 'none'}),  # Health Content Div close

        # Key Findings
        html.H3("Key Findings", style={'fontFamily': 'Arial'}),
        html.Ul([  # Key Findings List open
            html.Li([
                html.B("Health and Income Disparities: "),
                asthma_finding
            ], style={'fontFamily': 'Arial', 'fontSize': '14px'}),
            html.Li([
                html.B("Wildfire Risk Patterns: "),
                wildfire_finding
            ], style={'fontFamily': 'Arial', 'fontSize': '14px'})
        ])  # Key Findings List close
    ], style={'width': '80%', 'float': 'left', 'padding': '20px', 'boxSizing': 'border-box'})  # Main Content Div close
], style={'width': '100%', 'overflow': 'hidden'})  # Main Div close

# --- Callbacks ---
@app.callback(
    [Output('hazard-map-view', 'style'),
     Output('hazard-content', 'style'),
     Output('community-indicators-view', 'style'),
     Output('community-content', 'style'),
     Output('health-income-view', 'style'),
     Output('health-content', 'style')],
    [Input('view-dropdown', 'value')]
)
def toggle_view(view):
    hidden = {'display': 'none'}
    visible = {'display': 'block'}
    if view == "Hazard Map":
        return visible, visible, hidden, hidden, hidden, hidden
    elif view == "Community Indicators":
        return hidden, hidden, visible, visible, hidden, hidden
    else:
        return hidden, hidden, hidden, hidden, visible, visible

@app.callback(
    [Output('hazard-title', 'children'),
     Output('hazard-map', 'figure'),
     Output('hazard-top-title', 'children'),
     Output('hazard-plots', 'children')],
    [Input('state-dropdown', 'value'),
     Input('hazard-dropdown', 'value'),
     Input('threshold-slider', 'value')]
)
def update_hazard_view(state, hazards, threshold):
    wind_df_filtered = filter_by_state(wind_df, state)
    drought_df_filtered = filter_by_state(drought_df, state)
    wildfire_df_filtered = filter_by_state(wildfire_df, state)
    
    title = f"Hazard Exposure Across Counties ({state if state != 'All' else 'All States'})"
    fig = go.Figure()
    colors = {"Wind Risk": "#2D584A", "Drought Risk": "#759B90", "Wildfire Risk": "#000000"}  # Hex colors for all plots
    
    hazard_raw_map = {"Wind Risk": "Wind_Risk", "Drought Risk": "Drought_Risk", "Wildfire Risk": "Wildfire_Risk"}
    
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if filtered.empty:
            print(f"No counties meet the risk threshold for {metric_name_map[risk_col]} in {state if state != 'All' else 'the selected states'}.")
            continue
        fig.add_trace(go.Scattergeo(
            lon=filtered["Lon"],
            lat=filtered["Lat"],
            text=filtered["County"] + ", " + filtered["State"] + "<br>" + metric_name_map[risk_col] + ": " + filtered[risk_col].astype(str),
            marker=dict(
                size=filtered["MEAN_low_income_percentage"].clip(0, 100) * 0.15 + 5,
                color=colors[h],  # Use discrete color
                showscale=False,
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
    
    top_title = f"Top 10 Counties by Risk ({state if state != 'All' else 'All States'})"
    plots = []
    for h in hazards:
        risk_col = hazard_raw_map[h]
        df = wind_df_filtered if h == "Wind Risk" else drought_df_filtered if h == "Drought Risk" else wildfire_df_filtered
        filtered = filter_hazard_data(df, risk_col, threshold)
        if not filtered.empty:
            top_10 = filtered.sort_values(by=risk_col, ascending=False).head(10)
            top_10[risk_col] = pd.to_numeric(top_10[risk_col], errors='coerce')
            top_10["MEAN_low_income_percentage"] = pd.to_numeric(top_10["MEAN_low_income_percentage"], errors='coerce')
            top_10_clean = top_10.dropna(subset=[risk_col, "MEAN_low_income_percentage"])
            
            if top_10_clean.empty:
                plots.append(html.P(f"No valid data to plot for {metric_name_map[risk_col]} after cleaning.", style={'fontFamily': 'Arial', 'color': 'orange'}))
            else:
                hist_fig = px.histogram(
                    top_10_clean,
                    x=risk_col,
                    nbins=10,
                    title=f"Distribution of {metric_name_map[risk_col]} for Top 10 Counties",
                    color_discrete_sequence=[colors[h]],  # Use hex color
                    template="plotly_white"
                )
                hist_fig.update_layout(
                    xaxis_title=metric_name_map[risk_col],
                    yaxis_title="Number of Counties",
                    font=dict(family="Arial", size=12)
                )
                plots.append(dcc.Graph(figure=hist_fig))
                
                bar_fig = go.Figure()
                bar_fig.add_trace(go.Bar(
                    x=top_10_clean["County"],
                    y=top_10_clean[risk_col],
                    name=metric_name_map[risk_col],
                    marker_color=colors[h]  # Use hex color
                ))
                bar_fig.add_trace(go.Bar(
                    x=top_10_clean["County"],
                    y=top_10_clean["MEAN_low_income_percentage"],
                    name=metric_name_map["MEAN_low_income_percentage"],
                    marker_color="#C0C0C0"  # Light Gray
                ))
                bar_fig.update_layout(
                    title=f"Top 10 Counties: {metric_name_map[risk_col]} vs {metric_name_map['MEAN_low_income_percentage']}",
                    barmode="group",
                    xaxis_title="County",
                    yaxis_title="Value",
                    template="plotly_white",
                    font=dict(family="Arial", size=12),
                    xaxis_tickangle=-45
                )
                plots.append(dcc.Graph(figure=bar_fig))
        else:
            plots.append(html.P(f"No data to display for {metric_name_map[risk_col]} in {state if state != 'All' else 'the selected states'}.", style={'fontFamily': 'Arial', 'color': 'orange'}))
    
    return title, fig, top_title, plots

@app.callback(
    [Output('community-title', 'children'),
     Output('community-table', 'children'),
     Output('community-bar', 'figure')],
    [Input('state-dropdown', 'value'),
     Input('metric-dropdown', 'value'),
     Input('top-n-slider', 'value')]
)
def update_community_view(state, raw_metric, top_n):
    census_df_filtered = filter_by_state(census_df, state)
    title = f"Community Disadvantage & Demographics ({state if state != 'All' else 'All States'})"
    
    subset = census_df_filtered[census_df_filtered[raw_metric].notna()]
    if raw_metric == "Identified as disadvantaged":
        subset[raw_metric] = subset[raw_metric].astype(str).str.lower() == 'true'
        subset = subset[subset[raw_metric] == True]
    top = subset.sort_values(by=raw_metric, ascending=False).head(top_n)
    
    if top.empty:
        table = html.P(f"No data available for {metric_name_map[raw_metric]} in {state if state != 'All' else 'the selected states'}.", style={'fontFamily': 'Arial', 'color': 'orange'})
        fig = go.Figure()
    else:
        if raw_metric != "Identified as disadvantaged":
            top[raw_metric] = pd.to_numeric(top[raw_metric], errors='coerce')
            top = top.dropna(subset=[raw_metric])
        display_df = top[["County", "State", raw_metric, "Total population"]] if "Total population" in top.columns else top[["County", "State", raw_metric]]
        display_df.columns = [col if col not in metric_name_map else metric_name_map[col] for col in display_df.columns]
        table = html.Table([
            html.Thead(
                html.Tr([html.Th(col, style={'fontFamily': 'Arial', 'border': '1px solid black', 'padding': '5px'}) for col in display_df.columns])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(display_df.iloc[i][col], style={'fontFamily': 'Arial', 'border': '1px solid black', 'padding': '5px'})
                    for col in display_df.columns
                ]) for i in range(len(display_df))
            ])
        ], style={'borderCollapse': 'collapse', 'width': '100%'})
        
        if raw_metric != "Identified as disadvantaged":
            fig = px.bar(
                top, x="County", y=raw_metric, color="State",
                title=f"{metric_name_map[raw_metric]} by County in {state if state != 'All' else 'All States'}",
                color_discrete_sequence=["#2D584A"],  # Deep Green
                template="plotly_white"
            )
            fig.update_layout(xaxis_tickangle=-45, font=dict(family="Arial", size=12))
            fig.update_yaxes(title_text=metric_name_map[raw_metric])
        else:
            fig = go.Figure()
    
    return title, table, fig

@app.callback(
    [Output('income-histogram', 'figure'),
     Output('health-top-title', 'children'),
     Output('health-bar', 'figure'),
     Output('health-table', 'children')],
    [Input('state-dropdown', 'value'),
     Input('health-metric-dropdown', 'value')]
)
def update_health_view(state, raw_metric):
    health_df_filtered = filter_by_state(health_df, state)
    
    if health_df_filtered.empty:
        hist = go.Figure()
        title = f"Community Health and Income Risks ({state if state != 'All' else 'All States'})"
        bar = go.Figure()
        table = html.P(f"No health data available for {state if state != 'All' else 'the selected states'}.", style={'fontFamily': 'Arial', 'color': 'orange'})
        return hist, title, bar, table
    
    hist = px.histogram(
        health_df_filtered,
        x="MEAN_low_income_percentage",
        nbins=30,
        title=f"Low-Income Distribution Across Counties in {state if state != 'All' else 'All States'}",
        color_discrete_sequence=["#C0C0C0"],  # Light Gray
        template="plotly_white"
    )
    hist.update_layout(font=dict(family="Arial", size=12))
    hist.update_xaxes(title_text=metric_name_map["MEAN_low_income_percentage"])
    
    health_df_filtered[raw_metric] = pd.to_numeric(health_df_filtered[raw_metric], errors='coerce')
    top = health_df_filtered.sort_values(by=raw_metric, ascending=False).head(10)
    top = top.dropna(subset=[raw_metric])
    
    title = f"Top 10 Counties by {metric_name_map[raw_metric]} in {state if state != 'All' else 'All States'}"
    if top.empty:
        bar = go.Figure()
        table = html.P(f"No data available for {metric_name_map[raw_metric]} in {state if state != 'All' else 'the selected states'}.", style={'fontFamily': 'Arial', 'color': 'orange'})
    else:
        bar = px.bar(
            top,
            x="County",
            y=raw_metric,
            color="State",
            title=f"Top 10 Counties for {metric_name_map[raw_metric]} in {state if state != 'All' else 'All States'}",
            hover_data=["MEAN_low_income_percentage"],
            color_discrete_sequence=["#2D584A"],  # Deep Green
            template="plotly_white"
        )
        bar.update_layout(font=dict(family="Arial", size=12))
        bar.update_yaxes(title_text=metric_name_map[raw_metric])
        bar.update_traces(hovertemplate="County: %{x}<br>" + metric_name_map[raw_metric] + ": %{y}<br>" + metric_name_map["MEAN_low_income_percentage"] + ": %{customdata}")
        
        display_df = top[["County", "State", raw_metric, "MEAN_low_income_percentage"]]
        display_df.columns = ["County", "State", metric_name_map[raw_metric], metric_name_map["MEAN_low_income_percentage"]]
        table = html.Table([
            html.Thead(
                html.Tr([html.Th(col, style={'fontFamily': 'Arial', 'border': '1px solid black', 'padding': '5px'}) for col in display_df.columns])
            ),
            html.Tbody([
                html.Tr([
                    html.Td(display_df.iloc[i][col], style={'fontFamily': 'Arial', 'border': '1px solid black', 'padding': '5px'})
                    for col in display_df.columns
                ]) for i in range(len(display_df))
            ])
        ], style={'borderCollapse': 'collapse', 'width': '100%'})
    
    return hist, title, bar, table

# --- Run the app ---
if __name__ == '__main__':
    app.run(debug=True)
