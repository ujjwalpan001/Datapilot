"""Top N tool — finds the top N values in a column by count, sum, or mean."""

import os
import time
import pandas as pd
import numpy as np


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
CHART_OUTPUT_DIR = os.getenv("CHART_OUTPUT_DIR", "./outputs")


def top_n_values(filename: str, column: str, n: int = 10, metric: str = "count") -> dict:
    """
    Find the top N values in a column aggregated by a given metric.

    Args:
        filename: Name of the CSV file.
        column: Column name to analyze.
        n: Number of top results to return.
        metric: Aggregation method — "count", "sum", "mean", "max", or "min".

    Returns:
        Dictionary with sorted results and export URL.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": f"File '{filename}' not found."}

        df = pd.read_csv(filepath)

        if column not in df.columns:
            return {"error": f"Column '{column}' not found. Available columns: {list(df.columns)}"}

        export_df = None

        if metric == "count":
            result_series = df[column].value_counts().head(n)
            results = [
                {"value": str(val), "metric_value": int(count)}
                for val, count in result_series.items()
            ]
            export_df = result_series.reset_index()
            export_df.columns = [column, "count"]
        elif metric in ("sum", "mean", "max", "min"):
            numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
            if not numeric_cols:
                return {"error": f"No numeric columns available for {metric} aggregation."}

            agg_col = None
            for nc in numeric_cols:
                if nc != column:
                    agg_col = nc
                    break
            if agg_col is None:
                agg_col = numeric_cols[0]

            if metric == "sum":
                grouped = df.groupby(column)[agg_col].sum().nlargest(n)
            elif metric == "mean":
                grouped = df.groupby(column)[agg_col].mean().nlargest(n)
            elif metric == "max":
                grouped = df.groupby(column)[agg_col].max().nlargest(n)
            elif metric == "min":
                grouped = df.groupby(column)[agg_col].min().nsmallest(n)

            results = [
                {"value": str(val), "metric_value": round(float(metric_val), 2) if isinstance(metric_val, float) else metric_val}
                for val, metric_val in grouped.items()
            ]

            export_df = grouped.reset_index()
            export_df.columns = [column, f"{metric}_{agg_col}"]

            # Save export and return
            export_url = None
            if export_df is not None and len(export_df) > 0:
                os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
                timestamp = int(time.time())
                base_name = os.path.splitext(filename)[0]
                export_filename = f"{base_name}_top{n}_{column}_{timestamp}.csv"
                export_path = os.path.join(CHART_OUTPUT_DIR, export_filename)
                export_df.to_csv(export_path, index=False)
                export_url = f"/export/{export_filename}"

            return {
                "column": column,
                "metric": metric,
                "aggregated_by": agg_col,
                "n": n,
                "results": results,
                "export_url": export_url,
            }
        else:
            return {"error": f"Unsupported metric '{metric}'. Use 'count', 'sum', 'mean', 'max', or 'min'."}

        # Save export for count metric
        export_url = None
        if export_df is not None and len(export_df) > 0:
            os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
            timestamp = int(time.time())
            base_name = os.path.splitext(filename)[0]
            export_filename = f"{base_name}_top{n}_{column}_{timestamp}.csv"
            export_path = os.path.join(CHART_OUTPUT_DIR, export_filename)
            export_df.to_csv(export_path, index=False)
            export_url = f"/export/{export_filename}"

        return {
            "column": column,
            "metric": metric,
            "n": n,
            "results": results,
            "export_url": export_url,
        }

    except Exception as e:
        return {"error": f"Top N analysis failed: {str(e)}"}
