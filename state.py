from typing import TypedDict, List, Dict, Any

class GraphState(TypedDict):
    """
    Represents the state of our data analysis graph.
    It's the central object passed between all nodes.
    """
    # File paths that track the data's journey
    raw_data_path: str
    standardized_data_path: str
    cleaned_data_path: str

    # The AI-generated plan for cleaning the data
    cleaning_plan: Dict[str, Any]

    # --- START: NEW ADDITION ---
    # The statistical profile of the data, to be used for the final report
    data_profile: Dict[str, Any]
    # --- END: NEW ADDITION ---

    # A running log of actions taken during the process
    log_messages: List[str]

    # The final insights and artifacts generated
    insights: Dict[str, Any]
    documentation_path: str