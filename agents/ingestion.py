import pandas as pd
from typing import Dict, Any
from state import GraphState

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Converts all column names to snake_case."""
    cols = df.columns
    new_cols = []
    for col in cols:
        new_col = col.lower().strip().replace(' ', '_')
        new_cols.append(new_col)
    df.columns = new_cols
    return df

def ingestion_node(state: GraphState) -> Dict[str, Any]:
    """
    Robustly reads potentially malformed CSVs and standardizes them.
    """
    print("---EXECUTING INGESTION NODE---")
    raw_data_path = state['raw_data_path']

    # --- START: UPGRADED CSV READING LOGIC ---
    # For messy CSVs like the Amazon one, we enforce a structure.
    # This reads only the first two columns and names them, preventing parsing errors.
    try:
        print("Attempting robust read for potentially malformed CSV...")
        df = pd.read_csv(
            raw_data_path,
            encoding='latin-1',  # Use latin-1 which is common for this type of file
            header=None,         # The file has no header row
            usecols=[0, 1],      # Read only the first two columns
            names=['review_text', 'decision'] # Name them explicitly
        )
        print(f"Successfully loaded {raw_data_path} with robust parser.")
    except Exception as e:
        print(f"Robust parser failed: {e}. Falling back to standard parser.")
        # Fallback for well-formed CSVs
        df = pd.read_csv(raw_data_path, encoding='latin-1')
    # --- END: UPGRADED CSV READING LOGIC ---

    standardized_df = standardize_column_names(df)
    print("Standardized column names.")

    standardized_data_path = "outputs/1_standardized_data.csv"
    standardized_df.to_csv(standardized_data_path, index=False)
    print(f"Saved standardized data to {standardized_data_path}")

    return {
        "standardized_data_path": standardized_data_path,
        "log_messages": state.get('log_messages', []) + ["Ingestion complete."]
    }