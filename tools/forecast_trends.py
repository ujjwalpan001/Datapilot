"""Forecast Trends tool — predictive analytics using scikit-learn."""

import os
import time
import json
import pandas as pd
import numpy as np
from sklearn.linear_model import LinearRegression
from sklearn.preprocessing import PolynomialFeatures
from sklearn.pipeline import make_pipeline
import plotly.graph_objects as go


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
CHART_OUTPUT_DIR = os.getenv("CHART_OUTPUT_DIR", "./outputs")


def forecast_trends(
    filename: str,
    date_column: str,
    value_column: str,
    periods: int = 30,
    aggregation: str = "sum",
) -> dict:
    """
    Forecast future trends for a numeric column based on historical data.

    Args:
        filename: Name of the CSV file.
        date_column: Column containing date/time values.
        value_column: Numeric column to forecast.
        periods: Number of future periods to predict (days).
        aggregation: How to aggregate daily data — "sum", "mean", "count".

    Returns:
        Dictionary with historical data, forecast data, model info, and Plotly chart JSON.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": f"File '{filename}' not found."}

        df = pd.read_csv(filepath)

        if date_column not in df.columns:
            return {"error": f"Date column '{date_column}' not found. Available: {list(df.columns)}"}
        if value_column not in df.columns:
            return {"error": f"Value column '{value_column}' not found. Available: {list(df.columns)}"}

        # Parse dates
        try:
            df[date_column] = pd.to_datetime(df[date_column], infer_datetime_format=True)
        except Exception:
            return {"error": f"Could not parse '{date_column}' as dates. Ensure it contains valid date values."}

        # Aggregate by date
        if aggregation == "sum":
            daily = df.groupby(df[date_column].dt.date)[value_column].sum().reset_index()
        elif aggregation == "mean":
            daily = df.groupby(df[date_column].dt.date)[value_column].mean().reset_index()
        elif aggregation == "count":
            daily = df.groupby(df[date_column].dt.date)[value_column].count().reset_index()
        else:
            daily = df.groupby(df[date_column].dt.date)[value_column].sum().reset_index()

        daily.columns = ["date", "value"]
        daily["date"] = pd.to_datetime(daily["date"])
        daily = daily.sort_values("date").reset_index(drop=True)

        if len(daily) < 5:
            return {"error": f"Not enough data points for forecasting. Need at least 5, got {len(daily)}."}

        # Convert dates to numeric (days since first date)
        daily["day_num"] = (daily["date"] - daily["date"].min()).dt.days
        X = daily["day_num"].values.reshape(-1, 1)
        y = daily["value"].values

        # Fit polynomial regression (degree 2 for gentle curves)
        degree = 2 if len(daily) > 10 else 1
        model = make_pipeline(PolynomialFeatures(degree), LinearRegression())
        model.fit(X, y)

        # R² score
        r2_score = round(model.score(X, y), 4)

        # Predict on historical data
        y_fitted = model.predict(X)

        # Generate future dates
        last_day = int(daily["day_num"].max())
        future_days = np.arange(last_day + 1, last_day + periods + 1).reshape(-1, 1)
        y_forecast = model.predict(future_days)

        # Ensure no negative forecasts for typically positive metrics
        y_forecast = np.maximum(y_forecast, 0)

        last_date = daily["date"].max()
        future_dates = [last_date + pd.Timedelta(days=int(d - last_day)) for d in future_days.flatten()]

        # Build Plotly chart
        fig = go.Figure()

        # Historical data
        fig.add_trace(go.Scatter(
            x=daily["date"].tolist(),
            y=daily["value"].tolist(),
            mode="markers+lines",
            name="Historical Data",
            line=dict(color="#818cf8", width=2),
            marker=dict(size=4, color="#818cf8"),
        ))

        # Fitted trend line
        fig.add_trace(go.Scatter(
            x=daily["date"].tolist(),
            y=y_fitted.tolist(),
            mode="lines",
            name="Trend Line",
            line=dict(color="#a5b4fc", width=2, dash="dot"),
        ))

        # Forecast
        fig.add_trace(go.Scatter(
            x=[d.strftime("%Y-%m-%d") for d in future_dates],
            y=y_forecast.tolist(),
            mode="lines+markers",
            name=f"Forecast ({periods} days)",
            line=dict(color="#f472b6", width=2, dash="dash"),
            marker=dict(size=5, color="#f472b6"),
        ))

        fig.update_layout(
            title=f"Forecast: {value_column} ({aggregation}) — Next {periods} Days",
            template="plotly_dark",
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(18,19,23,0.8)",
            font=dict(family="Inter, sans-serif", color="#e3e2e8"),
            title_font=dict(size=18, color="#e3e2e8"),
            xaxis=dict(title="Date", gridcolor="rgba(255,255,255,0.05)"),
            yaxis=dict(title=value_column, gridcolor="rgba(255,255,255,0.05)"),
            margin=dict(t=60, l=50, r=20, b=50),
            legend=dict(bgcolor="rgba(0,0,0,0.3)"),
        )

        # Save chart JSON
        chart_json_str = fig.to_json()
        os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)

        timestamp = int(time.time())
        base_name = os.path.splitext(filename)[0]
        chart_filename = f"{base_name}_forecast_{timestamp}.json"
        chart_path = os.path.join(CHART_OUTPUT_DIR, chart_filename)

        with open(chart_path, "w") as f:
            f.write(chart_json_str)

        chart_url = f"/chart/{chart_filename}"

        # Build forecast summary
        forecast_summary = {
            "last_historical_date": daily["date"].max().strftime("%Y-%m-%d"),
            "forecast_end_date": future_dates[-1].strftime("%Y-%m-%d"),
            "forecast_avg": round(float(np.mean(y_forecast)), 2),
            "forecast_min": round(float(np.min(y_forecast)), 2),
            "forecast_max": round(float(np.max(y_forecast)), 2),
            "historical_avg": round(float(np.mean(y)), 2),
            "trend_direction": "upward" if y_forecast[-1] > y_forecast[0] else "downward",
        }

        return {
            "chart_url": chart_url,
            "chart_json": chart_json_str,
            "model_type": f"Polynomial Regression (degree {degree})",
            "r2_score": r2_score,
            "data_points_used": len(daily),
            "forecast_periods": periods,
            "aggregation": aggregation,
            "forecast_summary": forecast_summary,
            "message": (
                f"Forecasted '{value_column}' for the next {periods} days using {len(daily)} historical data points. "
                f"Model R² = {r2_score}. Trend is {forecast_summary['trend_direction']}. "
                f"Predicted average: {forecast_summary['forecast_avg']:.2f}."
            ),
        }

    except Exception as e:
        return {"error": f"Forecasting failed: {str(e)}"}
