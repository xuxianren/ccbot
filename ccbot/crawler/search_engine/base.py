from typing import List
from abc import ABC, abstractmethod

from pydantic import BaseModel


class SearchResultItem(BaseModel):
    title: str
    url: str
    summary: str
    pubdate: str | None = None
    platform: str | None = None


class SearchEngine(ABC):

    @abstractmethod
    async def search(self, keyword:str) -> List[SearchResultItem]:
        pass
