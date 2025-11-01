import os
import json
import socket
import google.generativeai as genai
from dotenv import load_dotenv
from typing import Dict, Any
from agents.logger import logger

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
    logger.debug("Generating cleaning plan with AI...")

    if not check_internet_connection():
        raise ConnectionError("No internet connection. Cannot contact AI planner.")
    logger.info("Internet connection verified.")
    
    prompt = f"""
    You are an expert data scientist preparing a dataset for machine learning. Your task is to generate a JSON object with a 'steps' key
    containing a list of actions to clean and enhance a pandas DataFrame based on its data profile.

    **CRITICAL Instructions:**
    1.  **Include a "reason" for every single step.** Explain why the action is necessary for analysis.
    
    # --- START: FINAL UPGRADE ---
    2.  **Use Categorical Cleaning Wisely:** ONLY suggest the `clean_categorical` action for columns that have a very low number of unique values (e.g., less than 10), like a 'sentiment' or 'status' column. Do NOT use it for columns with many unique values like city or district names.
    # --- END: FINAL UPGRADE ---

    3.  **Improve Readability:** If a column is named 'age' and its mean value is over 365, it is likely in days. You MUST suggest a `create_feature` step to create a new 'age_in_years' column by dividing 'age' by 365.25. Then, suggest removing the original 'age' column.
    4.  **Encode Binary Categories:** If a column has only two unique values (like 'yes'/'no' or 'true'/'false'), suggest the `encode_binary` action to convert them to 1s and 0s for modeling.
    5.  **Scale Numeric Features:** For important numeric columns that are not identifiers, suggest the `scale_numeric` action to normalize or standardize their values. Prefer 'min_max' scaling.
    6.  **PRIORITIZE TEXT COLUMNS:** If you see columns with names like 'review' or 'text', assume they are important. Suggest the `clean_text` action for them.
    7.  **Handle Duplicates and Unnecessary Columns:** Always suggest removing duplicates and any truly useless columns.
    8.  **Clean Messy Numeric Data:** Suggest `convert_type` with `pre_processing` for object columns that contain numbers.
    9.  **Engineer Features:** Suggest `create_feature` where it provides clear value for simple mathematical expressions.
    10. **Use Custom Functions for Complex Tasks:** For complex transformations that require specific logic, like calculating the number of years from a date range (e.g., '2023-24'), suggest the `execute_custom_function` action and specify the `calculate_year_span` helper function.

    **Allowed Actions & Required JSON Structure:**

    - **action: "encode_binary"**
      - **column**: The binary categorical column (e.g., "smoker").
      - **details**: {{"positive_value": "yes"}}  (The value that should map to 1).
      - **reason**: Explain that converting categories to numbers is essential for machine learning models.

    - **action: "scale_numeric"**
      - **column**: The numeric column to scale (e.g., "age").
      - **details**: {{"strategy": "min_max"}} (Can be 'min_max' for normalization or 'standard' for standardization).
      - **reason**: Explain that scaling features to a similar range improves the performance of many ML models.

    - **action: "execute_custom_function"**
      - **column**: The name of the new column to create (e.g., "tour_duration_years").
      - **details**: {{"function_name": "calculate_year_span", "source_column": "years"}}
      - **reason**: Explain that a specialized function is needed for this complex transformation.

    - **action: "clean_categorical"**
      - **column**: The categorical column to clean (e.g., "decision").
      - **details**: {{"valid_values": ["positive", "negative"]}}
      - **reason**: Explain that this step ensures the column only contains valid categories for accurate grouping.

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
    
    # Corrected model name to the one that works
    model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)
    
    try:
        response = model.generate_content(prompt)
        plan = json.loads(response.text)
        logger.debug("Successfully generated reasoned cleaning plan from AI.")
        return plan
    except Exception as e:
        logger.error(f"An error occurred during AI plan generation: {e}")
        return {"steps": []}