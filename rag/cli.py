"""Interactive CLI for Acme Tech Enterprise RAG."""
from pathlib import Path
import typer
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

from rag.config import settings
from rag.document_loader import load_all_documents, load_document_file
from rag.vector_store import AcmeVectorStore
from rag.engine import RAGEngine, EXACT_NOT_FOUND

app = typer.Typer(help="Acme Tech Enterprise Internal Document Assistant CLI")
console = Console()

ROLE_COLORS = {
    "employee": "green",
    "manager": "yellow",
    "admin": "red"
}

@app.command()
def ingest(
    docs_dir: str = typer.Option(
        None,
        "--docs-dir", "-d",
        help="Path to documents directory containing markdown files"
    ),
    reset: bool = typer.Option(
        False,
        "--reset", "-r",
        help="Reset existing vector store before ingesting"
    )
):
    """Ingest Acme Tech company documents into ChromaDB with role metadata."""
    target_path = Path(docs_dir) if docs_dir else Path(settings.DOCUMENTS_DIR)

    if not target_path.exists():
        console.print(f"[bold red]Error:[/bold red] Documents directory '{target_path}' does not exist.")
        raise typer.Exit(1)

    console.print(Panel(
        f"[bold cyan]Acme Tech Document Ingestion Engine[/bold cyan]\n"
        f"Directory: [dim]{target_path}[/dim]\n"
        f"Chroma DB: [dim]{settings.CHROMA_PERSIST_DIR}[/dim]\n"
        f"Embedding Provider: [dim]{settings.EMBEDDING_PROVIDER}[/dim]",
        border_style="cyan"
    ))

    vector_store = AcmeVectorStore()
    if reset:
        console.print("[yellow]Resetting vector collection...[/yellow]")
        vector_store.client.delete_collection(vector_store.COLLECTION_NAME)
        vector_store = AcmeVectorStore()

    with console.status("[bold green]Loading and chunking markdown documents..."):
        chunks = load_all_documents(target_path)
        added_count = vector_store.add_chunks(chunks)

    indexed_docs = vector_store.get_all_indexed_docs()

    table = Table(title="Ingested Acme Tech Documents", border_style="dim")
    table.add_column("Doc ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="white")
    table.add_column("Role Access", style="bold")
    table.add_column("Department", style="magenta")
    table.add_column("Chunks", justify="right", style="green")

    for doc in indexed_docs:
        role = doc["role_access"]
        role_color = ROLE_COLORS.get(role, "white")
        table.add_row(
            doc["doc_id"],
            doc["title"],
            f"[{role_color}]{role.upper()}[/{role_color}]",
            doc["department"],
            str(doc["chunks"])
        )

    console.print(table)
    console.print(f"\n[bold green]Success![/bold green] Ingested {len(indexed_docs)} documents ({added_count} total chunks) into ChromaDB.\n")

@app.command()
def ask(
    question: str = typer.Argument(..., help="The question to ask the document assistant"),
    role: str = typer.Option(
        "employee",
        "--role", "-r",
        help="User role: 'employee', 'manager', or 'admin'"
    ),
    top_k: int = typer.Option(4, "--top-k", "-k", help="Number of chunks to evaluate")
):
    """Ask a question as a specific role and view citations."""
    role = role.lower().strip()
    if role not in ROLE_COLORS:
        console.print(f"[bold red]Invalid role '{role}'.[/bold red] Must be 'employee', 'manager', or 'admin'.")
        raise typer.Exit(1)

    role_color = ROLE_COLORS[role]
    console.print(f"\n[bold {role_color}][Role: {role.upper()}][/bold {role_color}] [bold white]Q: {question}[/bold white]")

    engine = RAGEngine()
    response = engine.ask(query=question, role=role, top_k=top_k)

    # Display Answer
    if not response.is_found or response.answer == EXACT_NOT_FOUND:
        console.print(Panel(
            f"[bold red]{EXACT_NOT_FOUND}[/bold red]",
            title="Assistant Response",
            border_style="red"
        ))
    else:
        console.print(Panel(
            f"[white]{response.answer}[/white]",
            title="Assistant Response",
            border_style="green"
        ))

        # Display Citations
        if response.citations:
            cit_table = Table(title="Citations (Retrieved Sources)", border_style="dim")
            cit_table.add_column("#", style="dim", width=3)
            cit_table.add_column("Document", style="cyan")
            cit_table.add_column("Section", style="yellow")
            cit_table.add_column("Snippet", style="white")

            for i, cit in enumerate(response.citations, 1):
                cit_table.add_row(str(i), cit.document, cit.section, cit.snippet)

            console.print(cit_table)
    console.print()

@app.command()
def chat(
    role: str = typer.Option(
        "employee",
        "--role", "-r",
        help="User role: 'employee', 'manager', or 'admin'"
    )
):
    """Start an interactive chat session under a given role."""
    role = role.lower().strip()
    if role not in ROLE_COLORS:
        console.print(f"[bold red]Invalid role '{role}'.[/bold red] Must be 'employee', 'manager', or 'admin'.")
        raise typer.Exit(1)

    role_color = ROLE_COLORS[role]
    console.print(Panel(
        f"[bold]Acme Tech Interactive Document Assistant[/bold]\n"
        f"Active Role: [bold {role_color}]{role.upper()}[/bold {role_color}]\n"
        f"Type [dim]'exit'[/dim] or [dim]'quit'[/dim] to leave, or [dim]'role <new_role>'[/dim] to switch.",
        border_style=role_color
    ))

    engine = RAGEngine()
    current_role = role

    while True:
        try:
            curr_color = ROLE_COLORS.get(current_role, "white")
            user_input = console.input(f"[bold {curr_color}][{current_role.upper()}] > [/bold {curr_color}]").strip()

            if not user_input:
                continue

            if user_input.lower() in ("exit", "quit"):
                console.print("[dim]Goodbye![/dim]")
                break

            if user_input.lower().startswith("role "):
                new_role = user_input.split(" ", 1)[1].strip().lower()
                if new_role in ROLE_COLORS:
                    current_role = new_role
                    console.print(f"[green]Switched role to [bold]{current_role.upper()}[/bold][/green]")
                else:
                    console.print(f"[red]Unknown role '{new_role}'. Choose employee, manager, or admin.[/red]")
                continue

            response = engine.ask(query=user_input, role=current_role)
            if not response.is_found or response.answer == EXACT_NOT_FOUND:
                console.print(f"[red]{EXACT_NOT_FOUND}[/red]\n")
            else:
                console.print(f"\n[bold green]Assistant:[/bold green] {response.answer}")
                if response.citations:
                    console.print("[dim]Citations:[/dim]")
                    for c in response.citations:
                        console.print(f"  • [cyan]{c.document}[/cyan] ({c.section}): \"{c.snippet}\"")
                console.print()

        except (KeyboardInterrupt, EOFError):
            console.print("\n[dim]Session closed.[/dim]")
            break

@app.command("list-docs")
def list_docs():
    """List all currently indexed documents in ChromaDB."""
    vs = AcmeVectorStore()
    docs = vs.get_all_indexed_docs()
    if not docs:
        console.print("[yellow]No documents indexed. Run 'python -m rag.cli ingest' first.[/yellow]")
        return

    table = Table(title="Indexed Acme Tech Documents", border_style="dim")
    table.add_column("Doc ID", style="cyan")
    table.add_column("Title", style="white")
    table.add_column("Role Access", style="bold")
    table.add_column("Department", style="magenta")
    table.add_column("Chunks", justify="right", style="green")

    for d in docs:
        role = d["role_access"]
        role_color = ROLE_COLORS.get(role, "white")
        table.add_row(
            d["doc_id"],
            d["title"],
            f"[{role_color}]{role.upper()}[/{role_color}]",
            d["department"],
            str(d["chunks"])
        )
    console.print(table)

if __name__ == "__main__":
    app()
