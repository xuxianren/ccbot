from enum import StrEnum
from httpx import AsyncClient
from urllib.parse import urljoin

class Mode(StrEnum):
    httpx = "httpx"
    browser = "browser"
    smart = "smart"

class Formats(StrEnum):
    html = "html"
    title_ = "title"
    metadata = "metadata"
    text = "text"
    links = "links"
    main_content = "main_content"
    markdown = "markdown"

class EngineEnum(StrEnum):
    bing = "bing"
    toutiao = "toutiao"

default_formats = (Formats.title_, Formats.main_content)

class CcbotClient:

    def __init__(self, baseurl="http://localhost:8000") -> None:
        self.client = AsyncClient()
        self.baseurl = baseurl
    
    async def __aenter__(self):
        await self.client.__aenter__()
        return self
    
    async def __aexit__(self, exc_type=None, exc_value=None, traceback=None):
        await self.client.__aexit__(exc_type, exc_value, traceback)

    async def post(self, url, **kwargs):
        resp = await self.client.post(
            url,
            **kwargs
        )
        result = resp.json()
        return result

    async def search(self, keyword, engine=EngineEnum.toutiao, timeout=-1)->dict:
        api = urljoin(self.baseurl, "/search")
        data = {
            "keyword": keyword,
            "engine": engine,
            "timeout": timeout,
        }
        return await self.post(api, json=data)

    async def crawl(self, url, formats=default_formats, timeout=-1, mode=Mode.smart)->dict:
        api = urljoin(self.baseurl, "/crawl")
        data = {
            "url": url,
            "formats": formats,
            "timeout": timeout,
            "mode": mode,
        }
        return await self.post(api, json=data)

    async def screen(self, url, timemout=-1)->bytes:
        api = urljoin(self.baseurl, "/screen")
        data = {
            "url": url,
            "timemout": timemout,
        }
        resp = await self.client.post(
            api,
            json=data,
        )
        result = resp.content
        return result

    async def extract(self, html, formats=default_formats)->dict:
        api = urljoin(self.baseurl, "/extract")
        data = {
            "html": html,
            "formats": formats,
        }
        return await self.post(api, json=data)


if __name__ == "__main__":
    import asyncio

    async def test():
        async with CcbotClient() as client:
            # result = await client.search("大熊猫")
            result = await client.crawl("https://m.gmw.cn/toutiao/2023-05/03/content_1303361958.htm", formats=[Formats.html])
            result = await client.extract(result["html"], formats=[Formats.title_, Formats.main_content])
            # screen = await client.screen("https://m.gmw.cn/toutiao/2023-05/03/content_1303361958.htm")
            # with open("screen.png", "wb") as f:
            #     f.write(screen)
            print(result)

    asyncio.run(test())