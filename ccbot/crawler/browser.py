import asyncio

from playwright.async_api import Browser, async_playwright, Page
from contextlib import asynccontextmanager

from ccbot.config import settings


lock = asyncio.Lock()
browser: Browser|None = None
DEFAULT_BROWSER_TIMEOUT = 2000


async def get_browser():
    global browser
    if browser is None:
        async with lock:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch()
    return browser

@asynccontextmanager
async def get_page(init_script=True):
    browser = await get_browser()
    if init_script:
        ctx = await browser.new_context()
        await ctx.add_init_script(path=settings.INIT_SCRIPT)
        page:Page = await ctx.new_page()
    else:
        page:Page = await browser.new_page()
    try:
        yield page
    finally:
        await page.close()
        if init_script:
            await ctx.close()