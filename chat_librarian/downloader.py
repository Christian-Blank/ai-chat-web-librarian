import asyncio
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from bs4 import BeautifulSoup, NavigableString
from playwright.async_api import BrowserContext, Error, Locator, Page, async_playwright
from playwright_stealth import Stealth

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

class ChatDownloader:
    def __init__(self, connect_port: Optional[int], is_first_run: bool):
        self.connect_port = connect_port
        self.is_first_run = is_first_run
        self.p = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.ACTION_TIMEOUT = 90000

    async def __aenter__(self):
        self.p = await async_playwright().start()
        stealth = Stealth()
        if self.connect_port:
            endpoint_url = f"http://localhost:{self.connect_port}"
            browser = await self.p.chromium.connect_over_cdp(endpoint_url)
            self.context = browser.contexts[0]
            await stealth.apply_stealth_async(self.context)
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        else:
            self.context = await self.p.chromium.launch_persistent_context(
                user_data_dir=USER_DATA_DIR,
                headless=not self.is_first_run,
                slow_mo=50,
            )
            await stealth.apply_stealth_async(self.context)
            self.page = self.context.pages[0] if self.context.pages else await self.context.new_page()
        
        self.page.set_default_timeout(self.ACTION_TIMEOUT)
        await self.page.goto(CHATGPT_URL)
        print("Checking for and dismissing any post-login modals...")
        try:
            dismiss_button = self.page.get_by_role("button", name="Okay, let’s go")
            await dismiss_button.click(timeout=5000)
            print("Dismissed a welcome modal.")
        except Error:
            print("No initial modal found. Continuing.")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.context and not self.connect_port:
            await self.context.close()
        if self.p:
            await self.p.stop()

    async def list_chats(self) -> List[Dict[str, Any]]:
        """Fetches ALL chat titles by simulating human-like scrolling."""
        print("Waiting for chat history to be fully loaded...")
        history_container = self.page.locator(HISTORY_CONTAINER_SELECTOR)
        chat_links_locator = history_container.locator(CHAT_LINK_SELECTOR)
        
        await chat_links_locator.first.wait_for()
        print("Chat history is loaded. Scrolling to reveal all conversations...")

        # --- NEW & IMPROVED SMART SCROLLING LOGIC ---
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 5 # Failsafe to prevent infinite loops

        while scroll_attempts < max_scroll_attempts:
            # Hover over the last visible chat link to ensure focus is in the scrollable area
            await chat_links_locator.last.hover()
            # Simulate scrolling the mouse wheel down
            await self.page.mouse.wheel(0, 1000) # Scroll down by 1000 pixels
            # Wait a moment for new content to lazy-load
            await self.page.wait_for_timeout(1500) 
            
            current_count = await chat_links_locator.count()
            print(f"  ...found {current_count} chats so far.")

            if current_count == last_count:
                # If the count hasn't changed, we might be at the bottom.
                # Increment our failsafe counter.
                scroll_attempts += 1
            else:
                # If we found new chats, reset the failsafe counter.
                scroll_attempts = 0
            
            last_count = current_count
        
        print(f"Finished scrolling. Total chats found: {last_count}")
        # --- END OF SMART SCROLLING LOGIC ---

        all_chats = await chat_links_locator.all()
        
        chat_data = []
        for i, chat_locator in enumerate(all_chats):
            try:
                title = await chat_locator.inner_text()
                if title:
                    chat_data.append({"index": i, "title": title.strip(), "locator": chat_locator})
            except Error:
                print(f"Warning: Could not read title for chat at index {i}. Skipping.")

        return sorted(chat_data, key=lambda x: x['index'], reverse=True)

    async def download_chat(self, chat_title: str, chat_locator: Locator) -> Path:
        print(f"Targeting chat: '{chat_title}'")
        await chat_locator.click()
        downloaded_content = await self._extract_conversation_content(self.page)
        safe_title = _sanitize_filename(chat_title)
        output_path = OUTPUT_DIR / f"{safe_title}.md"
        OUTPUT_DIR.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {chat_title}\n\n{downloaded_content}")
        return output_path

    async def _extract_conversation_content(self, page: Page) -> str:
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
            content_container = soup.find('div', class_='markdown') or soup.find('div', class_='whitespace-pre-wrap')
            content_text = ""
            if content_container:
                content_text = self._parse_soup_to_markdown(content_container)
            formatted_text.append(f"### {role_display}\n\n{content_text}\n\n---\n")
            if (i + 1) % 5 == 0:
                print(f"  ...parsed message {i + 1}/{len(message_blocks)}")
        return "\n".join(formatted_text)

    def _parse_soup_to_markdown(self, soup_container: BeautifulSoup) -> str:
        content_parts = []
        for element in soup_container.contents:
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
                    li_text = li.get_text().strip()
                    list_items.append(f"{prefix} {li_text}")
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
            elif element.name in ['h1', 'h2', 'h3', 'h4']:
                level = int(element.name[1])
                content_parts.append(f"{'#' * level} {element.get_text()}")
        return "\n\n".join(part for part in content_parts if part)