# Chat Librarian 🤖📚

A command-line tool to download your conversations from ChatGPT and Gemini locally as clean, formatted Markdown files.

## Features

-   **Multi-Platform Support**: Download conversations from both ChatGPT and Gemini with unified commands.
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

### Platform Selection

All commands support the `--platform` parameter to choose between ChatGPT and Gemini. The default is ChatGPT for backward compatibility.

### First-Time Setup (Required)

The very first time you run the tool, you must use the `--first-run` flag. This will open a visible browser window where you can log in to your account. Your session will be saved for all future runs.

**For ChatGPT (default):**
```bash
chat-librarian select --first-run
# or explicitly
chat-librarian select --platform chatgpt --first-run
```

**For Gemini:**
```bash
chat-librarian select --platform gemini --first-run
```

### Interactive Mode (Default)

Run the `select` command to get an interactive list of your conversations.

**ChatGPT:**
```bash
chat-librarian select --first-run
```

**Gemini:**
```bash
chat-librarian select --platform gemini --first-run
```

The tool will display a table of your conversations. Enter the number of the chat you wish to download.

### Download by Title

Use the `title` command followed by the exact, case-insensitive title of the conversation in quotes.

**ChatGPT:**
```bash
chat-librarian title "My Important Research Chat" --first-run
```

**Gemini:**
```bash
chat-librarian title "My Important Research Chat" --platform gemini --first-run
```

### Quick Mode: Download Last Chat

To quickly save your most recent conversation, use the `last` command.

**ChatGPT:**
```bash
chat-librarian last --first-run
```

**Gemini:**
```bash
chat-librarian last --platform gemini --first-run
```

### Debug Mode

For troubleshooting issues or getting detailed information about what the tool is doing, you can enable debug mode by adding the `--debug` flag to any command. This provides verbose logging with timing information, selector attempts, and detailed progress updates.

**Example with debug mode:**
```bash
chat-librarian select --platform gemini --first-run --debug
```

**Debug output includes:**
- Detailed selector attempts and results
- Performance timing for operations
- Platform-specific context information
- Enhanced error reporting with stack traces

**Production mode (default)** shows clean, user-friendly output:
```
ℹ️  [Gemini] Waiting for Gemini chat history to be loaded
ℹ️  [Gemini] Found 'Recent' section - chat history is loaded (586ms)
```

**Debug mode** shows detailed technical information:
```
2024-01-30T18:45:00.123456Z [info] [Gemini] Waiting for Gemini chat history to be loaded
2024-01-30T18:45:00.234567Z [debug] [Gemini] Trying selector (selector: text=Recent)
2024-01-30T18:45:00.345678Z [info] [Gemini] Selector found elements (selector: text=Recent, found: 1)
```

### Known Issues

-   **Headless Mode**: Currently, running the tool in headless mode (i.e., without the `--first-run` flag) is unstable and may result in a timeout. For reliable operation, please use the `--first-run` flag for all commands, which will open a visible browser window to perform the automation. This will be addressed in a future update.

## License

This project is licensed under the MIT License.
