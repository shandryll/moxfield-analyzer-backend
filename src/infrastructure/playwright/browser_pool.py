import asyncio
import os
from playwright.async_api import async_playwright, Browser, Page

MAX_USES = int(os.getenv("BROWSER_POOL_MAX_USES", "50"))
MOXFIELD_REFERER = os.getenv("MOXFIELD_REFERER", "https://moxfield.com/")
MOXFIELD_ORIGIN = os.getenv("MOXFIELD_ORIGIN", "https://moxfield.com")


class BrowserPool:
    def __init__(self) -> None:
        self._browser: Browser | None = None
        self._use_count = 0
        self._playwright_instance = None
        self._lock = asyncio.Lock()

    async def get_page(self) -> Page:
        async with self._lock:
            if not self._browser or not self._browser.is_connected():
                if self._playwright_instance is None:
                    self._playwright_instance = await async_playwright().start()
                self._browser = await self._launch_browser()
                self._use_count = 0

            self._use_count += 1
            if self._use_count >= MAX_USES:
                old = self._browser
                self._browser = await self._launch_browser()
                self._use_count = 0
                await old.close()

            context = await self._browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/120.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1920, "height": 1080},
                extra_http_headers={
                    "Accept": "application/json, text/plain, */*",
                    "Accept-Language": "en-US,en;q=0.9",
                    "Referer": MOXFIELD_REFERER,
                    "Origin": MOXFIELD_ORIGIN,
                },
            )
            return await context.new_page()

    async def _launch_browser(self) -> Browser:
        return await self._playwright_instance.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
            ],
        )

    async def close(self) -> None:
        if self._browser:
            await self._browser.close()
            self._browser = None
        if self._playwright_instance:
            await self._playwright_instance.stop()
            self._playwright_instance = None


_browser_pool: BrowserPool | None = None


def get_browser_pool() -> BrowserPool:
    global _browser_pool
    if _browser_pool is None:
        _browser_pool = BrowserPool()
    return _browser_pool


async def close_browser_pool() -> None:
    global _browser_pool
    if _browser_pool:
        await _browser_pool.close()
        _browser_pool = None
