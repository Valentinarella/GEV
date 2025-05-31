import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd  # Added for merging and numeric operations
from data_loader import filter_hazard_data  # Already imported

def hazard_map_view(wind_df_filtered, drought_df_filtered, wildfire_df_filtered, selected_state, metric_name_map):
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
    st.plotly_chart(fig, use_container_width=True)

    st.subheader(f"Top 10 Counties by Risk ({selected_state if selected_state != 'All' else 'All States'})")
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
                st.warning(f"No valid data to plot for {metric_name_map[risk_col]} after cleaning. Displaying raw data instead.")
                st.dataframe(top_10)
            else:
                try:
                    hist_fig = px.histogram(
                        top_10_clean,
                        x=risk_col,
                        nbins=10,
                        title=f"Distribution of {metric_name_map[risk_col]} for Top 10 Counties",
                        color_discrete_sequence=[colors[h]],
                        template="plotly_white"
                    )
                    hist_fig.update_layout(
                        xaxis_title=metric_name_map[risk_col],
                        yaxis_title="Number of Counties",
                        font=dict(family="Arial", size=12)
                    )
                    st.plotly_chart(hist_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Failed to create histogram for {metric_name_map[risk_col]}. Displaying raw data instead. Error: {str(e)}")
                    st.dataframe(top_10)

                try:
                    bar_fig = go.Figure()
                    bar_fig.add_trace(go.Bar(
                        x=top_10_clean["County"],
                        y=top_10_clean[risk_col],
                        name=metric_name_map[risk_col],
                        marker_color=colors[h]
                    ))
                    bar_fig.add_trace(go.Bar(
                        x=top_10_clean["County"],
                        y=top_10_clean["MEAN_low_income_percentage"],
                        name=metric_name_map["MEAN_low_income_percentage"],
                        marker_color="#1f77b4"
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
                    st.plotly_chart(bar_fig, use_container_width=True)
                except Exception as e:
                    st.warning(f"Failed to create bar chart. Displaying raw data instead. Error: {str(e)}")
                    st.dataframe(top_10)

            st.download_button(f"Download {metric_name_map[risk_col]} Table", top_10.to_csv(index=False), f"top_{h}.csv", "text/csv")
        else:
            st.warning(f"No data to display for {metric_name_map[risk_col]} in {selected_state if selected_state != 'All' else 'the selected states'}.")

    # New Section: Top 10 Counties by Combined Risk (All States)
    st.subheader("Top 10 Counties by Combined Risk (All States)")
    hazard_dfs = {
        "Wind_Risk": wind_df_filtered,
        "Drought_Risk": drought_df_filtered,
        "Wildfire_Risk": wildfire_df_filtered
    }
    combined_df = None
    for risk_col, df in hazard_dfs.items():
        filtered = filter_hazard_data(df, risk_col, threshold)
        if not filtered.empty:
            # Normalize risk scores to 0-100 for fair comparison
            filtered[risk_col] = pd.to_numeric(filtered[risk_col], errors='coerce')
            max_val = filtered[risk_col].max()
            min_val = filtered[risk_col].min()
            if max_val != min_val:  # Avoid division by zero
                filtered[f"Normalized_{risk_col}"] = 100 * (filtered[risk_col] - min_val) / (max_val - min_val)
            else:
                filtered[f"Normalized_{risk_col}"] = 100  # If all values are same, set to max
            # Select columns for merging
            subset = filtered[["County", "State", f"Normalized_{risk_col}", "MEAN_low_income_percentage"]]
            if combined_df is None:
                combined_df = subset
            else:
                combined_df = combined_df.merge(
                    subset,
                    on=["County", "State", "MEAN_low_income_percentage"],
                    how="outer"
                )
    
    if combined_df is None or combined_df.empty:
        st.warning("No data available to compute combined risk across all hazards.")
    else:
        # Calculate average normalized risk
        norm_cols = [f"Normalized_{col}" for col in hazard_dfs.keys()]
        combined_df["Combined_Risk"] = combined_df[norm_cols].mean(axis=1)
        combined_df["MEAN_low_income_percentage"] = pd.to_numeric(combined_df["MEAN_low_income_percentage"], errors='coerce')
        top_10_combined = combined_df.dropna(subset=["Combined_Risk", "MEAN_low_income_percentage"])
        top_10_combined = top_10_combined.sort_values(by="Combined_Risk", ascending=False).head(10)
        
        if top_10_combined.empty:
            st.warning("No valid data to plot for combined risk after cleaning. Displaying raw data instead.")
            st.dataframe(combined_df.head(10))
        else:
            try:
                bar_fig = go.Figure()
                bar_fig.add_trace(go.Bar(
                    x=top_10_combined["County"],
                    y=top_10_combined["Combined_Risk"],
                    name="Combined Risk Score",
                    marker_color="#ff4500"  # Orange-red for combined risk
                ))
                bar_fig.add_trace(go.Bar(
                    x=top_10_combined["County"],
                    y=top_10_combined["MEAN_low_income_percentage"],
                    name=metric_name_map["MEAN_low_income_percentage"],
                    marker_color="#1f77b4"  # Blue for low-income, consistent with app
                ))
                bar_fig.update_layout(
                    title="Top 10 Counties: Combined Risk vs Low-Income Percentage (All States)",
                    barmode="group",
                    xaxis_title="County",
                    yaxis_title="Value",
                    template="plotly_white",
                    font=dict(family="Arial", size=12),
                    xaxis_tickangle=-45
                )
                st.plotly_chart(bar_fig, use_container_width=True)
            except Exception as e:
                st.warning(f"Failed to create bar chart for combined risk. Displaying raw data instead. Error: {str(e)}")
                st.dataframe(top_10_combined)
            
            # Display and download
            display_df = top_10_combined[["County", "State", "Combined_Risk", "MEAN_low_income_percentage"]]
            display_df.columns = ["County", "State", "Combined Risk Score", metric_name_map["MEAN_low_income_percentage"]]
            st.dataframe(display_df)
            st.download_button(
                "Download Combined Risk Table",
                top_10_combined.to_csv(index=False),
                "top_combined_risk.csv",
                "text/csv"
            )
