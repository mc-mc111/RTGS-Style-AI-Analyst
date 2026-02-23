import glob
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import os
import json
from typing import Dict, Any, List
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

def _create_markdown_table(data: pd.Series, index_name: str, value_name: str) -> str:
    """Converts a pandas Series into a Markdown table string."""
    headers = f"| {index_name} | {value_name} |\n"
    separator = f"|:---|---:|\n"
    rows = ""
    for index, value in data.items():
        try:
            rows += f"| {index} | {float(value):,.2f} |\n"
        except (ValueError, TypeError):
            rows += f"| {index} | {value} |\n"
    return headers + separator + rows

def _create_stats_markdown_table(stats_dict: Dict[str, Any]) -> str:
    """Converts a dictionary of statistics into a Markdown table."""
    headers = "| Statistic | Value |\n"
    separator = "|:---|---:|\n"
    rows = ""
    for key, value in stats_dict.items():
        try:
            rows += f"| {key.replace('_', ' ').title()} | {float(value):,.2f} |\n"
        except (ValueError, TypeError):
             rows += f"| {key.replace('_', ' ').title()} | {value} |\n"
    return headers + separator + rows

def generate_findings_in_batch(interpretation_requests: List[Dict[str, Any]]) -> List[str]:
    """Sends a batch of interpretation requests to the AI to get actionable recommendations."""
    logger.debug(f"Generating {len(interpretation_requests)} recommendations in a single batch...")
    
    # --- START: PROMPT UPGRADE TO POLICY ADVISOR ---
    prompt = "You are a senior policy advisor writing a brief for a decision-maker.\n"
    prompt += "For each of the following numbered analyses, provide a concise, one-sentence actionable policy recommendation based on the key stats. The recommendation should be data-driven and suggest a clear next step or area of focus.\n\n"
    
    for i, req in enumerate(interpretation_requests):
        prompt += f"--- Analysis {i+1} ---\n"
        prompt += f"Question: {req['question']}\n"
        prompt += f"Key Stats: {json.dumps(req['stats'])}\n"
        prompt += "Example Recommendation: Policymakers should investigate the high service load in the 'Warangal' division to determine if resources are allocated effectively.\n\n"

    prompt += "Provide your recommendations as a numbered list of sentences, with each recommendation on a new line."
    # --- END: PROMPT UPGRADE ---

    model = genai.GenerativeModel("gemini-2.5-flash")
    try:
        response = model.generate_content(prompt)
        findings = [line.strip().split('. ', 1)[1] for line in response.text.strip().split('\n') if '. ' in line]
        if len(findings) != len(interpretation_requests):
             return ["An AI-generated recommendation could not be produced." for _ in interpretation_requests]
        return findings
    except Exception as e:
        logger.error(f"Error generating batch recommendations: {e}")
        return ["An AI-generated recommendation could not be produced." for _ in interpretation_requests]


def generate_insight_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Asks the AI to suggest a list of valuable analyses with questions."""
    logger.debug("Generating comprehensive insight plan with AI...")

    simplified_profile = {
        "total_rows": profile.get("total_rows"),
        "columns": list(profile.get("columns", {}).keys())
    }

    prompt = f"""
    You are a principal data analyst. Based on the following profile of a cleaned dataset,
    generate a JSON object containing a list of high-value analyses to perform.

    **CRITICAL Instructions:**
    1.  Suggest a list of 3 to 5 diverse analyses.
    2.  For EACH analysis, provide a "question_to_answer" that the analysis will address.
    3.  Prioritize insights that reveal distributions, correlations, and group-by comparisons.
    4.  Choose the most impactful columns for your analysis.

    **Allowed Analysis Types & JSON Structure:**
    Each item must be a dictionary with "action", "details", and "question_to_answer".

    - "action": "distribution", "details": {{"column": "col_name"}}, "question_to_answer": "What is the spread and central tendency of [column]?"
    - "action": "correlation", "details": {{"column_x": "col1", "column_y": "col2"}}, "question_to_answer": "Is there a relationship between [col1] and [col2]?"
    - "action": "group_by_summary", "details": {{"groupby_column": "cat_col", "agg_column": "num_col", "agg_function": "mean"}}, "question_to_answer": "Which [cat_col] has the highest average [num_col]?"
    - "action": "count_plot", "details": {{"column": "cat_col"}}, "question_to_answer": "What are the most frequent categories in [cat_col]?"
    - "action": "word_frequency", "details": {{"text_column": "col_name"}}, "question_to_answer": "What are the most common topics discussed in the text data?"

    Dataset Profile:
    {json.dumps(simplified_profile, indent=2)}

    Generate the JSON list of analysis steps now in a single root key called "analyses".
    """
    
    generation_config = {"temperature": 0.0, "response_mime_type": "application/json"}
    model = genai.GenerativeModel("gemini-2.5-flash", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text)
    except Exception as e:
        logger.error(f"Error generating insight plan: {e}")
        return {"analyses": []}

def insight_node(state: GraphState) -> Dict[str, Any]:
    """
    Executes analyses, generates plots, and interprets all results in a single batch.
    """
    logger.info("    - Executing: Automated EDA & Interpretation Node")
    insights_dir = "outputs/insights"
    if os.path.exists(insights_dir):
        logger.debug(f"Cleaning old plots from '{insights_dir}'...")
        old_plots = glob.glob(os.path.join(insights_dir, "*.png"))
        for plot in old_plots:
            try:
                os.remove(plot)
            except OSError as e:
                logger.error(f"Error removing old plot {plot}: {e}")
    os.makedirs(insights_dir, exist_ok=True)

    cleaned_data_path = state['cleaned_data_path']
    
    try:
        df = pd.read_csv(cleaned_data_path, encoding='latin-1')
        if df.empty:
            logger.warning("Cleaned data is empty. No insights generated.")
            return {"insights": {"generated_insights": []}}
    except pd.errors.EmptyDataError:
        logger.warning("Cleaned data file is empty. No insights generated.")
        return {"insights": {"generated_insights": []}}
    
    profile = get_data_profile(cleaned_data_path)
    if not profile.get("columns"):
        logger.warning("Data profile is empty. No insights can be generated.")
        return {"insights": {"generated_insights": []}}
        
    insight_plan = generate_insight_plan(profile)
    analysis_tasks = insight_plan.get("analyses", [])
    
    generated_insights = []
    interpretation_batch = []

    for i, task in enumerate(analysis_tasks):
        action = task.get("action")
        details = task.get("details", {})
        question = task.get("question_to_answer", "No question was provided by the AI.")
        
        try:
            plt.figure(figsize=(10, 6))
            plot_path = f"outputs/insights/insight_{i+1}_{action}.png"
            title = f"Insight {i+1}: {action.replace('_', ' ').title()}"
            
            stats_for_ai = None
            markdown_table = None

            if action == "distribution" and details.get("column") in df.columns:
                col = details["column"]
                if pd.api.types.is_numeric_dtype(df[col]):
                    title = f"Distribution of '{col}'"
                    data_to_describe = df[col].dropna()
                else:
                    title = f"Distribution of Length of '{col}'"
                    data_to_describe = df[col].str.len().dropna()

                sns.histplot(data_to_describe, kde=True, color='skyblue')
                plt.title(title, fontsize=16)
                stats = data_to_describe.describe().to_dict()
                stats_for_ai = {k: round(v, 2) for k, v in stats.items() if pd.notna(v)}
                markdown_table = _create_stats_markdown_table(stats_for_ai)

            elif action == "correlation" and all(k in details for k in ["column_x", "column_y"]):
                col_x, col_y = details["column_x"], details["column_y"]
                if col_x in df.columns and col_y in df.columns:
                    title = f"Correlation between '{col_x}' and '{col_y}'"
                    sns.scatterplot(x=df[col_x], y=df[col_y])
                    plt.title(title, fontsize=16)
                    corr = df[col_x].corr(df[col_y])
                    stats_for_ai = {"pearson_correlation": round(corr, 2)}
                    markdown_table = _create_stats_markdown_table(stats_for_ai)

            elif action == "group_by_summary" and all(k in details for k in ["groupby_column", "agg_column", "agg_function"]):
                groupby_col, agg_col, agg_func = details["groupby_column"], details["agg_column"], details["agg_function"]
                if groupby_col in df.columns and agg_col in df.columns:
                    title = f"Top 15 {agg_func.title()} of '{agg_col}' by '{groupby_col}'"
                    summary_data = df.groupby(groupby_col)[agg_col].agg(agg_func).sort_values(ascending=False).head(15)
                    stats_for_ai = summary_data.head(5).to_dict()
                    
                    table = Table(title=title)
                    table.add_column(groupby_col, style="cyan")
                    table.add_column(agg_func.title(), style="magenta", justify="right")
                    for index, value in summary_data.items():
                        table.add_row(str(index), f"{value:,.2f}")
                    console.print(table)
                    
                    markdown_table = _create_markdown_table(summary_data, groupby_col.title(), agg_func.title())
                    summary_data.plot(kind='bar', color='teal')
                    plt.title(title, fontsize=16)
            
            elif action == "count_plot" and details.get("column") in df.columns:
                col = details["column"]
                title = f"Top 15 Category Counts in '{col}'"
                summary_data = df[col].value_counts().head(15)
                stats_for_ai = summary_data.head(5).to_dict()
                markdown_table = _create_markdown_table(summary_data, col.title(), "Count")
                sns.countplot(y=df[col], order=summary_data.index, palette='viridis', hue=df[col], legend=False)
                plt.title(title, fontsize=16)

            elif action == "word_frequency" and details.get("text_column") in df.columns:
                text_col = details["text_column"]
                title = f"Top 15 Most Common Words in '{text_col}'"
                stop_words = set(stopwords.words('english'))
                words = ' '.join(df[text_col].dropna()).split()
                word_counts = Counter(word for word in words if word not in stop_words)
                insight_data = pd.Series(dict(word_counts.most_common(15)))
                stats_for_ai = insight_data.head(5).to_dict()
                
                table = Table(title=title)
                table.add_column("Word", style="cyan")
                table.add_column("Count", style="magenta", justify="right")
                for word, count in insight_data.items():
                    table.add_row(word, str(count))
                console.print(table)
                markdown_table = _create_markdown_table(insight_data, "Word", "Count")
                insight_data.plot.bar(color='cyan')
                plt.title(title, fontsize=16)

            else:
                logger.warning(f"Skipping invalid or incomplete analysis task: {task}")
                plt.close()
                continue
                
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
            plt.savefig(plot_path)
            plt.close()
            logger.debug(f"Saved plot to {plot_path}")
            
            insight_info = {
                "summary": title, 
                "plot_path": plot_path,
                "question": question,
                "markdown_table": markdown_table
            }
            generated_insights.append(insight_info)
            if stats_for_ai:
                interpretation_batch.append({"question": question, "stats": stats_for_ai})
            
        except Exception as e:
            logger.error(f"Could not execute analysis task {task}. Error: {e}", exc_info=True)
            plt.close()

    if interpretation_batch:
        findings = generate_findings_in_batch(interpretation_batch)
        
        for i in range(len(generated_insights)):
            if i < len(findings):
                generated_insights[i]["finding"] = findings[i]
            else:
                generated_insights[i]["finding"] = "An AI-generated finding could not be produced for this insight."
            
    return {"insights": {"generated_insights": generated_insights}}