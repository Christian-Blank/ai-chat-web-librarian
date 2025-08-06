# Chat Librarian 🤖📚

A command-line tool to download your ChatGPT conversations locally as clean, formatted Markdown files.

## Features

-   **Interactive Mode**: Scans your entire chat history (even with lazy-loading) and lets you choose which conversation to download from a list.
-   **Download by Title**: Directly download a specific chat by providing its full title.
-   **Quick Download**: Instantly download your most recent conversation with a single command.
-   **High-Fidelity Markdown**: Preserves complex formatting, including paragraphs, lists, headings, and code blocks.
-   **Persistent Login**: Log in once, and the tool securely remembers your session for future use.
-   **Advanced Control**: Can connect to an existing Chrome browser session for seamless integration.

## Installation

This tool uses modern Python packaging and requires Python 3.11+.

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/Christian-Blank/ai-chat-web-librarian.git](https://github.com/Christian-Blank/ai-chat-web-librarian.git)
    cd chat-librarian
    ```

2.  **Set up the Environment with `uv`**
    ```bash
    # Create a virtual environment
    uv venv

    # Activate the environment
    source .venv/bin/activate
    ```

3.  **Install Dependencies**
    ```bash
    # Install the tool and its Python packages in editable mode
    uv pip install -e .

    # Install the necessary browser binaries for Playwright
    playwright install
    ```

## Usage

### First-Time Setup (Required)

The very first time you run the tool, you must use the `--first-run` flag. This will open a visible browser window where you can log in to your OpenAI account. Your session will be saved for all future runs.

```bash
chat-librarian select --first-run
```

### Interactive Mode (Default)

Run the `select` command to get an interactive list of your conversations.

```bash
chat-librarian select --first-run
```
The tool will display a table of your conversations. Enter the number of the chat you wish to download.

### Download by Title

Use the `title` command followed by the exact, case-insensitive title of the conversation in quotes.

```bash
chat-librarian title "My Important Research Chat" --first-run
```

### Quick Mode: Download Last Chat

To quickly save your most recent conversation, use the `last` command.

```bash
chat-librarian last --first-run
```

### Known Issues

-   **Headless Mode**: Currently, running the tool in headless mode (i.e., without the `--first-run` flag) is unstable and may result in a timeout. For reliable operation, please use the `--first-run` flag for all commands, which will open a visible browser window to perform the automation. This will be addressed in a future update.

## License

This project is licensed under the MIT License.