from enum import StrEnum

from .base import SearchResultItem, SearchEngine
from .bing import Bing
from .tongtiao import Toutiao

class EngineEnum(StrEnum):
    bing = "bing"
    toutiao = "toutiao"

engines = {
    EngineEnum.bing.value: Bing(),
    EngineEnum.toutiao.value: Toutiao(),
}

def engine_factory(t:EngineEnum)->SearchEngine|None:
    return engines.get(t.value)