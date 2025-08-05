import asyncio
from typing import Optional

import typer
from playwright.async_api import Error
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from chat_librarian.downloader import ChatDownloader

app = typer.Typer(
    name="chat-librarian",
    help="A CLI to download your ChatGPT conversations.",
    add_completion=False,
    no_args_is_help=True,
)
console = Console()

async def run_interactive_session(port: Optional[int], first_run: bool):
    """Handles the interactive chat selection and download."""
    async with ChatDownloader(connect_port=port, is_first_run=first_run) as downloader:
        with console.status("[bold green]Fetching chat list..."):
            chats = await downloader.list_chats()
        
        if not chats:
            console.print("[bold red]No chats found in the sidebar.[/bold red]")
            return

        table = Table(title="Available ChatGPT Conversations", show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Title")
        
        for i, chat in enumerate(chats, 1):
            table.add_row(str(i), chat['title'])
        
        console.print(table)
        
        try:
            choice_str = typer.prompt("\nEnter the number of the chat to download (or 'q' to quit)")
            if choice_str.lower() == 'q':
                console.print("Quitting.")
                return

            choice = int(choice_str) - 1
            if not 0 <= choice < len(chats):
                console.print("[bold red]Invalid selection.[/bold red]")
                return
            
            selected_chat = chats[choice]
            
            with console.status(f"[bold green]Downloading '{selected_chat['title']}'..."):
                 saved_file_path = await downloader.download_chat(
                     chat_title=selected_chat['title'],
                     chat_locator=selected_chat['locator']
                 )
            
            console.print(
                Panel(
                    f"[bold green]✅ Success![/bold green]\n\nConversation saved to:\n[cyan]{saved_file_path}[/cyan]",
                    title="Download Complete",
                    border_style="green",
                )
            )

        except (ValueError, IndexError):
            console.print("[bold red]Invalid input. Please enter a number from the list.[/bold red]")

@app.command(name="select", help="Select a chat to download from an interactive list. [default]")
def select_chat(
    port: Optional[int] = typer.Option(None, "--port", help="Connect to a running Chrome instance on this port (e.g., 9222)."),
    first_run: bool = typer.Option(False, "--first-run", help="For standalone mode: Run in a visible browser for the first time."),
):
    """The default command, allowing interactive chat selection."""
    if first_run:
        console.print(Panel("[bold yellow]ACTION REQUIRED[/bold yellow]\n\nA browser window will open. Please log in to your OpenAI account. The script will continue automatically after you're logged in.", title="First-Time Setup"))
    
    try:
        asyncio.run(run_interactive_session(port, first_run))
    except Error as e:
        console.print(Panel(f"[bold red]❌ An Error Occurred[/bold red]\n\n[white]{e}[/white]", title="Download Failed", border_style="red"))
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")


@app.command(name="last", help="Quickly download the most recent chat.")
def download_last(
    port: Optional[int] = typer.Option(None, "--port", help="Connect to a running Chrome instance on this port (e.g., 9222)."),
    first_run: bool = typer.Option(False, "--first-run", help="For standalone mode: Run in a visible browser for the first time."),
):
    """Downloads the most recent chat non-interactively."""
    if first_run:
        console.print(Panel("[bold yellow]ACTION REQUIRED[/bold yellow]\n\nA browser window will open. Please log in to your OpenAI account. The script will continue automatically after you're logged in.", title="First-Time Setup"))

    async def run_last_session():
        async with ChatDownloader(connect_port=port, is_first_run=first_run) as downloader:
            with console.status("[bold green]Fetching chat list..."):
                chats = await downloader.list_chats()
            
            if not chats:
                console.print("[bold red]No chats found in the sidebar.[/bold red]")
                return

            latest_chat = chats[0]
            with console.status(f"[bold green]Downloading '{latest_chat['title']}'..."):
                 saved_file_path = await downloader.download_chat(
                     chat_title=latest_chat['title'],
                     chat_locator=latest_chat['locator']
                 )
            
            console.print(
                Panel(
                    f"[bold green]✅ Success![/bold green]\n\nConversation saved to:\n[cyan]{saved_file_path}[/cyan]",
                    title="Download Complete",
                    border_style="green",
                )
            )

    try:
        asyncio.run(run_last_session())
    except Error as e:
        console.print(Panel(f"[bold red]❌ An Error Occurred[/bold red]\n\n[white]{e}[/white]", title="Download Failed", border_style="red"))
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")

@app.command(name="title", help="Download a specific chat by its full title (case-insensitive).")
def by_title(
    title: str = typer.Argument(..., help="The exact, case-insensitive title of the chat to download."),
    port: Optional[int] = typer.Option(None, "--port", help="Connect to a running Chrome instance on this port."),
    first_run: bool = typer.Option(False, "--first-run", help="For standalone mode: Run in a visible browser for the first time."),
):
    """Downloads a chat by matching its title."""
    if first_run:
        console.print(Panel("[bold yellow]ACTION REQUIRED[/bold yellow]\n\nA browser window will open. Please log in to your OpenAI account. The script will continue automatically after you're logged in.", title="First-Time Setup"))

    async def run_title_session():
        async with ChatDownloader(connect_port=port, is_first_run=first_run) as downloader:
            with console.status(f"[bold green]Searching for chat titled '{title}'..."):
                saved_file_path = await downloader.download_chat_by_title(title)
            
            console.print(
                Panel(
                    f"[bold green]✅ Success![/bold green]\n\nConversation saved to:\n[cyan]{saved_file_path}[/cyan]",
                    title="Download Complete",
                    border_style="green",
                )
            )

    try:
        asyncio.run(run_title_session())
    except (Error, ValueError) as e:
        console.print(Panel(f"[bold red]❌ An Error Occurred[/bold red]\n\n[white]{e}[/white]", title="Download Failed", border_style="red"))
        raise typer.Exit(code=1)
    except KeyboardInterrupt:
        console.print("\n[bold yellow]Operation cancelled by user.[/bold yellow]")

if __name__ == "__main__":
    app()