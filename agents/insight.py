import pandas as pd
import matplotlib.pyplot as plt
import os
import json
from typing import Dict, Any
from collections import Counter

from rich.console import Console
from rich.table import Table

# NLTK for stop words
import nltk
from nltk.corpus import stopwords

from state import GraphState
from agents.profiler import get_data_profile
import google.generativeai as genai

# Download stopwords once
try:
    stopwords.words('english')
except LookupError:
    nltk.download('stopwords')

console = Console()

def generate_insight_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Asks the AI to suggest a good analysis for the given data."""
    print("---GENERATING INSIGHT PLAN WITH AI---")

    prompt = f"""
    You are a data analyst. Based on the profile of the CLEANED dataset below,
    suggest a single, valuable insight to generate.

    **Instructions:**
    1.  **For Text Data:** If there is a primary text column (like 'review_text'), the most valuable insight is a `word_frequency` analysis.
    2.  **For Numerical/Categorical Data:** Suggest a plan with `groupby_column`, `agg_column`, and `agg_function`.

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
        print(f"Error generating insight plan: {e}")
        return {}

def insight_node(state: GraphState) -> Dict[str, Any]:
    """Dynamically generates insights based on an AI-driven plan."""
    print("\n---EXECUTING DYNAMIC INSIGHT NODE---")
    cleaned_data_path = state['cleaned_data_path']
    
    try:
        df = pd.read_csv(cleaned_data_path)
        if df.empty:
            print("Cleaned data is empty. No insights generated.")
            return {"insights": {}}
    except pd.errors.EmptyDataError:
        print("Cleaned data file is empty. No insights generated.")
        return {"insights": {}}
    
    profile = get_data_profile(cleaned_data_path)
    if not profile.get("columns"):
        print("Data profile is empty. No insights can be generated.")
        return {"insights": {}}
        
    insight_plan = generate_insight_plan(profile)
    action = insight_plan.get("action")

    try:
        if action == "word_frequency":
            text_col = insight_plan["text_column"]
            print(f"AI Insight Plan: Calculate word frequency for column '{text_col}'.")
            
            stop_words = set(stopwords.words('english'))
            words = ' '.join(df[text_col].dropna()).split()
            word_counts = Counter(word for word in words if word not in stop_words)
            
            most_common_words = word_counts.most_common(15)
            
            table = Table(title=f"Top 15 Most Common Words in '{text_col}'")
            table.add_column("Word", style="cyan")
            table.add_column("Count", style="magenta", justify="right")
            for word, count in most_common_words:
                table.add_row(word, str(count))
            console.print(table)
            
            # Generate Plot
            plt.figure(figsize=(12, 8))
            pd.DataFrame(most_common_words, columns=['Word', 'Count']).plot.bar(x='Word', y='Count', color='cyan', legend=False)
            plt.title(f"Top 15 Most Common Words in '{text_col}'", fontsize=16)
            plt.ylabel("Frequency")
            plt.xlabel("Words")
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()

        elif action == "group_and_aggregate":
            # (This logic remains the same)
            groupby_col = insight_plan["groupby_column"]
            agg_col = insight_plan["agg_column"]
            agg_func = insight_plan["agg_function"]
            print(f"AI Insight Plan: Group by '{groupby_col}', calculate '{agg_func}' of '{agg_col}'.")
            insight_data = df.groupby(groupby_col)[agg_col].agg(agg_func).sort_values(ascending=False)
            # ... (table and plot generation for this case) ...
        
        else:
            print("AI did not suggest a valid insight plan.")
            return {"insights": {}}

        os.makedirs("outputs/insights", exist_ok=True)
        plot_path = f"outputs/insights/final_insight_plot.png"
        plt.savefig(plot_path)
        print(f"Saved plot to {plot_path}")

        return {"insights": {"plot_path": plot_path}}
        
    except Exception as e:
        print(f"Error executing insight plan: {e}")
        return {"insights": {}}