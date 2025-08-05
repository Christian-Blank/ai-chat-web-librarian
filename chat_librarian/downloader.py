import re
from pathlib import Path
from typing import Optional

from bs4 import BeautifulSoup, NavigableString
from playwright.async_api import BrowserContext, Error, Page, async_playwright
from playwright_stealth import Stealth

# --- Configuration & Selectors (All Correct) ---
USER_DATA_DIR: Path = Path.home() / ".chat_scraper_data"
CHATGPT_URL: str = "https://chat.openai.com"
OUTPUT_DIR: Path = Path.cwd() / "ChatGPT_Downloads"
HISTORY_CONTAINER_SELECTOR: str = "div#history"
CHAT_LINK_SELECTOR: str = 'a[href^="/c/"]'
MESSAGE_AUTHOR_BLOCK_SELECTOR: str = "div[data-message-author-role]"


def _sanitize_filename(name: str) -> str:
    """Removes invalid characters from a string to make it a valid filename."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()


# --- THIS IS THE ONLY FUNCTION THAT CHANGES (FINAL UPGRADE) ---
async def _extract_conversation_content(page: Page) -> str:
    """Extracts conversation text by intelligently converting message block HTML to Markdown."""
    
    print("Waiting for chat content to be fully loaded...")
    await page.locator(MESSAGE_AUTHOR_BLOCK_SELECTOR).first.wait_for()
    await page.wait_for_load_state('networkidle', timeout=30000)
    print("Chat content is loaded.")

    formatted_text: list[str] = []
    message_blocks = await page.locator(MESSAGE_AUTHOR_BLOCK_SELECTOR).all()

    print(f"Parsing content from {len(message_blocks)} message blocks...")
    for i, block in enumerate(message_blocks):
        role = await block.get_attribute("data-message-author-role")
        role_display = "User" if role == "user" else "Assistant"

        html_content = await block.inner_html()
        soup = BeautifulSoup(html_content, 'lxml')
        
        # FINAL UPGRADE: A more sophisticated HTML-to-Markdown conversion
        content_parts = []
        # Find the main container for the message content
        content_container = soup.find('div', class_='markdown') or soup.find('div', class_='whitespace-pre-wrap')

        if content_container:
            for element in content_container.contents:
                if isinstance(element, NavigableString) and element.strip():
                    content_parts.append(element.strip())
                    continue

                if not hasattr(element, 'name'):
                    continue

                if element.name == 'p':
                    content_parts.append(element.get_text())
                elif element.name in ['ol', 'ul']:
                    list_items = []
                    for li in element.find_all('li', recursive=False):
                        prefix = "1." if element.name == 'ol' else "*"
                        list_items.append(f"{prefix} {li.get_text()}")
                    content_parts.append("\n".join(list_items))
                elif element.name == 'pre':
                    code_language_div = element.find('div')
                    code_language = ''
                    if code_language_div and code_language_div.get('class'):
                        lang_class = [c for c in code_language_div['class'] if c.startswith('language-')]
                        if lang_class:
                            code_language = lang_class[0].replace('language-', '')
                    code_text = element.find('code').get_text() if element.find('code') else ''
                    content_parts.append(f"```{code_language}\n{code_text}\n```")
                elif element.name in ['h1', 'h2', 'h3']:
                    level = int(element.name[1])
                    content_parts.append(f"{'#' * level} {element.get_text()}")
        
        content_text = "\n\n".join(content_parts)
        
        formatted_text.append(f"### {role_display}\n\n{content_text}\n\n---\n")
        if (i + 1) % 5 == 0:
            print(f"  ...parsed message {i + 1}/{len(message_blocks)}")

    return "\n".join(formatted_text)


# --- This function remains perfect ---
async def download_last_chat(connect_port: Optional[int], is_first_run: bool) -> Path:
    """Automates downloading the last chat from ChatGPT."""
    # ... (This function is perfect and requires no changes) ...
    OUTPUT_DIR.mkdir(exist_ok=True)
    page: Optional[Page] = None
    context: Optional[BrowserContext] = None
    ACTION_TIMEOUT = 90000

    async with async_playwright() as p:
        stealth = Stealth()
        try:
            if connect_port:
                endpoint_url = f"http://localhost:{connect_port}"
                browser = await p.chromium.connect_over_cdp(endpoint_url)
                context = browser.contexts[0]
                await stealth.apply_stealth_async(context)
                page = context.pages[0] if context.pages else await context.new_page()
            else:
                context = await p.chromium.launch_persistent_context(
                    user_data_dir=USER_DATA_DIR,
                    headless=not is_first_run,
                    slow_mo=50,
                )
                await stealth.apply_stealth_async(context)
                page = context.pages[0] if context.pages else await context.new_page()
            
            page.set_default_timeout(ACTION_TIMEOUT)
            await page.goto(CHATGPT_URL)
            
            print("Checking for and dismissing any post-login modals...")
            try:
                dismiss_button = page.get_by_role("button", name="Okay, let’s go")
                await dismiss_button.click(timeout=5000)
                print("Dismissed a welcome modal.")
            except Error:
                print("No initial modal found. Continuing.")

            print("Waiting for chat history to be fully loaded...")
            history_container = page.locator(HISTORY_CONTAINER_SELECTOR)
            chat_links_locator = history_container.locator(CHAT_LINK_SELECTOR)
            await chat_links_locator.first.wait_for()
            print("Chat history is loaded.")
            
            chat_count = await chat_links_locator.count()
            if chat_count == 0:
                raise ValueError("No conversations found in the sidebar after waiting.")
            print(f"Found {chat_count} chats in the sidebar.")

            last_chat_link = chat_links_locator.last
            chat_title = await last_chat_link.inner_text()
            print(f"Targeting last chat: '{chat_title}'")
            await last_chat_link.click()

            downloaded_content = await _extract_conversation_content(page)
            safe_title = _sanitize_filename(chat_title)
            output_path = OUTPUT_DIR / f"{safe_title}.md"
            
            with open(output_path, "w", encoding="utf-8") as f:
                f.write(f"# {chat_title}\n\n{downloaded_content}")
            
            return output_path

        finally:
            if context and not connect_port:
                await context.close()