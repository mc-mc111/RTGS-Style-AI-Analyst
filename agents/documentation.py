import json
from datetime import datetime
from typing import Dict, Any
from agents.logger import logger
from state import GraphState

def format_plan_for_report(plan: Dict[str, Any]) -> str:
    """Formats the JSON plan into a readable Markdown list."""
    report_lines = []
    steps = plan.get("steps", [])
    
    if not steps:
        return "No cleaning or feature engineering plan was generated."
        
    for i, step in enumerate(steps):
        action = step.get("action", "N/A").replace("_", " ").title()
        column = step.get("column") or step.get("details", {}).get("column")
        reason = step.get("reason", "No reason provided.")
        
        line = f"**Step {i+1}: {action}**"
        if column:
            line += f" on column `{column}`"
        
        report_lines.append(line)
        report_lines.append(f"> *Reason: {reason}*")
        
    return "\n\n".join(report_lines)


def documentation_node(state: GraphState) -> Dict[str, Any]:
    """Gathers all information and creates a final Markdown report."""
    logger.info("    - Executing: Documentation Node")
    
    raw_data_path = state.get('raw_data_path', 'N/A')
    cleaning_plan = state.get('cleaning_plan', {})
    log_messages = state.get('log_messages', [])
    
    # Format the plan into a readable list
    formatted_plan = format_plan_for_report(cleaning_plan)
    
    report = f"""
# RTGS AI Analyst Run Report

**Run Timestamp:** {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}
**Location:** Vijayawada, Andhra Pradesh, India

---

## 1. Input Data
- **Source File:** `{raw_data_path}`

---

## 2. AI-Generated Analysis & Transformation Plan
The AI analyzed the data and generated the following plan, which was then executed.

{formatted_plan}

---

## 3. Execution Log
A high-level log of the pipeline's execution stages:
{"\n- ".join(log_messages)}


---
*End of Report*
"""
    
    # Define the path and save the report to a file, ensuring UTF-8 encoding
    report_path = "outputs/run_report.md"
    try:
        with open(report_path, "w", encoding="utf-8") as f:
            f.write(report)
        logger.debug(f"Successfully generated and saved run report to {report_path}")
    except Exception as e:
        logger.error(f"Error saving report: {e}")

    # Update the state with the path to the final report
    return {"documentation_path": report_path}