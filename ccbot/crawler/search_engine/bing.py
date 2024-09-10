import logging
import re
import json
from copy import copy
from httpx import AsyncClient
from lxml import etree

from ...config import settings
from ..browser import get_page
from .base import SearchResultItem, SearchEngine

logger = logging.getLogger(__name__)

class BingContextManager:

    def __init__(self) -> None:
        self._cache = None

    async def new_context(self):
        async with get_page() as page:
            await page.goto("https://cn.bing.com/")
            await page.wait_for_selector('input[id="sb_form_q"]')
            cookies = await page.context.cookies()
            cookies = {
                item["name"]: item["value"] 
                for item in cookies
            }
            html = await page.content()
        m = re.search('_IG="(.*?)"', html) or re.search("IG:\"(.*?)\"", html)
        cvid = m.group(1)
        ctx = {
            "cookies": cookies,
            "params": {
                "cvid": cvid,
            }
        }
        logger.info("新生成上下文: %s", json.dumps(ctx, ensure_ascii=False))
        return ctx
    
    async def get_ctx(self, force=False):
        if self._cache is None or force:
            self._cache = await self.new_context()
        return self._cache

    async def clean_ctx(self):
        self._cache = None

default_manager = BingContextManager()


class Bing(SearchEngine):

    def __init__(self, ctx_manager=default_manager) -> None:
        super().__init__()
        self.ctx_manager = ctx_manager

    async def search(self, keyword):
        try:
            html = await self._request(keyword)
            result = self._parse(html)
            return result
        except Exception:
            logger.exception("搜索失败")
            return []

    async def _request(self, keyword):
        """
        参数解释 https://answers.fuyeor.com/zh-hans/question/6612
        """
        url = "https://cn.bing.com/search"
        ctx = await default_manager.get_ctx()
        logger.debug("载入上下文: %s", json.dumps(ctx, ensure_ascii=False))
        cookies = ctx.get("cookies")
        default_params = ctx["params"]
        async with AsyncClient(
            headers={"user-agent": settings.UA},
            verify=False,
            cookies=cookies,
            ) as client:
            params = copy(default_params)
            params.update({
                "q": keyword,
                "form": "QBRE",
                "sp": -1,
                "lq": 0,
                "pq": keyword,
                "sc": "0-8",
                # "qs": "n",
                "qs": "ds",
                "ghsh": 0,
                "ghacc": 0,
                "ghpl": "",
            })
            resp = await client.get(url, params=params, follow_redirects=True)
        return resp.text

    def _parse(self, html):
        tree = etree.HTML(html)
        items = tree.xpath('//ol[@id="b_results"]/li[@class="b_algo"]')
        results = []
        if items is None:
            return results
        for item in items:
            a = item.find("./h2/a")
            if a is None:
                # print("无效的item")
                # print( etree.tostring(item, encoding="unicode"))
                continue
            title = etree.tostring(a, method="text", encoding="unicode")
            title = re.sub(r"\s{2,}", " ", title)
            url = a.get("href")
            summary = item.find('./div[@class="b_caption"]')
            if summary is None:
                # print("无效的item")
                # print( etree.tostring(item, encoding="unicode"))
                continue
            summary = etree.tostring(summary, method="text", encoding="unicode")
            summary = re.sub(r"\s{2,}", " ", summary)
            if len(summary) > 13 and summary[13] == "·":
                summary = summary[15:]
                # pubdate = summary[:11]
            results.append(
                SearchResultItem(
                title=title,
                url=url,
                summary=summary,    )
            )
        return results

