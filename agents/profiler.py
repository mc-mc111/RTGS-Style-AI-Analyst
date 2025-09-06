import pandas as pd
import os
from typing import Dict, Any

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
            col_data.update({
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "std_dev": float(df[col].std())
            })
        else: # Assumed categorical/object
            col_data["unique_values_count"] = unique_count
            top_values = df[col].value_counts().nlargest(5).to_dict()
            col_data["top_5_values"] = {str(k): int(v) for k, v in top_values.items()}
            
        profile[col] = col_data
    return {"total_rows": total_rows, "columns": profile}

def get_data_profile(file_path: str) -> Dict[str, Any]:
    """Checks file size and generates a profile for the dataset."""
    print(f"\n---PROFILING DATA: {file_path}---")
    file_size_mb = os.path.getsize(file_path) / (1024 * 1024)
    
    # Conditional logic for scalability
    if file_size_mb < 100:
        print("File size is small (<100MB). Using in-memory profiling.")
        df = pd.read_csv(file_path)
    else:
        # For a prototype, we'll still use in-memory but show the logic path
        print("File size is large (>=100MB). Using in-memory for prototype, but would use chunking in production.")
        df = pd.read_csv(file_path)
        
    profile = profile_in_memory(df)
    print("Profiling complete.")
    return profile