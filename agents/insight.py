import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from typing import Dict, Any
from collections import Counter

from rich.console import Console
from rich.table import Table

import nltk
from nltk.corpus import stopwords

from state import GraphState
from agents.profiler import get_data_profile
import google.generativeai as genai
from agents.logger import logger

try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

console = Console()

def generate_insight_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Asks the AI to suggest a good analysis for the given data."""
    logger.debug("Generating insight plan with AI...")

    prompt = f"""
    You are a data analyst. Based on the profile of the CLEANED dataset below,
    suggest a single, valuable insight to generate.

    **Instructions:**
    1.  **For Text Data:** If there is a primary text column (like 'review_text'), the most valuable insight is a `word_frequency` analysis.
    2.  **For Numerical/Categorical Data:** Suggest a plan with `group_and_aggregate`.

    **Allowed Plans:**
    - Plan A (For Text): {{"action": "word_frequency", "text_column": "column_name"}}
    - Plan B (For Other Data): {{"action": "group_and_aggregate", "groupby_column": "cat_col", "agg_column": "num_col", "agg_function": "mean"}}

    Data Profile:
    {json.dumps(profile, indent=2)}

    Generate the most appropriate JSON insight plan now.
    """
    
    generation_config = {"temperature": 0.0, "response_mime_type": "application/json"}
    model = genai.GenerativeModel("gemini-1.5-flash-latest", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error generating insight plan: {e}")
        return {}

def insight_node(state: GraphState) -> Dict[str, Any]:
    """Dynamically generates insights based on an AI-driven plan."""
    logger.info("    - Executing: Dynamic Insight Node")
    cleaned_data_path = state['cleaned_data_path']
    
    try:
        df = pd.read_csv(cleaned_data_path)
        if df.empty:
            logger.warning("Cleaned data is empty. No insights generated.")
            return {"insights": {"summary": "Cleaned data was empty."}}
    except pd.errors.EmptyDataError:
        logger.warning("Cleaned data file is empty. No insights generated.")
        return {"insights": {"summary": "Cleaned data file was empty."}}
    
    profile = get_data_profile(cleaned_data_path)
    if not profile.get("columns"):
        logger.warning("Data profile is empty. No insights can be generated.")
        return {"insights": {"summary": "Data profile was empty."}}
        
    insight_plan = generate_insight_plan(profile)
    action = insight_plan.get("action")

    try:
        title = "Insight Report"
        plot_path = f"outputs/insights/final_insight_plot.png"
        os.makedirs("outputs/insights", exist_ok=True)

        if action == "word_frequency":
            text_col = insight_plan["text_column"]
            logger.info(f"    Insight: Calculating word frequency for column '{text_col}'.")
            
            stop_words = set(stopwords.words('english'))
            words = ' '.join(df[text_col].dropna()).split()
            word_counts = Counter(word for word in words if word not in stop_words)
            insight_data = word_counts.most_common(15)
            
            title = f"Top 15 Most Common Words in '{text_col}'"
            table = Table(title=title)
            table.add_column("Word", style="cyan")
            table.add_column("Count", style="magenta", justify="right")
            for word, count in insight_data:
                table.add_row(word, str(count))
            console.print(table)
            
            plt.figure(figsize=(12, 8))
            pd.DataFrame(insight_data, columns=['Word', 'Count']).set_index('Word').plot.bar(color='cyan', legend=False)
            plt.title(title, fontsize=16)
        
        elif action == "group_and_aggregate":
            groupby_col = insight_plan["groupby_column"]
            agg_col = insight_plan["agg_column"]
            agg_func = insight_plan["agg_function"]
            logger.info(f"    Insight: Group by '{groupby_col}', calculate '{agg_func}' of '{agg_col}'.")
            
            # --- START: THIS IS THE RESTORED LOGIC ---
            insight_data = df.groupby(groupby_col)[agg_col].agg(agg_func).sort_values(ascending=False).head(15)
            
            title = f"Top 15 {agg_func.capitalize()} of {agg_col.title()} by {groupby_col.title()}"
            table = Table(title=title)
            table.add_column(groupby_col.title(), style="cyan")
            table.add_column(f"{agg_func.capitalize()}", style="magenta", justify="right")
            for index, value in insight_data.items():
                table.add_row(str(index), f"{value:,.2f}")
            console.print(table)

            plt.figure(figsize=(12, 8))
            insight_data.plot(kind='bar', color='teal')
            plt.title(title, fontsize=16)
            # --- END: THIS IS THE RESTORED LOGIC ---

        else:
            logger.warning("AI did not suggest a valid insight plan.")
            return {"insights": {}}

        # Common plotting code
        plt.ylabel("Value")
        plt.xlabel(None)
        plt.xticks(rotation=45, ha='right')
        plt.tight_layout()
        plt.savefig(plot_path)
        logger.debug(f"Saved plot to {plot_path}")

        return {"insights": {"plot_path": plot_path, "summary": title}}
        
    except Exception as e:
        logger.error(f"Error executing insight plan: {e}", exc_info=True)
        return {"insights": {}}