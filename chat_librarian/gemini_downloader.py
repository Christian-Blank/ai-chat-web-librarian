import time
from pathlib import Path
from typing import Any, Dict, List

from bs4 import BeautifulSoup
from playwright.async_api import Error, Locator, Page

from chat_librarian.base_downloader import BaseChatDownloader
from chat_librarian.logging_config import (
    get_logger,
    log_error,
    log_platform_action,
    log_selector_attempt,
    log_selector_failure,
    log_selector_success,
    log_timing,
)

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
        logger = get_logger()
        log_platform_action(
            "Checking for Google authentication and any modals", "Gemini"
        )
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        # Wait for the page to load and check if we're logged in
        try:
            log_selector_attempt("mat-sidenav", "Gemini")
            await self.page.wait_for_selector("mat-sidenav", timeout=10000)
            log_platform_action("Gemini interface loaded successfully", "Gemini")
        except Error:
            logger.warning(
                "Gemini interface not immediately available - may need to log in",
                platform="Gemini",
            )

        # Give some time for any modals or initialization to complete
        await self.page.wait_for_timeout(2000)

    async def list_chats(self) -> List[Dict[str, Any]]:
        """List all Gemini conversations."""
        logger = get_logger()
        start_time = time.time()
        log_platform_action("Waiting for Gemini chat history to be loaded", "Gemini")

        if self.page is None:
            raise RuntimeError("Page is not initialized")

        # Wait for the "Recent" heading to appear, which indicates chat history
        # is loaded
        try:
            log_selector_attempt("text=Recent", "Gemini")
            await self.page.wait_for_selector("text=Recent", timeout=30000)
            log_selector_success("text=Recent", 1, "Gemini")
            log_platform_action(
                "Found 'Recent' section - chat history is loaded", "Gemini"
            )
        except Error:
            logger.warning(
                "Could not find 'Recent' section, trying alternative selectors",
                platform="Gemini",
            )
            # Fallback: wait for the sidebar container
            log_selector_attempt(CHAT_HISTORY_CONTAINER_SELECTOR, "Gemini")
            await self.page.wait_for_selector(
                CHAT_HISTORY_CONTAINER_SELECTOR, timeout=30000
            )

        log_platform_action("Searching for chat history items", "Gemini")

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
                log_selector_attempt(selector, "Gemini")
                elements = await self.page.locator(selector).all()
                if elements:
                    log_selector_success(selector, len(elements), "Gemini")
                    # Filter elements that likely represent chats (contain text)
                    for element in elements:
                        try:
                            text = await element.inner_text()
                            if text and len(text.strip()) > 0:
                                chat_elements.append(element)
                        except Error:
                            continue
                    break
                else:
                    log_selector_failure(selector, "Gemini")
            except Error:
                log_selector_failure(selector, "Gemini")

        if not chat_elements:
            logger.info(
                "No chat elements found, trying to scroll and search again",
                platform="Gemini",
            )
            # Try scrolling to load more chats
            sidebar = self.page.locator(CHAT_HISTORY_CONTAINER_SELECTOR)
            await sidebar.scroll_into_view_if_needed()
            await self.page.mouse.wheel(0, 1000)
            await self.page.wait_for_timeout(2000)

            # Retry finding elements
            for selector in possible_chat_selectors:
                try:
                    log_selector_attempt(selector, "Gemini")
                    elements = await self.page.locator(selector).all()
                    if elements:
                        log_selector_success(selector, len(elements), "Gemini")
                        for element in elements:
                            try:
                                text = await element.inner_text()
                                if text and len(text.strip()) > 0:
                                    chat_elements.append(element)
                            except Error:
                                continue
                        if chat_elements:
                            break
                    else:
                        log_selector_failure(selector, "Gemini")
                except Error:
                    log_selector_failure(selector, "Gemini")

        logger.info(
            "Found potential chat elements", count=len(chat_elements), platform="Gemini"
        )

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
            except Error as e:
                logger.debug(
                    "Could not read title for chat element",
                    index=i,
                    platform="Gemini",
                    error=str(e),
                )

        # Log timing and results
        duration_ms = (time.time() - start_time) * 1000
        log_timing(
            "Chat history loaded", duration_ms, "Gemini", chat_count=len(chat_data)
        )

        return sorted(chat_data, key=lambda x: x["index"], reverse=True)

    async def download_chat(self, chat_title: str, chat_locator: Locator) -> Path:
        """Download a specific Gemini conversation."""
        if self.page is None:
            raise RuntimeError("Page is not initialized")

        log_platform_action("Targeting Gemini chat", "Gemini", chat_title=chat_title)
        await chat_locator.click()

        # Wait for the conversation to load
        await self.page.wait_for_timeout(3000)

        downloaded_content = await self._extract_conversation_content(self.page)
        return self._save_chat_content(chat_title, downloaded_content)

    async def _extract_conversation_content(self, page: Page) -> str:
        """Extract and format Gemini conversation content."""
        logger = get_logger()
        log_platform_action(
            "Waiting for Gemini chat content to be fully loaded", "Gemini"
        )

        # Wait for conversation container
        try:
            log_selector_attempt(CONVERSATION_CONTAINER_SELECTOR, "Gemini")
            await page.wait_for_selector(CONVERSATION_CONTAINER_SELECTOR, timeout=10000)
            log_selector_success(CONVERSATION_CONTAINER_SELECTOR, 1, "Gemini")
        except Error:
            logger.warning(
                "Could not find conversation container, using timeout fallback",
                platform="Gemini",
            )
            # Fallback to waiting for any message content
            await page.wait_for_timeout(3000)

        log_platform_action("Gemini chat content loaded, extracting messages", "Gemini")

        formatted_text: list[str] = []

        # Try to find user and assistant messages
        try:
            # Look for user messages
            user_messages = await page.locator(USER_MESSAGE_SELECTOR).all()
            assistant_messages = await page.locator(ASSISTANT_MESSAGE_SELECTOR).all()

            logger.info(
                "Found message elements",
                user_messages=len(user_messages),
                assistant_messages=len(assistant_messages),
                platform="Gemini",
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
                logger.info(
                    "Fallback: extracting general conversation content",
                    platform="Gemini",
                )
                conversation_area = page.locator(CONVERSATION_CONTAINER_SELECTOR)
                if await conversation_area.count() > 0:
                    content = await conversation_area.first.inner_text()
                    if content:
                        formatted_text.append(
                            f"### Conversation Content\n\n{content}\n\n---\n"
                        )

        except Error as e:
            log_error("Error extracting conversation", e, "Gemini")
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
