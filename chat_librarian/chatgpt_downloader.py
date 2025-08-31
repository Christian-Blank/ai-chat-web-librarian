from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup, NavigableString, Tag
from playwright.async_api import Error, Locator, Page

from chat_librarian.base_downloader import BaseChatDownloader

CHATGPT_URL: str = "https://chat.openai.com"
OUTPUT_DIR: Path = Path.cwd() / "ChatGPT_Downloads"
HISTORY_CONTAINER_SELECTOR: str = "div#history"
CHAT_LINK_SELECTOR: str = 'a[href^="/c/"]'
MESSAGE_AUTHOR_BLOCK_SELECTOR: str = "div[data-message-author-role]"


class ChatGPTDownloader(BaseChatDownloader):
    """ChatGPT-specific implementation of chat downloader."""

    @property
    def platform_url(self) -> str:
        return CHATGPT_URL

    @property
    def platform_name(self) -> str:
        return "ChatGPT"

    @property
    def output_dir(self) -> Path:
        return OUTPUT_DIR

    async def _platform_init(self) -> None:
        """Handle ChatGPT-specific initialization."""
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        print("Checking for and dismissing any post-login modals...")
        try:
            dismiss_button = self.page.get_by_role("button", name="Okay, let's go")
            await dismiss_button.click(timeout=5000)
            print("Dismissed a welcome modal.")
        except Error:
            print("No initial modal found. Continuing.")

    async def list_chats(self) -> List[Dict[str, Any]]:
        """List all ChatGPT conversations."""
        print("Waiting for chat history to be fully loaded...")
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        history_container = self.page.locator(HISTORY_CONTAINER_SELECTOR)
        chat_links_locator = history_container.locator(CHAT_LINK_SELECTOR)
        await chat_links_locator.first.wait_for()

        print("Chat history is loaded. Scrolling to reveal all conversations...")
        last_count = 0
        scroll_attempts = 0
        max_scroll_attempts = 5

        while scroll_attempts < max_scroll_attempts:
            await chat_links_locator.last.hover()
            await self.page.mouse.wheel(0, 1000)
            await self.page.wait_for_timeout(1500)
            current_count = await chat_links_locator.count()
            print(f"  ...found {current_count} chats so far.")

            if current_count == last_count:
                scroll_attempts += 1
            else:
                scroll_attempts = 0
            last_count = current_count

        print(f"Finished scrolling. Total chats found: {last_count}")
        all_chats = await chat_links_locator.all()
        chat_data = []

        for i, chat_locator in enumerate(all_chats):
            try:
                title = await chat_locator.inner_text()
                if title:
                    chat_data.append(
                        {"index": i, "title": title.strip(), "locator": chat_locator}
                    )
            except Error:
                print(f"Warning: Could not read title for chat at index {i}. Skipping.")

        return sorted(chat_data, key=lambda x: x["index"], reverse=True)

    async def download_chat(self, chat_title: str, chat_locator: Locator) -> Path:
        """Download a specific ChatGPT conversation."""
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        print(f"Targeting chat: '{chat_title}'")
        await chat_locator.click()

        downloaded_content = await self._extract_conversation_content(self.page)
        return self._save_chat_content(chat_title, downloaded_content)

    async def _extract_conversation_content(self, page: Page) -> str:
        """Extract and format ChatGPT conversation content."""
        print("Waiting for chat content to be fully loaded...")
        await page.locator(MESSAGE_AUTHOR_BLOCK_SELECTOR).first.wait_for()
        await page.wait_for_load_state("networkidle", timeout=30000)
        print("Chat content is loaded.")

        formatted_text: list[str] = []
        message_blocks = await page.locator(MESSAGE_AUTHOR_BLOCK_SELECTOR).all()
        print(f"Parsing content from {len(message_blocks)} message blocks...")

        for i, block in enumerate(message_blocks):
            role = await block.get_attribute("data-message-author-role")
            role_display = "User" if role == "user" else "Assistant"
            html_content = await block.inner_html()

            soup = BeautifulSoup(html_content, "lxml")
            content_container = soup.find("div", class_="markdown") or soup.find(
                "div", class_="whitespace-pre-wrap"
            )

            content_text = ""
            if content_container and isinstance(content_container, Tag):
                content_text = self._parse_soup_to_markdown(content_container)

            formatted_text.append(f"### {role_display}\n\n{content_text}\n\n---\n")

            if (i + 1) % 5 == 0:
                print(f"  ...parsed message {i + 1}/{len(message_blocks)}")

        return "\n".join(formatted_text)

    def _parse_soup_to_markdown(self, soup_container: Tag) -> str:
        """Convert ChatGPT HTML content to Markdown."""
        content_parts = []
        for element in soup_container.contents:
            if isinstance(element, NavigableString) and element.strip():
                content_parts.append(element.strip())
                continue

            if not hasattr(element, "name"):
                continue

            if isinstance(element, Tag):
                if element.name == "p":
                    content_parts.append(element.get_text())
                elif element.name in ["ol", "ul"]:
                    list_items = []
                    li_elements = element.find_all("li", recursive=False)
                    for li in li_elements:
                        prefix = "1." if element.name == "ol" else "*"
                        li_text = li.get_text().strip()
                        list_items.append(f"{prefix} {li_text}")
                    content_parts.append("\n".join(list_items))
                elif element.name == "pre":
                    code_language_div = element.find("div")
                    code_language = ""
                    if (
                        code_language_div
                        and isinstance(code_language_div, Tag)
                        and code_language_div.get("class")
                    ):
                        class_list = code_language_div.get("class")
                        if class_list:
                            lang_class = [
                                c for c in class_list if c.startswith("language-")
                            ]
                            if lang_class:
                                code_language = lang_class[0].replace("language-", "")
                    code_element = element.find("code")
                    code_text = (
                        code_element.get_text() if code_element else ""
                    )
                    content_parts.append(f"```{code_language}\n{code_text}\n```")
                elif element.name in ["h1", "h2", "h3", "h4"]:
                    level = int(element.name[1])
                    content_parts.append(f"{'#' * level} {element.get_text()}")

        return "\n\n".join(part for part in content_parts if part)
