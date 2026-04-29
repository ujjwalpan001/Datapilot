"""Join Datasets tool — merge two CSV files on a common column."""

import os
import pandas as pd


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def join_data(file1: str, file2: str, join_column: str, join_type: str = "inner") -> dict:
    """
    Join two CSV datasets on a common column.

    Args:
        file1: Name of the first CSV file.
        file2: Name of the second CSV file.
        join_column: Column name to join on (must exist in both files).
        join_type: Type of join — "inner", "left", "right", or "outer".

    Returns:
        Dictionary with merged preview, row counts, and saved filename.
    """
    try:
        path1 = os.path.join(UPLOAD_DIR, file1)
        path2 = os.path.join(UPLOAD_DIR, file2)

        if not os.path.exists(path1):
            return {"error": f"File '{file1}' not found."}
        if not os.path.exists(path2):
            return {"error": f"File '{file2}' not found."}

        df1 = pd.read_csv(path1)
        df2 = pd.read_csv(path2)

        if join_column not in df1.columns:
            return {"error": f"Column '{join_column}' not found in '{file1}'. Available: {list(df1.columns)}"}
        if join_column not in df2.columns:
            return {"error": f"Column '{join_column}' not found in '{file2}'. Available: {list(df2.columns)}"}

        valid_types = ["inner", "left", "right", "outer"]
        if join_type not in valid_types:
            return {"error": f"Invalid join_type '{join_type}'. Use one of: {valid_types}"}

        # Perform merge
        merged = pd.merge(df1, df2, on=join_column, how=join_type, suffixes=("_file1", "_file2"))

        # Save merged result
        base1 = os.path.splitext(file1)[0]
        base2 = os.path.splitext(file2)[0]
        merged_filename = f"{base1}_{base2}_merged.csv"
        merged_path = os.path.join(UPLOAD_DIR, merged_filename)
        merged.to_csv(merged_path, index=False)

        # Preview
        preview = merged.head(10).to_dict(orient="records")

        # Clean NaN for JSON
        import numpy as np
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

        return {
            "file1": file1,
            "file1_rows": len(df1),
            "file1_columns": list(df1.columns),
            "file2": file2,
            "file2_rows": len(df2),
            "file2_columns": list(df2.columns),
            "join_column": join_column,
            "join_type": join_type,
            "merged_rows": len(merged),
            "merged_columns": list(merged.columns),
            "merged_filename": merged_filename,
            "preview": clean_preview,
            "message": f"Successfully merged '{file1}' ({len(df1)} rows) and '{file2}' ({len(df2)} rows) on '{join_column}' → {len(merged)} rows. Saved as '{merged_filename}'.",
        }

    except Exception as e:
        return {"error": f"Join operation failed: {str(e)}"}
