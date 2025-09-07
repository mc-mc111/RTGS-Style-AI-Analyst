import os
import json
from datetime import datetime
from typing import Dict, Any, List

import google.generativeai as genai
from dotenv import load_dotenv

from state import GraphState
from agents.logger import logger

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_dataset_summary(profile: Dict[str, Any]) -> str:
    """Asks the AI to generate a high-level, natural language summary of the dataset."""
    logger.debug("Generating dataset summary with AI...")

    summary_profile = {
        "total_rows": profile.get("total_rows", "N/A"),
        "column_names": list(profile.get("columns", {}).keys())
    }

    prompt = f"""
    You are a data analyst writing the introduction to a report.
    Based on the following data profile, write a brief, one-paragraph summary of what this dataset contains.
    Describe it in a professional, easy-to-understand way.

    Data Profile:
    {json.dumps(summary_profile, indent=2)}

    Generate the summary paragraph now.
    """
    
    model = genai.GenerativeModel("gemini-1.5-flash-latest") # Corrected model name
    
    try:
        response = model.generate_content(prompt)
        return response.text
    except Exception as e:
        logger.error(f"Error generating dataset summary: {e}")
        return "An AI-generated summary of the dataset could not be produced."


def insight_report_node(state: GraphState) -> Dict[str, Any]:
    """
    Gathers all generated insights, tables, and findings to create a final 
    Markdown insight report.
    """
    logger.info("    - Executing: Insight Report Builder Node")
    
    raw_data_path = state.get('raw_data_path', 'N/A')
    generated_insights = state.get('insights', {}).get('generated_insights', [])
    data_profile = state.get('data_profile', {})
    
    report_lines = [
        f"# Automated EDA Insight Report: {os.path.basename(raw_data_path)}",
        f"**Run Timestamp:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
        "---"
    ]
    
    if data_profile:
        report_lines.append("## Dataset Overview")
        summary_text = generate_dataset_summary(data_profile)
        report_lines.append(summary_text)
        report_lines.append("---")

    if not generated_insights:
        report_lines.append("No insights were generated for this dataset.")
    else:
        report_lines.append("## Key Findings & Visualizations")
        for insight in generated_insights:
            summary = insight.get('summary', 'Untitled Insight')
            plot_path = insight.get('plot_path')
            question = insight.get('question', 'No question was provided for this analysis.')
            finding = insight.get('finding', 'No recommendation was generated for this analysis.')
            markdown_table = insight.get('markdown_table')
            
            report_lines.append(f"\n### {summary}")
            report_lines.append(f"> **Question:** *{question}*")

            if markdown_table:
                report_lines.append("\n**Summary Data:**")
                report_lines.append(markdown_table)

            if plot_path:
                relative_path = os.path.basename(plot_path)
                report_lines.append(f"\n**Visualization:**")
                report_lines.append(f"![{summary}]({relative_path})")

            # --- START: FINAL UPGRADE ---
            # Change the label from "Finding" to "Recommendation"
            report_lines.append(f"\n**Recommendation:** {finding}")
            # --- END: FINAL UPGRADE ---
    
    report_lines.append("\n---\n*End of Report*")
    
    report_content = "\n".join(report_lines)
    report_path = "outputs/insights/insight_report.md"
    
    try:
        os.makedirs(os.path.dirname(report_path), exist_ok=True)
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report_content)
        logger.debug(f"Successfully generated and saved insight report to {report_path}")
    except Exception as e:
        logger.error(f"Error saving insight report: {e}")

    return {"documentation_path": report_path}