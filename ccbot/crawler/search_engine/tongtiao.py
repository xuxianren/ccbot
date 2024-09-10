import logging
import json
from typing import List

from httpx import AsyncClient
from lxml import etree

from ..browser import get_page

from .base import SearchEngine, SearchResultItem
from ccbot.config import settings

logger = logging.getLogger(__name__)

class ToutiaoContextManager:
    
    def __init__(self) -> None:
        self._cache = None

    async def new_context(self):
        async with get_page() as page:
            await page.goto("https://www.toutiao.com/")
            await page.wait_for_selector('input[aria-label="搜索"][autofocus]')
            cookies = await page.context.cookies(page.url)
            cookies = {
                item["name"]: item["value"] 
                for item in cookies
            }
            # html = await page.content()
            ctx = {
                "cookies": cookies,
            }
            logger.info("新生成上下文: %s", json.dumps(ctx, ensure_ascii=False))
            return ctx
    
    async def get_ctx(self, force=False):
        if self._cache is None or force:
            self._cache = await self.new_context()
        return self._cache

    async def clean_ctx(self):
        self._cache = None


default_manager = ToutiaoContextManager()


class Toutiao(SearchEngine):

    def __init__(self, ctx_manager=default_manager) -> None:
        super().__init__()
        self.ctx_manager = ctx_manager

    async def search(self, keyword:str)-> List[SearchResultItem]:
        try:
            html = await self._request(keyword)
            if html is not None:
                result = self._parse(html)
                return result
        except Exception:
            logger.exception("搜索失败")
            return []

    async def _request(self, keyword):
        url = "https://so.toutiao.com/search"
        ctx = await self.ctx_manager.get_ctx(force=False)
        logger.debug("载入上下文: %s", json.dumps(ctx, ensure_ascii=False))
        cookies = ctx.get("cookies")
        params = {
            "dvpf": "pc",
            "source": "input",
            "keyword": keyword,
        }
        async with AsyncClient(
            headers={"user-agent": settings.UA},
            verify=False,
            cookies=cookies,
        ) as client:
            resp = await client.get(url, params=params, follow_redirects=True)
            return resp.text

    def _parse_item(self, item):
        cell_type = item.get("cell_type")
        match cell_type:
            case 26:
                # 只要百科，忽略其它
                if item.get("ala_src") != "baike_hudong_structure_new":
                    return
                display = item["display"]
                title = display["title"]["text"]
                summary = display["summary"]["text"]
                url = display["info"]["url"]
                try:
                    summary = display["data_ext"]["summary"]
                except Exception:
                    pass
            case 67:
                url = item["url"]
                title = item["display"]["title"]["text"]
                summary = item["display"]["summary"]["text"]
            case None:
                url = item["article_url"]
                title = item["display"]["title"]["text"]
                summary = item["display"]["summary"]["text"]
            case _:
                return
        return SearchResultItem(
                    title=title,
                    url= url,
                    summary=summary,
                )

    def _parse(self, html):
        results = []
        tree = etree.HTML(html)
        data = tree.xpath("//script[@id='only_use_in_search_container']/text()")
        data = data[0]
        data = json.loads(data)
        for item in data["rawData"]["data"]:
            try:
                result_item = self._parse_item(item)
                if result_item is not None:
                    results.append(result_item)
            except Exception:
                pass
        return results