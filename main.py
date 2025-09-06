import typer
from rich.console import Console
from langgraph.graph import StateGraph, END
from state import GraphState
from agents.ingestion import ingestion_node
from agents.planning import planning_node # <-- Import new node
from agents.cleaning import cleaning_node

console = Console()
app = typer.Typer()
file_loc = "TG-NPDCL_consumption_detail_agriculture_AUGUST-2025.csv"
@app.command()
def run(input_file: str = typer.Argument(file_loc, help=file_loc)):
    """Runs the full data analysis pipeline with AI-driven cleaning."""
    console.print(f"[bold green]Starting AI pipeline for: {input_file}[/bold green]")

    workflow = StateGraph(GraphState)
    workflow.add_node("ingest", ingestion_node)
    workflow.add_node("plan", planning_node) # <-- Add new node
    workflow.add_node("clean", cleaning_node)
    
    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "plan") # <-- Rewire edges
    workflow.add_edge("plan", "clean")
    workflow.add_edge("clean", END)

    graph = workflow.compile()

    initial_state = {"raw_data_path": input_file}
    final_state = graph.invoke(initial_state)

    console.print("\n[bold green]AI pipeline run complete![/bold green]")
    console.print("Final State:")
    console.print(final_state)

if __name__ == "__main__":
    app()