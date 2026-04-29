"""Data Cleaner tool — automated data cleaning for CSV datasets."""

import os
import time
import pandas as pd
import numpy as np


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def clean_data(filename: str, operations: list = None) -> dict:
    """
    Clean a CSV dataset by performing various data cleaning operations.

    Args:
        filename: Name of the CSV file in the uploads directory.
        operations: List of cleaning operations to perform.
                   Options: "drop_duplicates", "fill_nulls", "drop_nulls",
                           "fix_dates", "strip_whitespace", "auto"
                   Defaults to ["auto"] which runs all safe operations.

    Returns:
        Dictionary with cleaning report and path to the cleaned file.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)
        if not os.path.exists(filepath):
            return {"error": f"File '{filename}' not found."}

        df = pd.read_csv(filepath)
        original_shape = df.shape
        report = []

        if operations is None or operations == [] or "auto" in operations:
            operations = ["strip_whitespace", "drop_duplicates", "fill_nulls", "fix_dates"]

        # Track changes
        changes = {}

        # 1. Strip whitespace from string columns
        if "strip_whitespace" in operations:
            str_cols = df.select_dtypes(include=["object"]).columns
            for col in str_cols:
                df[col] = df[col].astype(str).str.strip()
            report.append(f"Stripped whitespace from {len(str_cols)} text columns.")
            changes["whitespace_stripped"] = len(str_cols)

        # 2. Drop duplicate rows
        if "drop_duplicates" in operations:
            dupes = df.duplicated().sum()
            if dupes > 0:
                df = df.drop_duplicates()
                report.append(f"Removed {dupes} duplicate rows.")
            else:
                report.append("No duplicate rows found.")
            changes["duplicates_removed"] = int(dupes)

        # 3. Fill null values
        if "fill_nulls" in operations:
            null_counts = df.isnull().sum()
            total_nulls = int(null_counts.sum())
            if total_nulls > 0:
                # Numeric columns: fill with median
                numeric_cols = df.select_dtypes(include=[np.number]).columns
                for col in numeric_cols:
                    if df[col].isnull().any():
                        median_val = df[col].median()
                        df[col] = df[col].fillna(median_val)
                        report.append(f"Filled {int(null_counts[col])} nulls in '{col}' with median ({median_val:.2f}).")

                # Categorical columns: fill with mode
                cat_cols = df.select_dtypes(include=["object", "category"]).columns
                for col in cat_cols:
                    if df[col].isnull().any() or (df[col] == "nan").any():
                        mode_val = df[col].replace("nan", np.nan).mode()
                        if len(mode_val) > 0:
                            df[col] = df[col].replace("nan", np.nan).fillna(mode_val[0])
                            report.append(f"Filled nulls in '{col}' with mode ('{mode_val[0]}').")
            else:
                report.append("No null values found.")
            changes["nulls_filled"] = total_nulls

        # 4. Drop null rows (alternative to fill)
        if "drop_nulls" in operations:
            null_rows = df.isnull().any(axis=1).sum()
            if null_rows > 0:
                df = df.dropna()
                report.append(f"Dropped {null_rows} rows containing null values.")
            changes["null_rows_dropped"] = int(null_rows)

        # 5. Fix date columns
        if "fix_dates" in operations:
            date_cols_fixed = 0
            for col in df.columns:
                if df[col].dtype == "object":
                    sample = df[col].dropna().head(20)
                    date_like = sample.str.match(
                        r"^\d{4}[-/]\d{1,2}[-/]\d{1,2}|^\d{1,2}[-/]\d{1,2}[-/]\d{4}"
                    )
                    if date_like.mean() > 0.7:
                        try:
                            df[col] = pd.to_datetime(df[col], infer_datetime_format=True, errors="coerce")
                            date_cols_fixed += 1
                            report.append(f"Converted '{col}' to datetime format.")
                        except Exception:
                            pass
            changes["date_columns_fixed"] = date_cols_fixed

        # Save cleaned file
        base_name = os.path.splitext(filename)[0]
        cleaned_filename = f"{base_name}_cleaned.csv"
        cleaned_path = os.path.join(UPLOAD_DIR, cleaned_filename)
        df.to_csv(cleaned_path, index=False)

        return {
            "original_shape": {"rows": original_shape[0], "columns": original_shape[1]},
            "cleaned_shape": {"rows": len(df), "columns": len(df.columns)},
            "operations_performed": operations,
            "report": report,
            "changes": changes,
            "cleaned_filename": cleaned_filename,
            "message": f"Dataset cleaned and saved as '{cleaned_filename}'. Original: {original_shape[0]} rows → Cleaned: {len(df)} rows.",
        }

    except Exception as e:
        return {"error": f"Data cleaning failed: {str(e)}"}
