import logging

from typing import Annotated, List

from fastapi import APIRouter, Request, Body
from fastapi.responses import StreamingResponse

from pydantic import BaseModel, HttpUrl
from ..crawler.single_page import common_crawl, Mode, Formats, DEFAULT_FORMANT, DEFAULT_MODE, get_screen

logger = logging.getLogger("ccbot")

router = APIRouter()


class CrawlIn(BaseModel):
    url: HttpUrl
    timeout: int = -1
    formats: List[Formats] = DEFAULT_FORMANT
    mode: Mode = DEFAULT_MODE


class CrawlOut(BaseModel):
    success: bool
    url: str
    title: str = None
    metadata: str = None 
    text: str = None
    links: List[str] = None
    main_content: str = None
    markdown: str = None

@router.post("/crawl")
async def crawl(crawl_in: CrawlIn) -> CrawlOut:
    url = str(crawl_in.url)
    try:
        result = await common_crawl(url, crawl_in.timeout, crawl_in.formats, crawl_in.mode)
        result["success"] = True
    except Exception:
        logger.exception("抓取网页失败: %s", crawl_in.url)
        result = {
            "success": False
        }
    result["url"] = url
    return result


@router.post("/screen")
async def screen(url: Annotated[HttpUrl, Body()]="https://bot.sannysoft.com", timeout: Annotated[int, Body()]=-1):
    img = await get_screen(str(url), timeout)
    headers = {
        "Content-Disposition": f"inline; filename=screen.png",
        "Content-Type": "image/png",
    }
    return StreamingResponse(
        iter([img,]),
        headers=headers,
        media_type="image/png"
    )