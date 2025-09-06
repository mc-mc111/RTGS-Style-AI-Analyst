import os
import json
import socket
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def check_internet_connection():
    """Checks for a live internet connection."""
    try:
        socket.create_connection(("8.8.8.8", 53), timeout=3)
        return True
    except OSError:
        return False

def generate_cleaning_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Sends the data profile to the AI to get a reasoned cleaning plan."""
    print("---GENERATING CLEANING PLAN WITH AI---")

    if not check_internet_connection():
        print("Error: No internet connection. Cannot contact AI planner.")
        return {"steps": []}
    print("Internet connection verified.")
    
    prompt = f"""
    You are an expert data analyst. Your task is to generate a JSON object with a 'steps' key
    containing a list of actions to clean and enhance a pandas DataFrame based on its data profile.

    **CRITICAL Instructions:**
    1.  **Include a "reason" for every single step.** Explain why the action is necessary for analysis.
    2.  **Identify and Remove Unnecessary Columns:** If a column is an identifier, redundant, or has no analytical value, suggest the 'remove_column' action.
    3.  **Clean Messy Numeric Columns:** Look for columns with type 'object' that contain numbers, currency, commas, or brackets. Suggest `convert_type` with the necessary `pre_processing` steps.
    4.  **Engineer Features:** If possible, create valuable new columns using the `create_feature` action.

    Allowed actions and details:
    - "action": (e.g., "remove_column", "remove_duplicates", "convert_type", "fill_missing", "create_feature")
    - "column": The target column.
    - "details": A dictionary with parameters for the action.
    - "reason": A clear, concise explanation for why this step is being taken.

    Data Profile:
    {json.dumps(profile, indent=2)}

    Generate the JSON cleaning and feature engineering plan now.
    """

    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json",
    }
    
    model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        plan = json.loads(response.text)
        print("Successfully generated reasoned cleaning plan from AI.")
        return plan
    except Exception as e:
        print(f"An error occurred during AI plan generation: {e}")
        return {"steps": []}