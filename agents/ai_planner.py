import os
import json
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any

load_dotenv()
genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))

def generate_cleaning_plan(profile: Dict[str, Any]) -> Dict[str, Any]:
    """Sends the data profile to the AI to get a JSON cleaning plan."""
    print("---GENERATING CLEANING PLAN WITH AI---")

    prompt = f"""
        You are an expert data analyst. Your task is to generate a JSON object with a 'steps' key,
        containing a list of actions to clean a pandas DataFrame based on its data profile.

        **Instructions:**
        1.  **Analyze Thoroughly:** Carefully examine the `data_type`, `missing_values_count`, and `top_5_values` for each column.
        2.  **Be Proactive:** Suggest `convert_type` for any column that looks numeric but has a data_type of 'object'. For example, columns with numbers, commas, or currency symbols.
        3.  **Handle Missing Data:** For numeric columns with missing values, suggest a `fill_missing` step using the 'mean' or 'median'.
        4.  **Always Check for Duplicates:** Always include a `remove_duplicates` step.

        Allowed actions and their required details:
        - 'remove_duplicates': Removes duplicate rows. 'details' must be an empty dictionary.
        - 'convert_type': Changes a column's data type. 'details' must include "new_type" (e.g., "int64", "float64").
        - 'fill_missing': Fills missing values. 'details' must include a "strategy" (e.g., "mean", "median", "mode").

        Data Profile:
        {json.dumps(profile, indent=2)}

        Generate the JSON cleaning plan now.
        """

    generation_config = {
        "temperature": 0.0,
        "response_mime_type": "application/json",
    }
    
    model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        plan = json.loads(response.text)
        print("Successfully generated cleaning plan from AI.")
        return plan
    except Exception as e:
        print(f"An error occurred during AI plan generation: {e}")
        # Return a default, safe plan on error
        return {"steps": [{"action": "remove_duplicates", "column": None, "details": {}}]}