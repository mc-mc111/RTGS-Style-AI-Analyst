import pandas as pd
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
        column = step.get("column")
        details = step.get("details", {})
        
        print(f"Executing: {action} on column '{column or 'all'}'")
        
        try:
            if action == "remove_duplicates":
                df_cleaned.drop_duplicates(inplace=True)
            elif action == "convert_type" and column:
                new_type = details.get("new_type")
                # Handle potential errors during conversion
                df_cleaned[column] = pd.to_numeric(df_cleaned[column], errors='coerce') if new_type in ['int', 'float'] else df_cleaned[column]
                df_cleaned = df_cleaned.astype({column: new_type})
            elif action == "fill_missing" and column:
                strategy = details.get("strategy")
                if strategy == "mean":
                    fill_value = df_cleaned[column].mean()
                elif strategy == "median":
                    fill_value = df_cleaned[column].median()
                elif strategy == "mode":
                    fill_value = df_cleaned[column].mode()[0]
                else: # 'value' strategy
                    fill_value = details.get("fill_value", 0)
                df_cleaned[column].fillna(fill_value, inplace=True)
        
        except Exception as e:
            print(f"Could not execute step {step}. Error: {e}")
            
    return df_cleaned

def cleaning_node(state: GraphState) -> Dict[str, Any]:
    """Loads data and executes the AI-generated cleaning plan."""
    print("\n---EXECUTING DYNAMIC CLEANING NODE---")
    standardized_data_path = state['standardized_data_path']
    plan = state['cleaning_plan']

    df = pd.read_csv(standardized_data_path)
    print(f"Loaded {standardized_data_path}.")
    print(f"Received cleaning plan: {plan}")

    cleaned_df = execute_plan(df, plan)

    cleaned_data_path = "outputs/2_cleaned_data.csv"
    cleaned_df.to_csv(cleaned_data_path, index=False)
    print(f"Saved dynamically cleaned data to {cleaned_data_path}")

    return {
        "cleaned_data_path": cleaned_data_path,
        "log_messages": state['log_messages'] + ["Dynamic cleaning complete."]
    }