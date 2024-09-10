from typing import Iterable
from enum import StrEnum
from lxml import etree
from lxml.html.clean import Cleaner

from readability import Document
import html2text
from httpx._utils import parse_content_type_charset

class Formats(StrEnum):
    html = "html"
    title_ = "title"
    metadata = "metadata"
    text = "text"
    links = "links"
    main_content = "main_content"
    markdown = "markdown"


DEFAULT_FORMANT = (Formats.title_, Formats.main_content)

def get_charset(html):
    root = etree.HTML(html)
    content_type = root.xpath('//head/meta[@http-equiv="Content-Type"]/@content')
    if content_type:
        content_type = content_type[0]
        charset = parse_content_type_charset(content_type)
        return charset

class CommonParser:
    cleaner = Cleaner(style=True)

    def __init__(self, html, formats: Iterable[Formats] = DEFAULT_FORMANT) -> None:
        self.html = html
        self.formats = formats
        self._root = None

    @property
    def root(self):
        if self._root is None:
            self._root = etree.HTML(self.html)
        return self._root

    def extract_text(self):
        cleaned_html = self.cleaner.clean_html(self.html)
        root = etree.HTML(cleaned_html)
        text = etree.tostring(root, method="text", encoding="unicode")
        return text

    def extract_title(self):
        el_title = self.root.xpath("//head/title/text()")
        if el_title:
            title = el_title[0]
        else:
            title = ""
        return title

    def extract_links(self):
        links = self.root.xpath("//a[@href]/@href")
        return links

    def extract_metadata(self):
        metadata = {}
        metas = self.root.xpath("//head/meta[@name]")
        for el in metas:
            metadata[el.get("name")] = el.get("content")
        return metadata

    def extract_main_content(self):
        doc = Document(self.html)
        main_html = doc.summary()
        content = self.extract_markdown(main_html)
        return content

    def extract_markdown(self, html=None):
        if html is None:
            html = self.html
        h = html2text.HTML2Text()
        h.ignore_links = True  # 忽略链接
        h.ignore_images = True  # 忽略图像
        h.ignore_tables = True  # 忽略表格
        text = h.handle(html)
        return text

    def parse(self):
        result = {}
        for item in self.formats:
            key = item.value
            extract_fn = getattr(self, f"extract_{key}")
            result[key] = extract_fn()
        return result


if __name__ == "__main__":
    with open("t2.html", encoding="gbk") as f:
        html = f.read()
    keys = [Formats.metadata, Formats.text, Formats.main_content, Formats.markdown]
    keys = [Formats.title_, Formats.metadata, Formats.links]
    keys = DEFAULT_FORMANT
    print(CommonParser(html, keys).parse())
