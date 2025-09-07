import pandas as pd
import re
import string
from typing import Dict, Any

# --- START: NEW IMPORTS FOR ML PREPROCESSING ---
from sklearn.preprocessing import MinMaxScaler, StandardScaler
# --- END: NEW IMPORTS ---

from state import GraphState
from agents.logger import logger

# --- HELPER FUNCTION LIBRARY (POWER TOOLS) ---
def _calculate_year_span(series: pd.Series) -> pd.Series:
    """
    Calculates the number of years in a string like '2023-24' or '2023'.
    This is a specialized "power tool" for complex transformations.
    """
    def span_from_string(s):
        s = str(s).strip()
        if '-' in s:
            try:
                parts = s.split('-')
                start_str = parts[0]
                end_str = parts[1]
                start_year = int(start_str)
                if len(end_str) == 2:
                    end_year = int(str(start_year)[:2] + end_str)
                else:
                    end_year = int(end_str)
                if end_year < start_year:
                    end_year += 100
                return end_year - start_year + 1
            except (ValueError, IndexError):
                return 1
        elif s.isdigit() and len(s) == 4:
            return 1
        return 1
    return series.apply(span_from_string)
# --- END: HELPER FUNCTION LIBRARY ---


def execute_plan(df: pd.DataFrame, plan: Dict[str, Any]) -> pd.DataFrame:
    """Dynamically executes the steps from the AI-generated cleaning plan."""
    df_cleaned = df.copy()
    
    custom_functions = {
        "calculate_year_span": _calculate_year_span
    }
    
    if "steps" not in plan or not isinstance(plan["steps"], list):
        logger.warning("Cleaning plan is malformed. Skipping cleaning.")
        return df_cleaned
        
    for step in plan["steps"]:
        action = step.get("action")
        details = step.get("details", {})
        column = step.get("column") or details.get("column")
        reason = step.get("reason", "No reason provided.")

        logger.debug(f"Action: {action}, Column: '{column or 'all'}', Reason: {reason}")
        
        try:
            if action == "remove_duplicates":
                df_cleaned.drop_duplicates(inplace=True)
            
            elif action == "remove_column" and column:
                df_cleaned.drop(columns=[column], inplace=True)
            
            elif action == "clean_text" and column:
                temp_col = df_cleaned[column].astype(str).fillna('')
                operations = details.get("operations", [])
                if "lowercase" in operations:
                    temp_col = temp_col.str.lower()
                if "remove_punctuation" in operations:
                    temp_col = temp_col.str.replace(f'[{re.escape(string.punctuation)}]', '', regex=True)
                if "remove_digits" in operations:
                    temp_col = temp_col.str.replace(r'\d+', '', regex=True)
                if "remove_non_ascii" in operations:
                    temp_col = temp_col.str.encode('ascii', 'ignore').str.decode('ascii')
                df_cleaned[column] = temp_col

            elif action == "clean_categorical" and column:
                valid_values = details.get("valid_values", [])
                if valid_values:
                    df_cleaned = df_cleaned[df_cleaned[column].isin(valid_values)]

            elif action == "encode_binary" and column:
                positive_value = details.get("positive_value")
                if positive_value:
                    df_cleaned[column] = df_cleaned[column].apply(lambda x: 1 if str(x).lower() == str(positive_value).lower() else 0)
                    logger.debug(f"Binary encoded column '{column}' with '{positive_value}' as 1.")

            elif action == "scale_numeric" and column:
                strategy = details.get("strategy")
                df_cleaned[column] = pd.to_numeric(df_cleaned[column], errors='coerce')
                
                col_data = df_cleaned[[column]].dropna()
                
                if col_data.empty:
                    logger.warning(f"Column '{column}' contains no valid data to scale. Skipping scaling step.")
                    continue
                
                if strategy == "min_max":
                    scaler = MinMaxScaler()
                elif strategy == "standard":
                    scaler = StandardScaler()
                else:
                    logger.warning(f"Unknown scaling strategy '{strategy}'. Skipping.")
                    continue
                
                # --- START: FINAL FIX for FutureWarning ---
                # Ensure the column is float type *before* assigning scaled float values.
                df_cleaned[column] = df_cleaned[column].astype(float)
                # --- END: FINAL FIX ---

                scaled_data = scaler.fit_transform(col_data)
                df_cleaned.loc[col_data.index, column] = scaled_data
                logger.debug(f"Applied '{strategy}' scaling to column '{column}'.")

            elif action == "convert_type" and column:
                new_type = details.get("new_type")
                pre_processing_steps = details.get("pre_processing", [])
                temp_col = df_cleaned[column].astype(str)
                if "remove_currency" in pre_processing_steps:
                    temp_col = temp_col.str.replace('$', '', regex=False)
                if "remove_commas" in pre_processing_steps:
                    temp_col = temp_col.str.replace(',', '', regex=False)
                if "remove_brackets" in pre_processing_steps:
                    temp_col = temp_col.str.replace(r'\[.*?\]', '', regex=True)
                df_cleaned[column] = pd.to_numeric(temp_col, errors='coerce')
                if df_cleaned[column].isnull().any():
                    df_cleaned[column] = df_cleaned[column].fillna(0)
                if new_type in ['int64', 'float64']:
                    df_cleaned = df_cleaned.astype({column: new_type})
            
            elif action == "fill_missing" and column:
                strategy = details.get("strategy")
                fill_value = 0
                if strategy == "mean":
                    fill_value = df_cleaned[column].mean()
                elif strategy == "median":
                    fill_value = df_cleaned[column].median()
                elif strategy == "mode":
                    fill_value = df_cleaned[column].mode()[0]
                else:
                    fill_value = details.get("fill_value", 0)
                df_cleaned[column] = df_cleaned[column].fillna(fill_value)
            
            elif action == "create_feature":
                new_col = details.get("new_column_name")
                expression = details.get("expression")
                if new_col and expression:
                    df_cleaned[new_col] = df_cleaned.eval(expression)
            
            elif action == "execute_custom_function" and column:
                func_name = details.get("function_name")
                source_col = details.get("source_column")
                if func_name in custom_functions and source_col in df_cleaned.columns:
                    func_to_run = custom_functions[func_name]
                    df_cleaned[column] = func_to_run(df_cleaned[source_col])
                    logger.debug(f"Successfully executed custom function '{func_name}'.")
                else:
                    logger.warning(f"Custom function '{func_name}' not found in library or source column not found.")

        except Exception as e:
            logger.error(f"Could not execute step {step}. Error: {e}", exc_info=True)
            
    return df_cleaned

def cleaning_node(state: GraphState) -> Dict[str, Any]:
    """Loads data and executes the AI-generated cleaning and preprocessing plan."""
    logger.info("    - Executing: Dynamic Cleaning & Preprocessing Node")
    standardized_data_path = state['standardized_data_path']
    plan = state['cleaning_plan']

    try:
        df = pd.read_csv(standardized_data_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(standardized_data_path, encoding='latin-1')
    
    logger.debug(f"Loaded {standardized_data_path}.")
    
    cleaned_df = execute_plan(df, plan)

    cleaned_data_path = "outputs/2_cleaned_data.csv"
    cleaned_df.to_csv(cleaned_data_path, index=False)
    logger.debug(f"Saved preprocessed data to {cleaned_data_path}")

    return {
        "cleaned_data_path": cleaned_data_path,
        "log_messages": state.get('log_messages', []) + ["Dynamic preprocessing complete."]
    }