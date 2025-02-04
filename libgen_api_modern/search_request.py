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
from .models import BookData, BkData, DownloadLinks
from .enums import SearchType


class SearchRequest:
    DOMAINS = ["libgen.is", "libgen.st", "libgen.rs"]
    BASE_MIRROR = "https://libgen.is"

    # Precompile regular expressions
    EDITION_PATTERN = re.compile(r"\[(.*?ed.*?)\]")
    ISBN_PATTERN = re.compile(r"[\d-]{10,}")

    # Precompile XPath expressions for search results
    XPATH_CACHE = {
        "table": etree.XPath("//table[@width='100%' and @cellspacing='1']"),
        "rows": etree.XPath(".//tr[position()>1]"),
        "cells": etree.XPath("./td"),
        "author_links": etree.XPath(".//a"),
        "title_link": etree.XPath(".//a[contains(@href, 'book/index.php')]"),
        "series_elem": etree.XPath(
            ".//font[@face='Times' and @color='green']/i[not(ancestor::a)]"
        ),
        "isbn_elem": etree.XPath(".//font[@face='Times' and @color='green']/i[last()]"),
    }

    # Precompile XPath expressions for mirror page
    MIRROR_XPATH = {
        "get": "//div[@id='download']/h2[1]/a/@href",
        "cloudflare": "//ul/li/a[contains(@href,'cloudflare-ipfs.com')]/@href",
        "ipfs": "//ul/li/a[contains(@href,'gateway.ipfs.io')]/@href",
        "pinata": "//ul/li/a[contains(@href,'pinata.cloud')]/@href",
        "cover": "//div/img/@src"
,
    }

    def __init__(
        self, query: str, search_type: SearchType = SearchType.DEFAULT
    ) -> None:
        if len(query.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
        self.query = query
        self.search_type = search_type
        self.used_domain: Optional[str] = None
        self.client = httpx.AsyncClient(
            timeout=5.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True,
        )

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _fetch_mirror_page(self, md5: str) -> DownloadLinks | None:
        try:
            url = f"https://books.ms/main/{md5}"

            response = await self.client.get(url, timeout=5.0)
            response.raise_for_status()

            tree = html.fromstring(response.text)

            get_link = tree.xpath(self.MIRROR_XPATH["get"])[0] if tree.xpath(self.MIRROR_XPATH["get"]) else None
            cloudflare = tree.xpath(self.MIRROR_XPATH["cloudflare"])[0] if tree.xpath(self.MIRROR_XPATH["cloudflare"]) else None
            ipfs = tree.xpath(self.MIRROR_XPATH["ipfs"])[0] if tree.xpath(self.MIRROR_XPATH["ipfs"]) else None
            pinata = tree.xpath(self.MIRROR_XPATH["pinata"])[0] if tree.xpath(self.MIRROR_XPATH["pinata"]) else None

            cover = tree.xpath(self.MIRROR_XPATH["cover"])[0] if tree.xpath(self.MIRROR_XPATH["cover"]) else None
            if cover:
                # Fix the URL construction by removing the leading slash
                cover = f"https://books.ms{cover}"

            return DownloadLinks(
                get_link=get_link,
                cloudflare_link=cloudflare,
                ipfs_link=ipfs,
                pinata_link=pinata,
                cover_link=cover,
            )

        except Exception as e:
            print(f"Error fetching mirror page: {e}")
            return None

    def _extract_md5_from_url(self, url: str) -> Optional[str]:
        md5_match = re.search(r"md5=([a-fA-F0-9]{32})", url)
        return md5_match.group(1) if md5_match else None

    async def _resolve_mirrors(
        self, mirrors: Dict[str, str]
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        TODO: Add support for library.gift mirror when it's back online
        """
        # For now, we only use libgen.li mirror
        for title, url in mirrors.items():

            if any(mirror in url for mirror in ["libgen.li", "books.ms"]):
                md5 = self._extract_md5_from_url(url)
                if md5:
                    return await self._fetch_mirror_page(md5)
        return None, None

    async def _parse_book_data_with_mirrors(
        self, book_data: BookData, mirrors: Dict[str, str]
    ) -> BookData:
        download_links: DownloadLinks | None = await self._resolve_mirrors(mirrors)

        # Create new BookData with resolved URLs
        return BookData(
            id=book_data.id,
            authors=book_data.authors,
            title=book_data.title,
            publisher=book_data.publisher,
            year=book_data.year,
            pages=book_data.pages,
            language=book_data.language,
            size=book_data.size,
            extension=book_data.extension,
            isbn=book_data.isbn,
            cover_url=download_links.cover_link if download_links else None,
            download_links=download_links,
        )

    @lru_cache(maxsize=128)
    def _build_search_url(self, domain: str) -> str:
        """Cached URL building for repeated searches."""
        parsed_query = "+".join(self.query.split())

        if self.search_type == SearchType.FICTION:
            return f"https://{domain}/fiction/?q={parsed_query}"
        elif self.search_type == SearchType.SCIMAG:
            return f"https://{domain}/scimag/?q={parsed_query}"
        return (
            f"https://{domain}/search.php?req={parsed_query}&lg_topic=libgen"
            f"&open=0&view=simple&res=100&phrase=1&column={self.search_type.value}"
        )

    async def _fetch_with_timeout(self, domain: str) -> Optional[str]:
        try:
            url = self._build_search_url(domain)
            response = await self.client.get(url)
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

    def _extract_title_info(
        self, cell: html.HtmlElement
    ) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
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

    def _extract_mirrors(self, cells: List[html.HtmlElement]) -> Dict[str, str]:
        mirrors = {}
        for cell in cells:
            for link in self.XPATH_CACHE["author_links"](cell):
                title = link.get("title")
                href = link.get("href")
                if title and href:
                    mirrors[title] = href
        return mirrors

    def _parse_book_data(self, row: html.HtmlElement) -> Optional[BookData]:
        try:
            cells = self.XPATH_CACHE["cells"](row)
            if len(cells) < 10:
                return None

            authors = self._extract_authors(cells[1])
            title, series, isbn, edition = self._extract_title_info(cells[2])

            return BkData(
                id=cells[0].text_content().strip(),
                authors=authors,
                title=title,
                series=series,
                publisher=cells[3].text_content().strip(),
                year=cells[4].text_content().strip(),
                pages=cells[5].text_content().strip(),
                language=cells[6].text_content().strip(),
                size=cells[7].text_content().strip(),
                extension=cells[8].text_content().strip(),
                mirrors=self._extract_mirrors(cells[9:11]),
                isbn=isbn,
                edition=edition,
            )
        except (IndexError, AttributeError):
            return None

    async def search(self) -> List[BookData]:

        # Get initial search results
        search_page = await self.get_search_page()
        tree = html.fromstring(search_page)

        table = self.XPATH_CACHE["table"](tree)
        if not table:
            return []

        # Process rows in parallel
        rows = self.XPATH_CACHE["rows"](table[0])
        with ThreadPoolExecutor(max_workers=min(32, len(rows))) as executor:
            initial_results = list(
                filter(None, executor.map(self._parse_book_data, rows))
            )

        # Resolve mirrors for each book
        tasks = []
        for book in initial_results:
            task = self._parse_book_data_with_mirrors(book, book.mirrors)
            tasks.append(task)

        final_results = await asyncio.gather(*tasks)

        return final_results
