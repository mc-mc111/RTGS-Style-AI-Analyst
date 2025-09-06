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
    You are an expert data scientist. Your task is to generate a JSON object with a 'steps' key
    containing a list of actions to clean and enhance a pandas DataFrame based on its data profile.

    **CRITICAL Instructions:**
    1.  **Include a "reason" for every single step.** Explain why the action is necessary for analysis.
    2.  **PRIORITIZE TEXT COLUMNS:** If you see columns with names like 'review' or 'text', assume they are important. Suggest the `clean_text` action for them.
    3.  **Handle Duplicates and Unnecessary Columns:** Always suggest removing duplicates and any truly useless columns.
    4.  **Clean Messy Numeric Data:** Suggest `convert_type` with `pre_processing` for object columns that contain numbers.
    5.  **Engineer Features:** Suggest `create_feature` where it provides clear value.

    **Allowed Actions & Required JSON Structure:**

    - **action: "clean_text"**
      - **column**: The name of the text column (e.g., "review_text").
      - **details**: {{"operations": ["lowercase", "remove_punctuation", "remove_digits", "remove_non_ascii"]}}
      - **reason**: Explain why cleaning text is crucial for NLP tasks.

    - **action: "remove_column"**
      - **column**: The name of the column to remove (e.g., "user_id").
      - **details**: {{}}
      - **reason**: Explain why the column is not useful for analysis (e.g., "it's an identifier").

    - **action: "remove_duplicates"**
      - **column**: null
      - **details**: {{}}
      - **reason**: Explain that removing duplicates prevents skewed analysis.

    - **action: "convert_type"**
      - **column**: The name of the column to convert (e.g., "price").
      - **details**: {{"new_type": "float64", "pre_processing": ["remove_currency", "remove_commas"]}}
      - **reason**: Explain why changing the data type is necessary for calculations.

    - **action: "fill_missing"**
      - **column**: The name of the column with missing values (e.g., "age").
      - **details**: {{"strategy": "mean"}}
      - **reason**: Explain the choice of filling strategy.

    - **action: "create_feature"**
      - **column**: null
      - **details**: {{"new_column_name": "bmi", "expression": "weight / ((height / 100) ** 2)"}}
      - **reason**: Explain what the new feature represents and why it's valuable.

    Data Profile:
    {json.dumps(profile, indent=2)}

    Generate the JSON cleaning and feature engineering plan now.
    """

    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json",
    }
    
    model = genai.GenerativeModel("gemini-1.5-flash-latest", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        plan = json.loads(response.text)
        print("Successfully generated reasoned cleaning plan from AI.")
        return plan
    except Exception as e:
        print(f"An error occurred during AI plan generation: {e}")
        return {"steps": []}