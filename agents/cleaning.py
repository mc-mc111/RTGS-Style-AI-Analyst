import pandas as pd
import re
import string
from typing import Dict, Any
from state import GraphState

def execute_plan(df: pd.DataFrame, plan: Dict[str, Any]) -> pd.DataFrame:
    """Dynamically executes the steps from the AI-generated cleaning plan."""
    df_cleaned = df.copy()
    
    if "steps" not in plan or not isinstance(plan["steps"], list):
        print("Warning: Cleaning plan is malformed. Skipping cleaning.")
        return df_cleaned
        
    for step in plan["steps"]:
        action = step.get("action")
        details = step.get("details", {})
        column = step.get("column") or details.get("column")
        reason = step.get("reason", "No reason provided.")

        log_message = f"Action: {action}, Column: '{column or 'all'}', Reason: {reason}"
        print(log_message)
        
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
                    df_cleaned[column] = df_cleaned[column].fillna(0) # Switched to non-inplace
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
                
                # --- FIX IS HERE: Switched to the recommended, non-inplace method ---
                df_cleaned[column] = df_cleaned[column].fillna(fill_value)
            
            elif action == "create_feature":
                new_col = details.get("new_column_name")
                expression = details.get("expression")
                if new_col and expression:
                    df_cleaned[new_col] = df_cleaned.eval(expression)

        except Exception as e:
            print(f"Could not execute step {step}. Error: {e}")
            
    return df_cleaned

def cleaning_node(state: GraphState) -> Dict[str, Any]:
    """Loads data and executes the AI-generated cleaning plan."""
    print("\n---EXECUTING DYNAMIC CLEANING NODE---")
    standardized_data_path = state['standardized_data_path']
    plan = state['cleaning_plan']

    # Using latin-1 as a robust fallback for tricky files
    try:
        df = pd.read_csv(standardized_data_path, encoding='utf-8')
    except UnicodeDecodeError:
        df = pd.read_csv(standardized_data_path, encoding='latin-1')
    
    print(f"Loaded {standardized_data_path}.")
    
    cleaned_df = execute_plan(df, plan)

    cleaned_data_path = "outputs/2_cleaned_data.csv"
    cleaned_df.to_csv(cleaned_data_path, index=False)
    print(f"Saved dynamically cleaned data to {cleaned_data_path}")

    return {
        "cleaned_data_path": cleaned_data_path,
        "log_messages": state.get('log_messages', []) + ["Dynamic cleaning complete."]
    }