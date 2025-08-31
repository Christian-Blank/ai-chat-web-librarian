import re
from abc import ABC, abstractmethod
from pathlib import Path
from types import TracebackType
from typing import Any, Dict, List, Optional, Self

from playwright.async_api import (
    BrowserContext,
    Locator,
    Page,
    Playwright,
    async_playwright,
)
from playwright_stealth import Stealth

USER_DATA_DIR: Path = Path.home() / ".chat_scraper_data"


def _sanitize_filename(name: str) -> str:
    """Sanitize a filename by removing invalid characters."""
    name = re.sub(r'[\\/*?:"<>|]', "", name)
    return name.strip()


class BaseChatDownloader(ABC):
    """Abstract base class for chat downloaders."""

    def __init__(self, connect_port: Optional[int], is_first_run: bool) -> None:
        self.connect_port = connect_port
        self.is_first_run = is_first_run
        self.p: Optional[Playwright] = None  # Playwright instance
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.ACTION_TIMEOUT = 90000

    @property
    @abstractmethod
    def platform_url(self) -> str:
        """URL for the chat platform."""
        pass

    @property
    @abstractmethod
    def platform_name(self) -> str:
        """Human-readable platform name."""
        pass

    @property
    @abstractmethod
    def output_dir(self) -> Path:
        """Directory where downloads should be saved."""
        pass

    async def __aenter__(self) -> Self:
        """Initialize the browser and navigate to the platform."""
        self.p = await async_playwright().start()
        if self.p is None:
            raise RuntimeError("Playwright initialization failed.")
        stealth = Stealth()

        if self.connect_port:
            endpoint_url = f"http://localhost:{self.connect_port}"
            browser = await self.p.chromium.connect_over_cdp(endpoint_url)
            self.context = browser.contexts[0]
            await stealth.apply_stealth_async(self.context)
            self.page = (
                self.context.pages[0]
                if self.context.pages
                else await self.context.new_page()
            )
        else:
            # Use platform-specific user data directory
            user_data_dir = USER_DATA_DIR / f"{self.platform_name.lower()}_data"
            self.context = await self.p.chromium.launch_persistent_context(
                user_data_dir=user_data_dir,
                headless=not self.is_first_run,
                args=["--disable-blink-features=AutomationControlled"],
                user_agent=(
                    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/125.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                screen={"width": 1920, "height": 1080},
                java_script_enabled=True,
            )
            await stealth.apply_stealth_async(self.context)
            self.page = (
                self.context.pages[0]
                if self.context.pages
                else await self.context.new_page()
            )

        self.page.set_default_timeout(self.ACTION_TIMEOUT)
        await self.page.goto(self.platform_url, wait_until="domcontentloaded")

        # Platform-specific initialization
        await self._platform_init()

        return self

    async def __aexit__(
        self,
        exc_type: Optional[type[BaseException]],
        exc_val: Optional[BaseException],
        exc_tb: Optional[TracebackType],
    ) -> Optional[bool]:
        """Clean up browser resources."""
        if self.context and not self.connect_port:
            await self.context.close()
            return True
        if self.p:
            await self.p.stop()
            return True
        return False

    @abstractmethod
    async def _platform_init(self) -> None:
        """Platform-specific initialization after navigation."""
        pass

    @abstractmethod
    async def list_chats(self) -> List[Dict[str, Any]]:
        """List all available chats for the platform."""
        pass

    async def download_chat_by_title(self, target_title: str) -> Path:
        """Download a chat by its exact title (case-insensitive)."""
        all_chats = await self.list_chats()
        found_chat = None
        for chat in all_chats:
            if chat["title"].lower() == target_title.lower():
                found_chat = chat
                break
        if not found_chat:
            raise ValueError(
                f"No chat found with the exact title (case-insensitive): "
                f"'{target_title}'"
            )
        return await self.download_chat(
            chat_title=found_chat["title"], chat_locator=found_chat["locator"]
        )

    @abstractmethod
    async def download_chat(self, chat_title: str, chat_locator: Locator) -> Path:
        """Download a specific chat."""
        pass

    def _save_chat_content(self, chat_title: str, content: str) -> Path:
        """Save chat content to a markdown file."""
        safe_title = _sanitize_filename(chat_title)
        output_path = self.output_dir / f"{safe_title}.md"
        self.output_dir.mkdir(exist_ok=True)
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(f"# {chat_title}\n\n{content}")
        return output_path

    @abstractmethod
    async def _extract_conversation_content(self, page: Page) -> str:
        """Extract and format conversation content from the current page."""
        pass
