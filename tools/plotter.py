"""Plotter tool — generates interactive distribution charts using Plotly."""

import os
import time
import json
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
CHART_OUTPUT_DIR = os.getenv("CHART_OUTPUT_DIR", "./outputs")


def plot_distribution(filename: str, column: str, chart_type: str = "auto") -> dict:
    """
    Generate an interactive distribution chart for a column in a CSV file using Plotly.

    Args:
        filename: Name of the CSV file in the uploads directory.
        column: Column name to plot.
        chart_type: "auto" (detect), "histogram", or "bar".

    Returns:
        Dictionary with chart_json (Plotly JSON), chart_url, column name, and chart_type used.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": f"File '{filename}' not found."}

        df = pd.read_csv(filepath)

        if column not in df.columns:
            return {"error": f"Column '{column}' not found. Available columns: {list(df.columns)}"}

        os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)

        col_data = df[column].dropna()
        is_numeric = pd.api.types.is_numeric_dtype(col_data)

        if chart_type == "auto":
            chart_type = "histogram" if is_numeric else "bar"

        if chart_type == "histogram" and is_numeric:
            fig = px.histogram(
                df, x=column,
                title=f"Distribution of {column}",
                color_discrete_sequence=["#818cf8"],
                template="plotly_dark",
            )
            fig.update_traces(marker_line_color="#6366f1", marker_line_width=1)
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(18,19,23,0.8)",
                font=dict(family="Inter, sans-serif", color="#e3e2e8"),
                title_font=dict(size=18, color="#e3e2e8"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(t=60, l=50, r=20, b=50),
            )
        elif chart_type == "bar" or not is_numeric:
            chart_type = "bar"
            value_counts = col_data.value_counts().head(20).reset_index()
            value_counts.columns = [column, "Count"]
            fig = px.bar(
                value_counts, x="Count", y=column, orientation="h",
                title=f"Top Values in {column}",
                color="Count",
                color_continuous_scale=["#312e81", "#6366f1", "#a5b4fc"],
                template="plotly_dark",
            )
            fig.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(18,19,23,0.8)",
                font=dict(family="Inter, sans-serif", color="#e3e2e8"),
                title_font=dict(size=18, color="#e3e2e8"),
                xaxis=dict(gridcolor="rgba(255,255,255,0.05)"),
                yaxis=dict(categoryorder="total ascending", gridcolor="rgba(255,255,255,0.05)"),
                margin=dict(t=60, l=120, r=20, b=50),
                coloraxis_showscale=False,
            )
        else:
            return {"error": f"Unsupported chart_type '{chart_type}'. Use 'auto', 'histogram', or 'bar'."}

        # Save chart as JSON
        chart_json_str = fig.to_json()

        timestamp = int(time.time())
        base_name = os.path.splitext(filename)[0]
        chart_filename = f"{base_name}_{column}_{timestamp}.json"
        chart_path = os.path.join(CHART_OUTPUT_DIR, chart_filename)

        with open(chart_path, "w") as f:
            f.write(chart_json_str)

        chart_url = f"/chart/{chart_filename}"

        return {
            "chart_path": chart_path,
            "chart_url": chart_url,
            "chart_json": chart_json_str,
            "column": column,
            "chart_type": chart_type,
        }

    except Exception as e:
        return {"error": f"Plot generation failed: {str(e)}"}
