import logging
from enum import StrEnum
from httpx import AsyncClient, USE_CLIENT_DEFAULT, Response
from urllib.parse import urlsplit
import json


from .parser import CommonParser, Formats, DEFAULT_FORMANT, get_charset
from ccbot.config import settings
from ..browser import get_page, DEFAULT_BROWSER_TIMEOUT


logger = logging.getLogger(__name__)

class Mode(StrEnum):
    httpx = "httpx"
    browser = "browser"
    smart = "smart"


DEFAULT_MODE = Mode.smart


async def get_screen(url, timeout=-1):
    if timeout == -1:
        mstimeout = DEFAULT_BROWSER_TIMEOUT
    else:
        mstimeout = timeout * 1000
    async with get_page() as page:
        await page.goto(url)
        await page.wait_for_timeout(mstimeout)
        image = await page.screenshot(full_page=True)
    return image


class ContextManager:
    def __init__(self) -> None:
        self._cache = {}

    def _get_domain(self, url):
        u = urlsplit(url)
        domain = u.netloc
        return domain

    def get_ctx(self, url):
        domain = self._get_domain(url)
        ctx = self._cache.get(domain)
        return ctx

    def del_ctx(self, url):
        domain = self._get_domain(url)
        ctx = self._cache.pop(domain, None)
        return ctx

    def add_ctx(self, url, ctx):
        domain = self._get_domain(url)
        self._cache[domain] = ctx


default_manager = ContextManager()


async def get_html_by_browser(
    url,
    timeout=-1,
    formats=DEFAULT_FORMANT,
    init_script=True,
    keep_ctx=False,
):
    logger.info("正在使用模拟浏览器抓取: %s", url)
    if timeout == -1:
        mstimeout = DEFAULT_BROWSER_TIMEOUT
    else:
        mstimeout = timeout * 1000
    ctx = None
    async with get_page(init_script) as page:
        await page.goto(url)
        await page.wait_for_timeout(mstimeout)
        html = await page.content()
        parser = CommonParser(html, formats)
        result = parser.parse()
        if keep_ctx:
            cookies = await page.context.cookies(page.url)
            cookies = {item["name"]: item["value"] for item in cookies}
            ctx = {"cookies": cookies}
            logger.info("浏览器上下文已存储: %s", json.dumps(ctx, ensure_ascii=False))
    logger.debug("解析结果: %s", json.dumps(result, ensure_ascii=False))
    return result, ctx


async def get_html_by_httpx(url, timeout=-1, formats=None, ctx=None, check_text=False):
    logger.info("正在使用httpx抓取: %s", url)
    if timeout == -1:
        timeout = USE_CLIENT_DEFAULT
    cookies = None
    if ctx:
        logger.info("已加载上下文: %s", json.dumps(ctx))
        cookies = ctx.get("cookies")
    async with AsyncClient(
        headers={
            "User-Agent": settings.UA,
        },
        verify=False,
        cookies=cookies,
    ) as client:
        resp = await client.get(url, timeout=timeout, follow_redirects=True)
        html = resp.content
        charset = resp.charset_encoding
        if charset is None:
            charset = get_charset(html)
        charset = charset or "utf-8"
        html = html.decode(charset)
        parser = CommonParser(html, formats)
        result = parser.parse()
        ok = True
        if check_text:
            if Formats.text in formats:
                text = result["text"]
            else:
                text = parser.extract_text()
            text = text.strip()
            if len(text) < 10:
                ok = False
    logger.debug("解析结果: %s", json.dumps(result, ensure_ascii=False))
    return result, ok


async def smart_crawl(url, timeout, formats=DEFAULT_FORMANT, ctx_manager = default_manager):
    ctx = ctx_manager.get_ctx(url)
    try:
        result, ok = await get_html_by_httpx(url, timeout, formats, ctx, check_text=True)
    except Exception as e:
        logger.info("httpx抓取失败: %s", str(e))
        result = {}
        ok = False
    if not ok:
        logger.info("切换到浏览器请求模式: %s", url)
        result, ctx = await get_html_by_browser(url, timeout, formats, keep_ctx=True)
        ctx_manager.add_ctx(url, ctx)
    return result


async def common_crawl(url, timeout, formats=DEFAULT_FORMANT, mode=DEFAULT_MODE):
    if mode == Mode.smart:
        result = await smart_crawl(url, timeout, formats)
    elif mode == Mode.httpx:
        result, _ = await get_html_by_httpx(url, timeout, formats, ctx=None)
    elif mode == Mode.browser:
        result, _ = await get_html_by_browser(
            url, timeout, formats, init_script=True, keep_ctx=False
        )
    else:
        raise ValueError("无效的mode")
    return result
