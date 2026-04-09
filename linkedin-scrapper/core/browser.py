from playwright.async_api import async_playwright
import asyncio
import time
import random

class BrowserManager:
    def __init__(self):
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None

    async def start(self, cookies=None):
        self.playwright = await async_playwright().start()
        self.browser = await self.playwright.chromium.launch(headless=False)
        self.context = await self.browser.new_context(
            user_agent="Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            viewport={"width": 1920, "height": 1080}
        )
        if cookies:
            await self.context.add_cookies(cookies)
        self.page = await self.context.new_page()
        
        # Apply anti-detection scripts
        js = """
        Object.defineProperty(navigator, 'webdriver', {
            get: () => undefined
        })
        """
        await self.page.add_init_script(js)

    async def navigate(self, url):
        print(f"Navigating to {url}...")
        await self.page.goto(url, wait_until="domcontentloaded")
        await self.human_delay()
        
    async def human_delay(self, min_sec=2, max_sec=5):
        delay = random.uniform(min_sec, max_sec)
        await asyncio.sleep(delay)
        
    async def scroll_down(self):
        await self.page.evaluate("window.scrollTo(0, document.body.scrollHeight);")
        await self.human_delay()

    async def get_html(self):
        return await self.page.content()

    async def get_cookies(self):
        return await self.context.cookies()

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
