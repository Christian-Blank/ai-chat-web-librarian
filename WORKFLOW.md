# Developer Workflow

This document outlines the setup and workflow for contributing to the Chat Librarian project.

## Initial Setup

This project uses `uv` for environment and package management.

1. **Create and Activate Environment**

    ```bash
    # Create the virtual environment in the .venv directory
    uv venv -p 3.13

    # Activate the environment
    # macOS / Linux
    source .venv/bin/activate
    # Windows
    # .venv\Scripts\activate
    ```

2. **Install Dependencies**

    ```bash
    # Install the project and all development dependencies in editable mode
    uv pip install -e ".[dev]"

    # Install Playwright's browser binaries
    playwright install
    ```

## Code Quality & Style

This project uses `ruff` for formatting/linting and `mypy` for type checking. Before committing code, please run the following commands to ensure code quality and consistency.

1. **Format Code**

    ```bash
    ruff format .
    ```

2. **Lint and Auto-fix Issues**

    ```bash
    ruff check . --fix
    ```

3. **Run Type Checking**

    ```bash
    mypy . --strict
    ```

## Code Structure

- **`pyproject.toml`**: Defines project metadata, dependencies (including development dependencies), and the CLI entry point (`chat-librarian`).
- **`chat_librarian/`**: The main source directory for the Python package.
  - **`main.py`**: Contains all the `typer` CLI logic. This file handles user input, orchestrates the commands, and prints formatted output using `rich`.
  - **`downloader.py`**: Contains the core browser automation logic within the `ChatDownloader` class. This module is responsible for all interactions with Playwright.

## Running the Tool in Development

Because the tool is installed in editable mode, any changes you make to the `.py` files will be reflected immediately when you run the `chat-librarian` command from your terminal (as long as the virtual environment is active).

### Example Development Cycle

1. Make a change to a `.py` file (e.g., `chat_librarian/downloader.py`).
2. Save the file.
3. Run the quality checks: `ruff format .`, `ruff check . --fix`, `mypy . --strict`.
4. Test the changes by running a command:

```bash
# Test interactive mode
chat-librarian select --first-run

# Test download by title
chat-librarian title "Your Chat Title" --first-run
```
