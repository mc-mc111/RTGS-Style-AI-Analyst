from typing import Dict, Any
from state import GraphState
from agents.profiler import get_data_profile
from agents.ai_planner import generate_cleaning_plan
from agents.logger import logger

def planning_node(state: GraphState) -> Dict[str, Any]:
    """Profiles the data and then uses the AI to generate a cleaning plan."""
    logger.info("    - Executing: AI Planning Node")
    
    data_path = state['standardized_data_path']
    profile = get_data_profile(data_path)
    plan = generate_cleaning_plan(profile)
    
    return {
        "cleaning_plan": plan,
        "log_messages": state.get('log_messages', []) + ["AI planning complete."]
    }   