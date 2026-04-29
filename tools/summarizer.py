"""Summarizer tool — computes descriptive statistics for a CSV dataset."""

import os
import pandas as pd
import numpy as np


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def summarize_data(filename: str, columns: list = None) -> dict:
    """
    Compute summary statistics for a CSV file.

    Args:
        filename: Name of the CSV file in the uploads directory.
        columns: Optional list of specific columns to summarize. If None, all columns are used.

    Returns:
        Dictionary with numeric stats, categorical value counts, null percentages,
        duplicate count, and memory usage.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": f"File '{filename}' not found."}

        df = pd.read_csv(filepath)

        if columns:
            valid_cols = [c for c in columns if c in df.columns]
            if not valid_cols:
                return {"error": f"None of the specified columns exist. Available: {list(df.columns)}"}
            df_subset = df[valid_cols]
        else:
            if len(df.columns) > 10:
                return {
                    "total_rows": len(df),
                    "total_columns": len(df.columns),
                    "all_columns": list(df.columns),
                    "error": f"Dataset is too wide ({len(df.columns)} columns) to summarize all at once. Please specify specific 'columns' you want to summarize to avoid rate limits."
                }
            df_subset = df

        result = {
            "total_rows": len(df),
            "total_columns": len(df.columns),
            "all_columns": list(df.columns),
        }

        # Numeric column statistics
        numeric_cols = df_subset.select_dtypes(include=[np.number])
        if not numeric_cols.empty:
            stats = numeric_cols.describe().to_dict()
            # Convert numpy types to native Python types for JSON serialization
            clean_stats = {}
            for col, col_stats in stats.items():
                clean_stats[col] = {
                    k: round(float(v), 4) if isinstance(v, (np.floating, float)) else int(v) if isinstance(v, (np.integer,)) else v
                    for k, v in col_stats.items()
                }
            result["numeric_stats"] = clean_stats

        # Categorical column value counts (top 10 per column)
        categorical_cols = df_subset.select_dtypes(include=["object", "category"])
        if not categorical_cols.empty:
            cat_stats = {}
            for col in categorical_cols.columns:
                value_counts = df[col].value_counts().head(10)
                cat_stats[col] = {
                    "unique_values": int(df[col].nunique()),
                    "top_values": {str(k): int(v) for k, v in value_counts.items()},
                    "most_common": str(value_counts.index[0]) if len(value_counts) > 0 else None,
                }
            result["categorical_stats"] = cat_stats

        # Null percentage per column
        null_pct = (df_subset.isnull().sum() / len(df) * 100).round(2)
        result["null_percentage"] = {col: float(pct) for col, pct in null_pct.items()}

        # Duplicate rows
        result["duplicate_rows"] = int(df.duplicated().sum())

        # Memory usage
        mem_usage = df.memory_usage(deep=True).sum()
        result["memory_usage_mb"] = round(mem_usage / (1024 * 1024), 2)

        return result

    except Exception as e:
        return {"error": f"Summarization failed: {str(e)}"}
