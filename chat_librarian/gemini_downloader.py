from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.async_api import Error, Locator, Page

from chat_librarian.base_downloader import BaseChatDownloader

GEMINI_URL: str = "https://gemini.google.com/app"
OUTPUT_DIR: Path = Path.cwd() / "Gemini_Downloads"

# Gemini-specific selectors (based on DOM analysis from screenshots)
CHAT_HISTORY_CONTAINER_SELECTOR: str = "mat-sidenav"
CHAT_HISTORY_SCROLL_CONTAINER_SELECTOR: str = "div.chat-history-scroll-container"
CONVERSATION_CONTAINER_SELECTOR: str = "div.conversation-container"
USER_MESSAGE_SELECTOR: str = "div.user-query"
ASSISTANT_MESSAGE_SELECTOR: str = "div.model-response"
MESSAGE_CONTENT_SELECTOR: str = "div.message-content"


class GeminiDownloader(BaseChatDownloader):
    """Gemini-specific implementation of chat downloader."""

    @property
    def platform_url(self) -> str:
        return GEMINI_URL

    @property
    def platform_name(self) -> str:
        return "Gemini"

    @property
    def output_dir(self) -> Path:
        return OUTPUT_DIR

    async def _platform_init(self) -> None:
        """Handle Gemini-specific initialization."""
        print("Checking for Google authentication and any modals...")
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        # Wait for the page to load and check if we're logged in
        try:
            # Look for the typical Gemini interface elements
            await self.page.wait_for_selector("mat-sidenav", timeout=10000)
            print("Gemini interface loaded successfully.")
        except Error:
            print("Gemini interface not immediately available - may need to log in.")

        # Give some time for any modals or initialization to complete
        await self.page.wait_for_timeout(2000)

    async def list_chats(self) -> List[Dict[str, Any]]:
        """List all Gemini conversations."""
        print("Waiting for Gemini chat history to be loaded...")
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        # Wait for the sidebar to be present
        await self.page.wait_for_selector(
            CHAT_HISTORY_CONTAINER_SELECTOR, timeout=30000
        )

        # Look for chat history items within the sidebar
        # We need to be more flexible with selectors since the exact structure
        # might vary
        print("Searching for chat history items...")

        # Try different possible selectors for chat items
        possible_chat_selectors = [
            "div[role='button']",  # Chat items might be buttons
            "a[href*='chat']",  # Chat items might be links
            "div.chat-item",  # Generic chat item class
            "mat-list-item",  # Material design list items
        ]

        chat_elements = []
        for selector in possible_chat_selectors:
            try:
                elements = await self.page.locator(selector).all()
                if elements:
                    print(f"Found {len(elements)} elements with selector: {selector}")
                    # Filter elements that likely represent chats (contain text)
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if text and len(text.strip()) > 0:
                                chat_elements.append(element)
                        except Error:
                            continue
                    break
            except Error:
                continue

        if not chat_elements:
            print("No chat elements found, trying to scroll and search again...")
            # Try scrolling to load more chats
            sidebar = self.page.locator(CHAT_HISTORY_CONTAINER_SELECTOR)
            await sidebar.scroll_into_view_if_needed()
            await self.page.mouse.wheel(0, 1000)
            await self.page.wait_for_timeout(2000)

            # Retry finding elements
            for selector in possible_chat_selectors:
                try:
                    elements = await self.page.locator(selector).all()
                    if elements:
                        for element in elements:
                            try:
                                text = await element.inner_text()
                                if text and len(text.strip()) > 0:
                                    chat_elements.append(element)
                            except Error:
                                continue
                        if chat_elements:
                            break
                except Error:
                    continue

        print(f"Found {len(chat_elements)} potential chat elements")

        chat_data = []
        for i, chat_element in enumerate(chat_elements):
            try:
                title = await chat_element.inner_text()
                if title and title.strip():
                    # Clean up the title (remove extra whitespace, newlines)
                    clean_title = " ".join(title.strip().split())
                    # Skip very short titles that might be UI elements
                    if len(clean_title) > 5:
                        chat_data.append(
                            {"index": i, "title": clean_title, "locator": chat_element}
                        )
            except Error:
                print(f"Warning: Could not read title for chat at index {i}. Skipping.")

        print(f"Successfully parsed {len(chat_data)} chat conversations")
        return sorted(chat_data, key=lambda x: x["index"], reverse=True)

    async def download_chat(self, chat_title: str, chat_locator: Locator) -> Path:
        """Download a specific Gemini conversation."""
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        print(f"Targeting Gemini chat: '{chat_title}'")
        await chat_locator.click()

        # Wait for the conversation to load
        await self.page.wait_for_timeout(3000)

        downloaded_content = await self._extract_conversation_content(self.page)
        return self._save_chat_content(chat_title, downloaded_content)

    async def _extract_conversation_content(self, page: Page) -> str:
        """Extract and format Gemini conversation content."""
        print("Waiting for Gemini chat content to be fully loaded...")

        # Wait for conversation container
        try:
            await page.wait_for_selector(CONVERSATION_CONTAINER_SELECTOR, timeout=10000)
        except Error:
            # Fallback to waiting for any message content
            await page.wait_for_timeout(3000)

        print("Gemini chat content loaded, extracting messages...")

        formatted_text: list[str] = []

        # Try to find user and assistant messages
        try:
            # Look for user messages
            user_messages = await page.locator(USER_MESSAGE_SELECTOR).all()
            assistant_messages = await page.locator(ASSISTANT_MESSAGE_SELECTOR).all()

            print(
                f"Found {len(user_messages)} user messages and "
                f"{len(assistant_messages)} assistant messages"
            )

            # If we have specific message elements, process them
            if user_messages or assistant_messages:
                # Combine and sort messages by their position on the page
                all_messages = []

                for msg in user_messages:
                    try:
                        content = await self._extract_message_content(msg)
                        if content:
                            box = await msg.bounding_box()
                            all_messages.append(
                                ("User", content, box["y"] if box else 0)
                            )
                    except Error:
                        continue

                for msg in assistant_messages:
                    try:
                        content = await self._extract_message_content(msg)
                        if content:
                            box = await msg.bounding_box()
                            all_messages.append(
                                ("Assistant", content, box["y"] if box else 0)
                            )
                    except Error:
                        continue

                # Sort by y position to maintain conversation order
                all_messages.sort(key=lambda x: x[2])

                for role, content, _ in all_messages:
                    formatted_text.append(f"### {role}\n\n{content}\n\n---\n")

            else:
                # Fallback: try to extract all text content from the conversation area
                print("Fallback: extracting general conversation content...")
                conversation_area = page.locator(CONVERSATION_CONTAINER_SELECTOR)
                if await conversation_area.count() > 0:
                    content = await conversation_area.first.inner_text()
                    if content:
                        formatted_text.append(
                            f"### Conversation Content\n\n{content}\n\n---\n"
                        )

        except Error as e:
            print(f"Error extracting conversation: {e}")
            # Final fallback - get all visible text
            try:
                body_text = await page.locator("body").inner_text()
                formatted_text.append(f"### Full Page Content\n\n{body_text}\n\n---\n")
            except Error:
                formatted_text.append(
                    "### Error\n\nCould not extract conversation content.\n\n---\n"
                )

        return "\n".join(formatted_text) if formatted_text else "No content extracted."

    async def _extract_message_content(self, message_element: Locator) -> str:
        """Extract clean content from a message element."""
        try:
            # Try to get HTML content and parse it
            html_content = await message_element.inner_html()
            soup = BeautifulSoup(html_content, "lxml")

            # Remove script and style elements
            for element in soup(["script", "style"]):
                element.decompose()

            # Get clean text
            text = soup.get_text()

            # Clean up whitespace
            clean_text = " ".join(text.split())
            return clean_text

        except Error:
            # Fallback to plain text
            try:
                return await message_element.inner_text()
            except Error:
                return ""
