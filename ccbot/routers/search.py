import logging

from typing import Annotated, List

from fastapi import APIRouter, Body


from ..crawler.search_engine import EngineEnum, engine_factory, SearchResultItem

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/search")
async def search(keyword: Annotated[str, Body()], engine:Annotated[EngineEnum, Body()]=EngineEnum.toutiao)->List[SearchResultItem]:
    logger.info("正在使用%s搜索: %s", engine.value, keyword)
    search_engine = engine_factory(engine)
    if search_engine is not None:
        results = await search_engine.search(keyword)
    else:
        results = []
    return results