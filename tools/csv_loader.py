"""CSV Loader tool — loads and validates a CSV file, returning schema information."""

import os
import pandas as pd


UPLOAD_DIR = os.getenv("UPLOAD_DIR", "./uploads")


def load_csv(filename: str) -> dict:
    """
    Load a CSV file from the uploads directory and return its schema info.

    Args:
        filename: Name of the CSV file in the uploads directory.

    Returns:
        Dictionary with success status, row/column counts, dtypes, preview, and missing values.
    """
    try:
        filepath = os.path.join(UPLOAD_DIR, filename)

        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filename}' not found in uploads directory.")

        file_size = os.path.getsize(filepath)
        if file_size == 0:
            return {"success": False, "error": "The uploaded file is empty (0 bytes)."}

        # Try reading with different encodings
        for encoding in ["utf-8", "latin-1", "cp1252"]:
            try:
                df = pd.read_csv(filepath, encoding=encoding)
                break
            except UnicodeDecodeError:
                continue
        else:
            return {"success": False, "error": "Could not decode the file. Supported encodings: utf-8, latin-1, cp1252."}

        if df.empty:
            return {"success": False, "error": "The CSV file has no data rows."}

        # Build dtype mapping (convert numpy types to strings for JSON serialization)
        dtypes = {col: str(dtype) for col, dtype in df.dtypes.items()}

        # Preview: first 5 rows as list of dicts
        preview = df.head(5).to_dict(orient="records")

        # Missing values per column
        missing_values = df.isnull().sum().to_dict()
        missing_values = {col: int(count) for col, count in missing_values.items()}

        return {
            "success": True,
            "rows": len(df),
            "columns": list(df.columns),
            "dtypes": dtypes,
            "preview": preview,
            "missing_values": missing_values,
        }

    except FileNotFoundError as e:
        return {"success": False, "error": str(e)}
    except pd.errors.EmptyDataError:
        return {"success": False, "error": "The CSV file is empty or has no parseable data."}
    except Exception as e:
        return {"success": False, "error": f"Failed to load CSV: {str(e)}"}
