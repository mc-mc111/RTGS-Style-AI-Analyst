import pandas as pd
import os
from typing import Dict, Any
import warnings # <-- Import the warnings library
from agents.logger import logger


def profile_in_memory(df: pd.DataFrame) -> Dict[str, Any]:
    """Generates a statistical profile for a DataFrame."""
    profile = {}
    total_rows = len(df)
    
    for col in df.columns:
        unique_count = df[col].nunique()
        
        # Identifier Rule: If a column has nearly all unique values, it's likely an ID.
        if total_rows > 0 and unique_count / total_rows > 0.99:
            profile[col] = {"data_type": "identifier", "unique_count": unique_count}
            continue

        col_data = {
            "data_type": str(df[col].dtype),
            "missing_values_count": int(df[col].isnull().sum()),
        }

        if pd.api.types.is_numeric_dtype(df[col]):
            # --- START: FINAL FIX ---
            # Suppress RuntimeWarning that can occur when calculating std dev on a
            # column with NaN values, which is expected during profiling.
            with warnings.catch_warnings():
                warnings.simplefilter("ignore", RuntimeWarning)
                col_data.update({
                    "min": float(df[col].min()),
                    "max": float(df[col].max()),
                    "mean": float(df[col].mean()),
                    "std_dev": float(df[col].std())
                })
            # --- END: FINAL FIX ---
        else: # Assumed categorical/object
            col_data["unique_values_count"] = unique_count
            top_values = df[col].value_counts().nlargest(5).to_dict()
            col_data["top_5_values"] = {str(k): int(v) for k, v in top_values.items()}
            
        profile[col] = col_data
    return {"total_rows": total_rows, "columns": profile}

def get_data_profile(file_path: str) -> Dict[str, Any]:
    """Checks file size and generates a profile for the dataset."""
    logger.debug(f"Profiling data from: {file_path}")
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    df = None
    try:
        if file_size_mb < 100:
            logger.debug("File size is small (<100MB). Using in-memory profiling.")
            df = pd.read_csv(file_path, encoding='latin-1')
        else:
            logger.debug("File size is large (>=100MB). Using in-memory for prototype.")
            df = pd.read_csv(file_path, encoding='latin-1')
    except Exception as e:
        logger.error(f"Profiler failed to read {file_path}. Error: {e}")
        # Return an empty profile if the file can't be read at all
        return {"total_rows": 0, "columns": {}}
        
    profile = profile_in_memory(df)
    logger.debug("Profiling complete.")
    return profile