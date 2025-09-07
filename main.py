import os
import typer
import traceback
from datetime import datetime
from langgraph.graph import StateGraph, END

# We will wrap the agent imports in a try block as well
try:
    from agents.logger import logger, log_error_and_exit
    from state import GraphState
    from agents.ingestion import ingestion_node
    from agents.planning import planning_node
    from agents.cleaning import cleaning_node
    from agents.insight import insight_node
    # --- START: UPGRADE - Re-import BOTH report builders ---
    from agents.insight_report import insight_report_node
    from agents.documentation import documentation_node # Re-import the original report node
    # --- END: UPGRADE ---
except ImportError as e:
    # This will catch errors like the one you saw if a module is missing or has an issue
    print("\n[ERROR] A critical error occurred during application startup.")
    print(f"Details: {e}")
    print("Please ensure all dependencies are installed correctly.")
    # We can't use the logger here because it might be the thing that failed to import
    # So we write a manual error log
    if not os.path.exists("logs"):
        os.makedirs("logs")
    with open(f"logs/import_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log", "w") as f:
        f.write(traceback.format_exc())
    raise typer.Exit(code=1)


# The logger is now created in the logger.py file
app = typer.Typer()

@app.command()
def run(input_file: str = typer.Argument(..., help="Path to the input CSV file.")):
    """Runs the full Automated EDA pipeline with a clean, logged interface."""
    
    try:
        logger.info("[bold green]Starting Automated EDA Pipeline...[/bold green]")
        
        # --- Pre-flight Checks ---
        logger.info(f"--> Verifying input file: '{input_file}'")
        if not os.path.exists(input_file):
            raise FileNotFoundError(f"Input file not found.")
        if os.path.getsize(input_file) == 0:
            raise ValueError(f"Input file is empty.")
        logger.info("    File verified successfully.")

        # --- Define Graph ---
        workflow = StateGraph(GraphState)
        workflow.add_node("ingest", ingestion_node)
        workflow.add_node("plan", planning_node)
        workflow.add_node("clean", cleaning_node)
        workflow.add_node("insight", insight_node)
        # --- START: UPGRADE - Add BOTH report nodes to the graph ---
        workflow.add_node("documentation", documentation_node) # The original technical report
        workflow.add_node("insight_report", insight_report_node) # The new analytical report
        
        workflow.set_entry_point("ingest")
        workflow.add_edge("ingest", "plan")
        workflow.add_edge("plan", "clean")
        workflow.add_edge("clean", "insight")
        # Re-wire the final steps to run both report builders in sequence
        workflow.add_edge("insight", "documentation")
        workflow.add_edge("documentation", "insight_report")
        workflow.add_edge("insight_report", END)
        # --- END: UPGRADE ---
        graph = workflow.compile()

        # --- Execute Pipeline ---
        initial_state = {"raw_data_path": input_file}
        logger.info("--> Executing data processing and analysis pipeline...")
        final_state = graph.invoke(initial_state)

        logger.info("\n[bold green]Automated EDA Pipeline Complete![/bold green]")
        # --- START: UPGRADE - Update the final message to mention both reports ---
        # The documentation_path key will now point to the last report generated
        logger.info(f"    - Analytical Insight Report: outputs/insights/insight_report.md")
        logger.info(f"    - Technical Run Report: outputs/run_report.md")
        logger.info(f"    - Cleaned Data: {final_state.get('cleaned_data_path')}")
        # --- END: UPGRADE ---

    except PermissionError as e:
        logger.critical("PermissionError occurred:", exc_info=True)
        logger.info(f"\n[bold red]FILE LOCK ERROR:[/bold red] The file '{e.filename}' is currently open or being used by another program (like Excel).")
        logger.info("Please close the program that is using the file and try again.")
        raise typer.Exit(code=1)
    except (ValueError, FileNotFoundError, ConnectionError) as e:
        # Catch our known, user-facing errors
        log_error_and_exit(logger, e)
    except Exception as e:
        # Catch any other unexpected runtime errors
        log_error_and_exit(logger, e)

if __name__ == "__main__":
    # This is the master safety net. It will catch any error, including ImportErrors.
    try:
        app()
    except Exception as e:
        # This part runs if something catastrophic happened before the logger was even ready
        print("\nAn unexpected critical error occurred.")
        # Manually create a log file for the traceback
        if not os.path.exists("logs"):
            os.makedirs("logs")
        log_filename = f"logs/critical_error_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
        with open(log_filename, "w") as f:
            f.write(traceback.format_exc())
        print(f"Details have been saved to '{log_filename}'.")