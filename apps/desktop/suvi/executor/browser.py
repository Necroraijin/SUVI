from playwright.async_api import async_playwright
import asyncio

class BrowserExecutor:
    """Navigates the web and extracts data using Playwright."""

    def __init__(self):
        self.playwright = None
        self.browser = None
        self.page = None

    async def start(self):
        if not self.playwright:
            self.playwright = await async_playwright().start()
            # headless=False means you will actually see the browser pop up!
            self.browser = await self.playwright.chromium.launch(headless=False) 
            self.page = await self.browser.new_page()

    async def navigate(self, url: str) -> str:
        if not self.page:
            await self.start()
        
        try:
            # Ensure it has a protocol
            if not url.startswith("http"):
                url = "https://" + url
                
            await self.page.goto(url)
            title = await self.page.title()
            return f"Navigated to {url}. Page title is '{title}'."
        except Exception as e:
            return f"Failed to navigate: {e}"

    async def get_page_content(self) -> str:
        if not self.page:
            return "Error: Browser is not open."
            
        # Extract text from the body and truncate it so we don't blow up Gemini's context window
        content = await self.page.locator("body").inner_text()
        return content[:2000] 

    async def close(self):
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()