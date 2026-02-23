# RTGS AI Analyst - Improvement Roadmap

This document outlines the identified flaws in the current system and the planned fixes, categorized by their impact on the codebase.

## 1. Stability & Defensive Programming (High Priority)

* [ ] **Implement Column Existence Checks**: Modify `agents/cleaning.py` to verify if a column exists before attempting any transformation (Prevents `KeyError`).
* [ ] **Graceful Step Failure**: Wrap individual cleaning steps in `try...except` blocks to allow the pipeline to continue even if one transformation fails.
* [ ] **Safe Row Filtering**: Add safeguards to `clean_categorical` to prevent the deletion of all rows if filter criteria don't match exactly.
* [ ] **Concurrent File Handling**: Update `insight_node` to use unique file naming or subdirectories for visual artifacts to prevent race conditions during parallel runs.

## 2. AI Alignment & Logic (Core Logic)

* [ ] **Dynamic Tool Schema Injection**: Update the AI prompt in `agents/ai_planner.py` to dynamically include only the functions actually implemented in the `cleaning.py` library.
* [ ] **Validated Action Planning**: Add a validation layer that checks the AI's JSON plan against the available tools before passing it to the execution node.
* [ ] **Improved Prompt Constraints**: Better instructions for the AI to handle numeric scaling and text cleaning based on the specific data types detected.

## 3. Data Integrity & Preprocessing

* [ ] **Duplicate Header Resolution**: Update `standardize_column_names` to detect collisions (e.g., "Col A!" and "Col A?" both becoming "cola") and append unique suffixes.
* [ ] **Fuzzy Categorical Cleaning**: Implement case-insensitive and whitespace-trimmed matching for the `clean_categorical` action.
* [ ] **Generalized Hybrid Ingestion**: Replace the hardcoded "review" keyword check with a structure-based heuristic (e.g., delimiter count, line skip ratio) to detect malformed CSVs.

## 4. Performance & Scalability

* [ ] **True Large-File Handling**: Replace placeholder logging with actual `chunksize` processing or a switch to `Polars` for files > 100MB.
* [ ] **Memory Optimization**: Reduce redundant `pd.read_csv()` calls across nodes by passing DataFrames or reusing cached states where possible.

## 5. Clean Code & Maintainability

* [ ] **Centralized Configuration**: Move hardcoded values (Model Names: `gemini-2.5-flash`, API endpoints, and timeouts) to a central `config.py` or `.env` file.
* [ ] **Environment Agnostic Health Checks**: Refactor the internet connectivity check to be more robust across different network configurations (e.g., using official Google API ping).
* [ ] **Enhanced Execution Log**: Improve the technical report to show specifically which steps failed and why, instead of just a high-level summary.
