"""Filter tool — filters rows in a CSV by column value with various operators."""

import os
import time
import pandas as pd
import numpy as np


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")
CHART_OUTPUT_DIR = os.getenv("CHART_OUTPUT_DIR", "./outputs")


def filter_data(filename: str, column: str, operator: str, value) -> dict:
    """
    Filter rows in a CSV file based on a column condition.

    Args:
        filename: Name of the CSV file.
        column: Column name to filter on.
        operator: One of "eq", "gt", "lt", "gte", "lte", "contains".
        value: The value to compare against.

    Returns:
        Dictionary with filtered row count, preview, and export URL.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": f"File '{filename}' not found."}

        df = pd.read_csv(filepath)

        if column not in df.columns:
            return {"error": f"Column '{column}' not found. Available columns: {list(df.columns)}"}

        supported_operators = ["eq", "gt", "lt", "gte", "lte", "contains"]
        if operator not in supported_operators:
            return {"error": f"Unsupported operator '{operator}'. Use one of: {supported_operators}"}

        col_data = df[column]

        # Try to cast value for numeric comparisons
        if operator in ("gt", "lt", "gte", "lte"):
            try:
                value = float(value)
            except (ValueError, TypeError):
                return {"error": f"Value '{value}' cannot be converted to a number for operator '{operator}'."}

        # Apply filter
        if operator == "eq":
            if pd.api.types.is_numeric_dtype(col_data):
                try:
                    mask = col_data == float(value)
                except (ValueError, TypeError):
                    mask = col_data.astype(str) == str(value)
            else:
                mask = col_data.astype(str) == str(value)
        elif operator == "gt":
            mask = col_data > value
        elif operator == "lt":
            mask = col_data < value
        elif operator == "gte":
            mask = col_data >= value
        elif operator == "lte":
            mask = col_data <= value
        elif operator == "contains":
            mask = col_data.astype(str).str.contains(str(value), case=False, na=False)
        else:
            mask = pd.Series([False] * len(df))

        filtered_df = df[mask]
        preview = filtered_df.head(10).to_dict(orient="records")

        # Clean up NaN values for JSON serialization
        clean_preview = []
        for row in preview:
            clean_row = {}
            for k, v in row.items():
                if isinstance(v, float) and np.isnan(v):
                    clean_row[k] = None
                elif isinstance(v, (np.integer,)):
                    clean_row[k] = int(v)
                elif isinstance(v, (np.floating,)):
                    clean_row[k] = round(float(v), 4)
                else:
                    clean_row[k] = v
            clean_preview.append(clean_row)

        # Export filtered data to CSV
        export_url = None
        if len(filtered_df) > 0:
            os.makedirs(CHART_OUTPUT_DIR, exist_ok=True)
            timestamp = int(time.time())
            base_name = os.path.splitext(filename)[0]
            export_filename = f"{base_name}_filtered_{timestamp}.csv"
            export_path = os.path.join(CHART_OUTPUT_DIR, export_filename)
            filtered_df.to_csv(export_path, index=False)
            export_url = f"/export/{export_filename}"

        return {
            "column": column,
            "operator": operator,
            "value": str(value),
            "total_rows": len(df),
            "filtered_rows": len(filtered_df),
            "match_percentage": round(len(filtered_df) / len(df) * 100, 2) if len(df) > 0 else 0,
            "preview": clean_preview,
            "export_url": export_url,
        }

    except Exception as e:
        return {"error": f"Filter operation failed: {str(e)}"}
