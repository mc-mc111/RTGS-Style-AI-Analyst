# RTGS-Style AI Analyst

A terminal-based agentic system that transforms raw, messy datasets into standardized, analysis-ready insights. This prototype uses a state-driven graph and a Large Language Model (LLM) to create and execute dynamic data cleaning and feature engineering plans.

---

## Mission

The goal of this project is to prototype a Real-Time Governance System (RTGS) that empowers decision-makers by turning raw public data into trustworthy, actionable evidence. The system is designed to be run from the command line, providing a fast and efficient workflow from data to insight.

---

## High-Level Architecture

The system is built as an **agentic pipeline** using the **LangGraph** framework. Instead of a rigid script, the workflow is a graph of specialized nodes (agents) that pass a central `state` object between them. This modular design makes the system highly extensible and robust.

### The Agents

1.  **Ingestion Agent:** Loads the raw dataset, standardizes column names to a consistent format (`snake_case`), and prepares it for analysis.
2.  **Planning Agent (The Brain):** This is the core of the system. It first programmatically profiles the data to understand its structure and statistics. It then sends this profile to the **Google Gemini AI** to generate a custom, step-by-step JSON plan for cleaning, transformation, and feature engineering. Crucially, it asks the AI to provide a **reason** for every action.
3.  **Cleaning Agent:** A dynamic executor that reads the AI-generated plan from the state and performs a series of complex operations, such as removing unnecessary columns, cleaning messy numeric data (e.g., currency), and creating new features.
4.  **Insight Agent:** An intelligent analyst that profiles the final, cleaned data and asks the AI to suggest a meaningful insight. It then executes the AI's suggestion, generating a summary table in the console and saving a plot to a file.
5.  **Documentation Agent:** The final scribe that compiles all information from the run—including the AI's reasoned plan—into a clean, human-readable Markdown report for transparency and auditing.

---

## Key Features

- **Dynamic Cleaning:** The system adapts to any tabular dataset, with the AI generating a custom cleaning plan on the fly.
- **Automated Feature Engineering:** The AI proactively suggests and creates new, valuable columns from the existing data (e.g., calculating BMI from height and weight).
- **Adaptive Insights:** The final analysis is not hard-coded; the AI suggests a relevant insight based on the columns present in the final cleaned dataset.
- **Intelligent Column Removal:** Automatically identifies and removes columns with low analytical value (like IDs or redundant fields).
- **Transparent Reporting:** Every run produces a detailed Markdown report explaining what actions were taken and, most importantly, *why*.

---

## Technology Stack

- **Agent-Orchestration:** LangGraph
- **Data Manipulation:** pandas
- **LLM Used:** Google Gemini
- **CLI:** Typer
- **Console UI:** rich
- **Plotting:** Matplotlib

---

## Project Structure
rtgs-ai-analyst/
├── .venv/
├── agents/
│   ├── init.py
│   ├── ai_planner.py
│   ├── cleaning.py
│   ├── documentation.py
│   ├── ingestion.py
│   ├── insight.py
│   └── profiler.py
├── data/
│   └── (Your datasets go here)
├── outputs/
│   ├── insights/
│   │   └── (Generated plots appear here)
│   ├── 1_standardized_data.csv
│   ├── 2_cleaned_data.csv
│   └── run_report.md
├── .env
├── .gitignore
├── main.py
├── README.md
├── requirements.txt
└── state.py

---

## Setup and Installation

Follow these steps to set up the project on a Windows machine.

### 1. Clone the Repository
git clone https://github.com/mc-mc111/RTGS-Style-AI-Analyst
cd rtgs-ai-analyst

### 2. Set Up the Python Environment
**Create and activate a virtual environment**
python -m venv .venv
.venv\Scripts\activate

### 3. Install Dependencies
pip install -r requirements.txt

### 4. Configure Your API Key
**Create a file named .env in the project's root directory. Add your Google API key to this file:**

GOOGLE_API_KEY="YOUR_GOOGLE_API_KEY_HERE"

### How to Run
**This application will run from the terminal. You must provide the path to the dataset you want to analyze as an argument.**

**Place your dataset (e.g., my_data.csv) inside the data/ folder.**

Run the following command in your terminal:
python main.py data/my_data.csv

The pipeline will execute, showing the progress of each agent in the console.
Incase if you don't give any input file it default executes for "TG-NPDCL_consumption_detail_agriculture_AUGUST-2025.csv" which is already available  in the repository.

### Expected Outputs
**After a successful run, you will find the following artifacts in the outputs/ directory:**

**1_standardized_data.csv**: The data after initial ingestion and column name standardization.

**2_cleaned_data.csv**: The final, cleaned, and feature-enriched dataset.

**outputs/insights/dynamic_plot.png**: A plot of the key insight generated by the Insight Agent.

**run_report.md**: A detailed report of the entire run, including the AI's reasoned plan.

## Example Report Snippet (run_report.md)

## RTGS AI Analyst Run Report

**Run Timestamp:** 2025-09-06 15:40:14
**Location:** Vijayawada, Andhra Pradesh, India

---

## 1. Input Data
- **Source File:** `concert.csv`

---

## 2. AI-Generated Analysis & Transformation Plan
The AI analyzed the data and generated the following plan, which was then executed.

**Step 1: Remove Column** on column `actualgross`

> *Reason: The column 'actualgross' is an identifier column with unique values for each row and does not provide analytical value.*

**Step 2: Remove Column** on column `adjustedgross_in_2022_dollars`

> *Reason: The column 'adjustedgross_in_2022_dollars' is an identifier column with unique values for each row and does not provide analytical value.*

**Step 3: Remove Column** on column `tour_title`

> *Reason: The column 'tour_title' is an identifier column with unique values for each row and does not provide analytical value.*

**Step 4: Remove Column** on column `average_gross`

> *Reason: The column 'average_gross' is an identifier column with unique values for each row and does not provide analytical value.*

**Step 5: Remove Column** on column `ref`

> *Reason: The column 'ref' is an identifier column with unique values for each row and does not provide analytical value.*

**Step 6: Convert Type** on column `peak`

> *Reason: The 'peak' column contains numeric data stored as strings with brackets and annotations. Converting it to numeric after cleaning will allow for numerical analysis. Missing values will be represented as NaN.*

**Step 7: Convert Type** on column `all_time_peak`

> *Reason: The 'all_time_peak' column contains numeric data stored as strings with brackets and annotations. Converting it to numeric after cleaning will allow for numerical analysis. Missing values will be represented as NaN.*

**Step 8: Create Feature** on column `start_year`

> *Reason: Extract the starting year from the 'years' column to facilitate time-based analysis. The regex will extract the first 4 digit number from the string.*

**Step 9: Convert Type** on column `start_year`

> *Reason: Convert the 'start_year' column to integer type for numerical analysis.*

---

## 3. Execution Log
A high-level log of the pipeline's execution stages:
- Ingestion complete.
- AI planning complete.
- Dynamic cleaning complete.


---
*End of Report*

In this way your going to get a detailed report.