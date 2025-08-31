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
  - **`main.py`**: Contains all the `typer` CLI logic with multi-platform support. This file handles user input, orchestrates the commands, and prints formatted output using `rich`.
  - **`base_downloader.py`**: Abstract base class that defines the common interface and shared functionality for all platform downloaders.
  - **`chatgpt_downloader.py`**: ChatGPT-specific implementation of the downloader, handling OpenAI authentication and ChatGPT DOM parsing.
  - **`gemini_downloader.py`**: Gemini-specific implementation of the downloader, handling Google authentication and Gemini DOM parsing.
  - **`logging_config.py`**: Structured logging configuration with production and debug modes, providing detailed troubleshooting capabilities.

## Running the Tool in Development

Because the tool is installed in editable mode, any changes you make to the `.py` files will be reflected immediately when you run the `chat-librarian` command from your terminal (as long as the virtual environment is active).

### Example Development Cycle

1. Make a change to a `.py` file (e.g., `chat_librarian/chatgpt_downloader.py` or `chat_librarian/gemini_downloader.py`).
2. Save the file.
3. Run the quality checks: `ruff format .`, `ruff check . --fix`, `mypy . --strict`.
4. Test the changes by running a command:

```bash
# Test ChatGPT interactive mode (default)
chat-librarian select --first-run

# Test Gemini interactive mode
chat-librarian select --platform gemini --first-run

# Test download by title for ChatGPT
chat-librarian title "Your Chat Title" --first-run

# Test download by title for Gemini
chat-librarian title "Your Chat Title" --platform gemini --first-run
```
