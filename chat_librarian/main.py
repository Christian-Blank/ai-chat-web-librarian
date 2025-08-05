import asyncio
from typing import Optional

import typer
from playwright.async_api import Error
from rich.console import Console
from rich.panel import Panel

# MODIFIED: Import from the new 'downloader' module and function name
from chat_librarian.downloader import download_last_chat

app = typer.Typer(
    name="chat-scraper",
    # MODIFIED: Help text
    help="A CLI to download your ChatGPT conversations.",
    add_completion=False,
)
console = Console()


@app.command()
def last(
    port: Optional[int] = typer.Option(
        None,
        "--port",
        help="Connect to a running Chrome instance on this port (e.g., 9222).",
    ),
    first_run: bool = typer.Option(
        False,
        "--first-run",
        help="For standalone mode: Run in a visible browser to log in for the first time.",
    )
):
    """
    Downloads the most recent chat from your history.
    """
    if port and first_run:
        console.print("[bold red]Error:[/bold red] --port and --first-run are mutually exclusive.")
        raise typer.Exit(code=1)

    if first_run:
        console.print(
            Panel(
                "[bold yellow]ACTION REQUIRED[/bold yellow]\n\nA browser window will open. Please log in to your OpenAI account. The script will continue automatically after you're logged in.",
                title="First-Time Setup (Standalone Mode)",
                border_style="yellow",
            )
        )
    
    if port:
        console.print(f"[bold blue]Attempting to connect to Chrome on port {port}...[/bold blue]")

    # MODIFIED: Status text
    with console.status("[bold green]Downloading in progress...", spinner="dots") as status:
        try:
            status.update("Launching browser...")
            # MODIFIED: Call the renamed async function
            saved_file_path = asyncio.run(download_last_chat(connect_port=port, is_first_run=first_run))
            
            console.print(
                Panel(
                    f"[bold green]✅ Success![/bold green]\n\nConversation saved to:\n[cyan]{saved_file_path}[/cyan]",
                    # MODIFIED: Panel title
                    title="Download Complete",
                    border_style="green",
                )
            )
        except Error as e:
            error_message = str(e)
            if "net::ERR_CONNECTION_REFUSED" in error_message:
                error_message = f"Connection refused on port {port}. Is Chrome running with '--remote-debugging-port={port}'?"
            
            console.print(
                Panel(
                    f"[bold red]❌ An Error Occurred[/bold red]\n\n[white]{error_message}[/white]",
                    # MODIFIED: Panel title
                    title="Download Failed",
                    border_style="red",
                )
            )
            raise typer.Exit(code=1)

if __name__ == "__main__":
    app()