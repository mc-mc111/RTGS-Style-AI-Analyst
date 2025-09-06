import pandas as pd
from typing import Dict, Any
from state import GraphState

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Converts all column names to snake_case."""
    cols = df.columns
    new_cols = []
    for col in cols:
        new_col = col.lower().strip()
        new_col = ''.join(e for e in new_col if e.isalnum() or e == ' ')
        new_col = new_col.replace(' ', '_')
        new_cols.append(new_col)
    df.columns = new_cols
    return df

def ingestion_node(state: GraphState) -> Dict[str, Any]:
    """Reads data, standardizes it, and saves it to a new location."""
    print("---EXECUTING INGESTION NODE---")
    raw_data_path = state['raw_data_path']

    df = pd.read_csv(raw_data_path)
    print(f"Loaded {raw_data_path} with {len(df)} rows.")

    standardized_df = standardize_column_names(df)
    print("Standardized column names.")

    standardized_data_path = "outputs/1_standardized_data.csv"
    standardized_df.to_csv(standardized_data_path, index=False)
    print(f"Saved standardized data to {standardized_data_path}")

    return {
        "standardized_data_path": standardized_data_path,
        "log_messages": state.get('log_messages', []) + ["Ingestion complete."]
    }