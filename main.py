import typer
from rich.console import Console
from langgraph.graph import StateGraph, END
from state import GraphState
from agents.ingestion import ingestion_node
from agents.planning import planning_node
from agents.cleaning import cleaning_node
from agents.insight import insight_node
from agents.documentation import documentation_node # <-- Import the final node

console = Console()
app = typer.Typer()

@app.command()
def run(input_file: str = typer.Argument("TG-NPDCL_consumption_detail_agriculture_AUGUST-2025.csv", help="Path to the input CSV file.")):
    """Runs the full data analysis pipeline with insights and documentation."""
    console.print(f"[bold green]Starting AI pipeline for: {input_file}[/bold green]")

    workflow = StateGraph(GraphState)
    workflow.add_node("ingest", ingestion_node)
    workflow.add_node("plan", planning_node)
    workflow.add_node("clean", cleaning_node)
    workflow.add_node("insight", insight_node)
    workflow.add_node("document", documentation_node) # <-- Add the final node

    workflow.set_entry_point("ingest")
    workflow.add_edge("ingest", "plan")
    workflow.add_edge("plan", "clean")
    workflow.add_edge("clean", "insight")
    workflow.add_edge("insight", "document") # <-- Rewire the graph
    workflow.add_edge("document", END)

    graph = workflow.compile()

    initial_state = {"raw_data_path": input_file}
    final_state = graph.invoke(initial_state)

    console.print("\n[bold green]AI pipeline run complete! All artifacts generated.[/bold green]")
    console.print(final_state)

if __name__ == "__main__":
    app()
