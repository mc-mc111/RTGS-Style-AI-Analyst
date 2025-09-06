import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from typing import Dict, Any

from rich.console import Console
from rich.table import Table

from state import GraphState
from agents.profiler import get_data_profile # We need the profiler again
import google.generativeai as genai

console = Console()

def generate_insight_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Asks the AI to suggest a good analysis for the given data."""
    print("---GENERATING INSIGHT PLAN WITH AI---")

    prompt = f"""
    You are a data analyst. Based on the profile of the CLEANED dataset below,
    suggest a single, valuable insight to generate.

    The plan should be a JSON object with three keys:
    - "groupby_column": A categorical column to group the data by.
    - "agg_column": A numerical column to perform a calculation on.
    - "agg_function": The function to use (e.g., "sum", "mean", "count").

    Choose the most insightful combination. For example, grouping by 'gender' and finding the 'mean' of 'bmi' is a good insight.

    Data Profile:
    {json.dumps(profile, indent=2)}

    Generate the JSON insight plan now.
    """
    
    generation_config = {"temperature": 0.0, "response_mime_type": "application/json"}
    model = genai.GenerativeModel("gemini-1.5-flash-latest", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        print(f"Error generating insight plan: {e}")
        return {}


def insight_node(state: GraphState) -> Dict[str, Any]:
    """
    Dynamically generates and displays insights based on an AI-driven plan.
    """
    print("\n---EXECUTING DYNAMIC INSIGHT NODE---")
    cleaned_data_path = state['cleaned_data_path']
    df = pd.read_csv(cleaned_data_path)
    
    # Profile the CLEAN data to decide what to analyze
    profile = get_data_profile(cleaned_data_path)
    insight_plan = generate_insight_plan(profile)

    if not all(k in insight_plan for k in ["groupby_column", "agg_column", "agg_function"]):
        print("Could not generate a valid insight plan from the AI.")
        return {"insights": {}}

    groupby_col = insight_plan["groupby_column"]
    agg_col = insight_plan["agg_column"]
    agg_func = insight_plan["agg_function"]

    print(f"AI Insight Plan: Group by '{groupby_col}', calculate '{agg_func}' of '{agg_col}'.")

    # Execute the dynamic insight plan
    try:
        insight_data = df.groupby(groupby_col)[agg_col].agg(agg_func).sort_values(ascending=False)

        # Display the table
        title = f"{agg_func.capitalize()} of {agg_col.replace('_', ' ').title()} by {groupby_col.replace('_', ' ').title()}"
        table = Table(title=title)
        table.add_column(groupby_col.title(), style="cyan")
        table.add_column(f"{agg_func.capitalize()} of {agg_col.title()}", style="magenta", justify="right")

        for index, value in insight_data.items():
            table.add_row(str(index), f"{value:,.2f}")
        
        console.print(table)

        # Generate and save the plot
        plt.figure(figsize=(12, 8))
        insight_data.plot(kind='bar', color='teal')
        plt.title(title, fontsize=16)
        plt.ylabel(f"{agg_func.capitalize()} of {agg_col.title()}")
        plt.xlabel(groupby_col.title())
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        
        os.makedirs("outputs/insights", exist_ok=True)
        plot_path = f"outputs/insights/dynamic_plot.png"
        plt.savefig(plot_path)
        print(f"Saved plot to {plot_path}")

        return {"insights": {"plot_path": plot_path}}
    except Exception as e:
        print(f"Error executing insight plan: {e}")
        return {"insights": {}}
