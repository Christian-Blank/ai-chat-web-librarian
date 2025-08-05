# Chat Librarian 🤖📚

A command-line tool to download and manage your ChatGPT, Gemini, Claude conversations locally as clean, formatted Markdown files in git.

## Features

-   **Interactive Mode**: Lists all your recent conversations and lets you choose which one to download.
-   **Quick Download**: Instantly download your very last conversation with a single command.
-   **High-Fidelity Markdown**: Preserves complex formatting, including paragraphs, lists, headings, and code blocks with syntax highlighting.
-   **Persistent Login**: Log in once, and the tool securely remembers your session for future use.
-   **Advanced Control**: Can connect to an existing Chrome browser session for seamless integration.

## Installation

This tool uses modern Python packaging and requires Python 3.11+.

1.  **Clone the Repository**
    ```bash
    git clone [https://github.com/Christian-Blank/ai-chat-web-librarian.git](https://github.com/Christian-Blank/ai-chat-web-librarian.git)
    cd ai-chat-web-librarian
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

### First-Time Setup

The very first time you run the tool, you must use the `--first-run` flag. This will open a visible browser window where you can log in to your OpenAI account. Your session will be saved for all future runs.

```bash
chat-librarian select --first-run
```

### Interactive Mode (Default)

Simply run the tool without any commands to get an interactive list of your recent chats.

```bash
chat-librarian select
# Or just:
chat-librarian
```

The tool will display a table of your conversations. Enter the number of the chat you wish to download.

### Quick Mode: Download Last Chat

To quickly save your most recent conversation without any prompts, use the `last` command.

```bash
chat-librarian last
```

### Advanced: Connect to an Existing Browser

If you prefer to use your main Chrome browser that's already running, you can!

1.  **Launch Chrome with a debugging port.**
    -   **macOS**: `"/Applications/Google Chrome.app/Contents/MacOS/Google Chrome" --remote-debugging-port=9222`
    -   **Windows**: `& "C:\Program Files\Google\Chrome\Application\chrome.exe" --remote-debugging-port=9222`

2.  **Run the tool with the `--port` flag.**
    ```bash
    chat-librarian select --port 9222
    ```

## License

This project is licensed under the MIT License.