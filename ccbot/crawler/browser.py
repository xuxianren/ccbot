import asyncio

from playwright.async_api import Browser, async_playwright, Page
from contextlib import asynccontextmanager

from ccbot.config import settings


lock = asyncio.Lock()
browser: Browser | None = None
DEFAULT_BROWSER_TIMEOUT = 2000


async def get_browser():
    global browser
    if browser is None:
        async with lock:
            playwright = await async_playwright().start()
            browser = await playwright.chromium.launch(headless=True)
    return browser


async def handle_route(route):
    headers = route.request.headers
    headers.update(
        {
            "sec-ch-ua": '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            "Accept-Language": "zh-CN,zh;q=0.9",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36",
        }
    )
    await route.continue_(headers=headers)


@asynccontextmanager
async def get_page(init_script=True):
    browser = await get_browser()
    if init_script:
        ctx = await browser.new_context()
        await ctx.add_init_script(path=settings.INIT_SCRIPT)
        page: Page = await ctx.new_page()
    else:
        page: Page = await browser.new_page()
    await page.route("**/*", handle_route)
    try:
        yield page
    finally:
        await page.close()
        if init_script:
            await ctx.close()
