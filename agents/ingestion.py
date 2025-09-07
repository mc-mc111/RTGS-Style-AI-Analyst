import pandas as pd
import re
from typing import Dict, Any
from state import GraphState
from agents.logger import logger

def standardize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """Converts all column names to a clean snake_case format."""
    cols = df.columns
    new_cols = []
    for col in cols:
        clean_col = str(col).lower().strip()
        clean_col = re.sub(r'[^a-z0-9_]+', '', clean_col)
        new_cols.append(clean_col)
    df.columns = new_cols
    return df

def ingestion_node(state: GraphState) -> Dict[str, Any]:
    """
    Uses a hybrid approach: tries a fast, standard read first, then falls back
    to a specialized parser if it detects a malformed text file.
    """
    logger.info("    - Executing: Hybrid Ingestion Node")
    raw_data_path = state['raw_data_path']

    df = None
    try:
        # --- STEP 1: THE FAST PATH for 99% of files ---
        df = pd.read_csv(
            raw_data_path,
            encoding='latin-1',
            on_bad_lines='skip',
            engine='python'
        )
        logger.debug(f"Initial read successful. DataFrame shape: {df.shape}")

        # --- STEP 2: THE CHECK for the broken Amazon file edge case ---
        # Heuristic: If there's only one column and its name contains "review",
        # it's highly likely to be the malformed Amazon file.
        if df.shape[1] == 1 and 'review' in str(df.columns[0]).lower():
            logger.warning("Malformed CSV detected (single column with 'review' in name). Applying specialized parser...")
            
            # --- STEP 3: THE ROBUST FALLBACK ---
            df = pd.read_csv(
                raw_data_path,
                encoding='latin-1',
                header=None,
                usecols=[0, 1],
                names=['review_text', 'decision'],
                on_bad_lines='skip',
                engine='python'
            )
            # We need to skip the original header row which is now read as data
            df = df.iloc[1:].reset_index(drop=True)
            logger.debug("Specialized parser applied successfully.")

    except Exception as e:
        logger.critical(f"Fatal error during ingestion: {e}", exc_info=True)
        raise e

    # Final cleanup and standardization
    df.dropna(axis=1, how='all', inplace=True)
    standardized_df = standardize_column_names(df)
    
    # Rename for better AI context only if it was the Amazon file
    if 'uncleanedreview' in standardized_df.columns:
        standardized_df.rename(columns={'uncleanedreview': 'review_text'}, inplace=True)

    logger.debug("Standardized and cleaned columns.")

    standardized_data_path = "outputs/1_standardized_data.csv"
    standardized_df.to_csv(standardized_data_path, index=False)
    logger.debug(f"Saved standardized data to {standardized_data_path}")

    return {
        "standardized_data_path": standardized_data_path,
        "log_messages": state.get('log_messages', []) + ["Hybrid ingestion complete."]
    }