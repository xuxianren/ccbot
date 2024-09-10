import logging
from typing import Annotated, List

from fastapi import APIRouter

from pydantic import BaseModel
from ..crawler.single_page import Formats, DEFAULT_FORMANT, CommonParser

logger = logging.getLogger("ccbot")

router = APIRouter()


DEFAULT_FORMANT = (Formats.title, Formats.main_content)

class ExtractIn(BaseModel):
    html: str
    formats: List[Formats] = DEFAULT_FORMANT

class ExtractOut(BaseModel):
    success: bool
    title: str = None
    metadata: str = None 
    text: str = None
    links: List[str] = None
    main_content: str = None
    markdown: str = None


@router.post("/extract")
async def extract(data: ExtractIn) -> ExtractOut:
    result = {"success": True}
    try:
        result.update(CommonParser(data.html, data.formats).parse())
    except Exception:
        result["sucess"] = False
    return result