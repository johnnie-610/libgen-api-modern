# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

import asyncio
import re
import httpx
from lxml import html, etree
from typing import Optional, List, Dict, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from .models import BookData

class SearchReq:
    DOMAINS = ["libgen.li", "libgen.gs", "libgen.vg", "libgen.la", "libgen.bz"]
    BASE_MIRROR = "https://libgen.li"

    EDITION_PATTERN = re.compile(r"\[(.*?ed.*?)\]")
    ISBN_PATTERN = re.compile(r"[\d-]{10,}")
    XPATH_CACHE = {
        "table": etree.XPath("//table[@id='tablelibgen and @class='table table-striped']"),
        "rows": etree.XPath(".//tbody/tr[position()>1]"),
        "cells": etree.XPath("./td"),
        "author_links": etree.XPath(".//a"),
        "title_link": etree.XPath(".//a[contains(@href, 'book/index.php')]"),
        "series_elem": etree.XPath(
            ".//font[@face='Times' and @color='green']/i[not(ancestor::a)]"
        ),
        "isbn_elem": etree.XPath(".//font[@face='Times' and @color='green']/i[last()]"),
    }

    MIRROR_XPATH = {
        "cover": etree.XPath("//table//a[contains(@href, '/covers/')]/img/@src"),
        "download": etree.XPath(
            "//td[@bgcolor='#A9F5BC']//a[contains(@href, 'get.php')]/@href"
        ),
    }

    def __init__(self, query: str) -> None:
        if len(query.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
        self.query = query
        self.used_domain: str | None = None
        self.client = httpx.AsyncClient(
            timeout=5.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _fetch_mirror_page(self, md5: str) -> Optional[str]:
        try:
            url = f"{self.BASE_MIRROR}/ads.php?md5={md5}"
            response = await self.client.get(url, timeout=5.0)
            response.raise_for_status()

            tree = html.fromstring(response.text)

            # Extract cover URL
            cover_path = self.MIRROR_XPATH["cover"](tree)
            cover_url = f"{self.BASE_MIRROR}{cover_path[0]}" if cover_path else None

            # Extract download URL
            download_path = self.MIRROR_XPATH["download"](tree)
            download_url = (
                f"{self.BASE_MIRROR}/{download_path[0]}" if download_path else None
            )

            return cover_url, download_url

        except Exception as e:
            print(f"Error fetching mirror page: {e}")
            return None

    def _extract_md5_from_url(self, url: str) -> str | None:
        md5_match = re.search(r"md5=([a-fA-F0-9]{32})", url)
        return md5_match.group(1) if md5_match else None

    async def _resolve_mirror(self, mirror: str) -> str | None:
        md5: str = self._extract_md5_from_url(mirror)
        if md5:
            return await self._fetch_mirror_page(md5)
        return None

    @lru_cache(maxsize=128)
    async def _build_search_url(self, domain: str) -> str:
        parsed_query = "+".join(self.query.split())
        return f"https://{domain}/index.php?req={parsed_query}&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=l&topics%5B%5D=c&topics%5B%5D=f&topics%5B%5D=a&topics%5B%5D=m&topics%5B%5D=r&topics%5B%5D=s&res=100&covers=on&filesuns=all"

    async def _fetch_with_timeout(self, domain: str) -> str | None:
        try:
            url = await self._build_search_url(domain)
            response = await self.client.get(url, timeout=5.0)
            response.raise_for_status()
            return response.text
        except Exception:
            return None

    async def get_search_page(self) -> str:
        tasks = [self._fetch_with_timeout(domain) for domain in self.DOMAINS]
        responses = await asyncio.gather(*tasks)

        for domain, response in zip(self.DOMAINS, responses):
            if response:
                self.used_domain = domain
                return response

        raise ConnectionError("All LibGen mirrors are unreachable")

    def _extract_authors(self, cell: html.HtmlElement) -> tuple[str, ...]:
        return tuple(
            author.text_content().strip()
            for author in self.XPATH_CACHE["author_links"](cell)
            if author.text_content().strip()
        )

    def _extract_title_info(self, cell: html.HtmlElement) -> tuple[str, ...]:
        series = None
        isbn = None
        edition = None

        series_elem = self.XPATH_CACHE["series_elem"](cell)
        if series_elem:
            series = series_elem[0].text_content().strip()

        title_link = self.XPATH_CACHE["title_link"](cell)[0]
        title = title_link.text_content().strip()

        isbn_match = self.XPATH_CACHE["isbn_elem"](cell)
        if isbn_match:
            isbn_text = isbn_match[0].text_content()
            isbn_matches = self.ISBN_PATTERN.findall(isbn_text)
            if isbn_matches:
                isbn = isbn_matches[0]

        edition_match = self.EDITION_PATTERN.search(cell.text_content())
        if edition_match:
            edition = edition_match.group(1)

        return title, series, isbn, edition

    def _parse_book_data(self, row: html.HtmlElement) -> Optional[BookData]:
        try:
            cells = self.XPATH_CACHE["cells"](row)
            if len(cells) < 10:
                return None

            authors = self._extract_authors(cells[1])
            title, series, isbn, edition = self._extract_title_info(cells[2])

            mirror = cells[]