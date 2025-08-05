# Developer Workflow

This document outlines the setup and workflow for contributing to the Chat Librarian project.

## Initial Setup

This project uses `uv` for environment and package management.

1.  **Create and Activate Environment**
    ```bash
    # Create the virtual environment in the .venv directory
    uv venv

    # Activate the environment
    # macOS / Linux
    source .venv/bin/activate
    # Windows
    # .venv\Scripts\activate
    ```

2.  **Install Dependencies**
    ```bash
    # Install the project in editable (-e) mode and its dependencies
    uv pip install -e .

    # Install Playwright's browser binaries
    playwright install
    ```

## Code Structure

-   **`pyproject.toml`**: Defines project metadata, dependencies, and the CLI entry point (`chat-librarian`).
-   **`chat_librarian/`**: The main source directory for the Python package.
    -   **`main.py`**: Contains all the `typer` CLI logic. This file handles user input, orchestrates the commands, and prints formatted output using `rich`.
    -   **`downloader.py`**: Contains the core browser automation logic within the `ChatDownloader` class. This module is responsible for all interactions with Playwright, including launching the browser, navigating, listing chats, and parsing conversation HTML.

## Running the Tool in Development

Because the tool is installed in editable mode, any changes you make to the `.py` files will be reflected immediately when you run the `chat-librarian` command from your terminal (as long as the virtual environment is active).

### Example Development Cycle

1.  Make a change to `chat_librarian/downloader.py`.
2.  Save the file.
3.  Run `chat-librarian select` in your terminal to test the change.
