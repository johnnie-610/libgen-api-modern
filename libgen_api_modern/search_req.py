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
from functools import lru_cache
from .models import BookData, SearchResults  # Updated import


class SearchReq:
    DOMAINS = ["libgen.li", "libgen.gs", "libgen.vg", "libgen.la", "libgen.bz"]
    BASE_MIRROR = "libgen.li"

    EDITION_PATTERN = re.compile(r"\[(.*?ed.*?)\]")
    ISBN_PATTERN = re.compile(r"[\d-]{10,}")

    XPATH_CACHE = {
        "table": etree.XPath(
            "//table[@id='tablelibgen' and @class='table  table-striped']"
        ),
        "rows": etree.XPath("//tbody/tr"),  # Updated to get rows directly from tbody
        "cells": etree.XPath("//td"),
        "author_links": etree.XPath("//a"),
        "title_link": etree.XPath(
            "//a[contains(@href, 'edition.php')]"
        ),  # Updated to match the HTML
        "series_elem": etree.XPath(
            ".//font[@face='Times' and @color='green']/i[not(ancestor::a)]"
        ),
        "isbn_elem": etree.XPath(".//font[@face='Times' and @color='green']/i[last()]"),
        "cover_link": etree.XPath(".//a[contains(@href, 'edition.php')]/img/@src"),
        "mirror_links": etree.XPath(
            "//nobr/a[contains(@href, '/ads') or contains(@href, 'library.lol') or contains(@href, 'annas-archive.org')]"
        ),
    }

    MIRROR_XPATH = {
        "download": etree.XPath(
            "//td[@bgcolor='#A9F5BC']//a[contains(@href, 'get.php')]/@href"
        ),
    }
    TOTAL_RESULTS_XPATH = etree.XPath(
        "//li/a[contains(@href,'filesuns=all')]/span[@class='badge badge-primary']/text()"
    )

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
        self.next_page_url: str | None = None
        self.max_pages = 10

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _fetch_mirror_page(self, md5: str) -> tuple[str | None, str | None ]:
        try:
            url = f"https://{self.BASE_MIRROR}/{md5}"
            response = await self.client.get(url, timeout=5.0)
            response.raise_for_status()
            tree = html.fromstring(response.text)

            download_path = self.MIRROR_XPATH["download"](tree)
            download_url = (
                f"https://{self.BASE_MIRROR}/{download_path[0]}" if download_path else None
            )

            return None, download_url

        except Exception as e:
            print(f"Error fetching mirror page: {e}")
            return None, None

    def _extract_md5_from_url(self, url: str) -> str | None:
        md5_match = re.search(r"md5=([a-fA-F0-9]{32})", url)
        return md5_match.group(1) if md5_match else None

    async def _resolve_mirror(self, mirror: str) -> str | None:
        md5 = self._extract_md5_from_url(mirror)
        if md5:
            _, download_url = await self._fetch_mirror_page(md5)
            return download_url
        return None

    @lru_cache(maxsize=128)
    def _build_search_url(self, domain: str, page: int = 1) -> str:
        parsed_query = "+".join(self.query.split())
        base_url = f"https://{domain}/index.php?req={parsed_query}&columns%5B%5D=t&columns%5B%5D=a&columns%5B%5D=s&columns%5B%5D=y&columns%5B%5D=p&columns%5B%5D=i&objects%5B%5D=f&objects%5B%5D=e&objects%5B%5D=s&objects%5B%5D=a&objects%5B%5D=p&objects%5B%5D=w&topics%5B%5D=l&topics%5B%5D=c&topics%5B%5D=f&topics%5B%5D=a&topics%5B%5D=m&topics%5B%5D=r&topics%5B%5D=s&res=100&covers=on&filesuns=all"

        if page > 1:
            return f"{base_url}&page={page}"
        return base_url

    async def _fetch_with_timeout(self, domain: str, page: int = 0) -> str | None:
        try:
            url = self._build_search_url(domain, page)
            response = await asyncio.wait_for(self.client.get(url), timeout=5.0)
            response.raise_for_status()
            return response.text
        except Exception:
            return None

    async def get_search_page(self, page: int = 0) -> str:
        tasks = [self._fetch_with_timeout(domain, page) for domain in self.DOMAINS]
        responses = await asyncio.gather(*tasks)

        for domain, response in zip(self.DOMAINS, responses):
            if response:
                self.used_domain = domain
                return response

        raise ConnectionError("All LibGen mirrors are unreachable")

    def _extract_authors(self, cell: html.HtmlElement) -> tuple[str, ...]:
        try:
            return tuple(
                author.text_content().strip()
                for author in self.XPATH_CACHE["author_links"](cell)
                if author.text_content().strip()
            )
        except (AttributeError, IndexError):
            return tuple()

    def _extract_title_info(
        self, cell: html.HtmlElement
    ) -> tuple[str | None, str | None, str | None]:
        try:
            title_link = self.XPATH_CACHE["title_link"](cell)[0]
            title = title_link.text_content().strip()
        except (AttributeError, IndexError):
            title = None

        try:
            isbn_match = self.XPATH_CACHE["isbn_elem"](cell)
            isbn_text = isbn_match[0].text_content() if isbn_match else None
            isbn = (
                self.ISBN_PATTERN.findall(isbn_text)[0]
                if isbn_text and self.ISBN_PATTERN.findall(isbn_text)
                else None
            )
        except (AttributeError, IndexError):
            isbn = None

        return title, isbn

    async def _parse_book_data(self, row: html.HtmlElement) -> BookData | None:
        try:
            cells = self.XPATH_CACHE["cells"](row)
            if len(cells) < 9:
                return None

            authors = self._extract_authors(cells[2])
            title, isbn = self._extract_title_info(cells[3])

            cover_paths = self.XPATH_CACHE["cover_link"](cells[0])
            cover_url = f"{self.BASE_MIRROR}{cover_paths[0]}" if cover_paths else None

            mirror_links = self.XPATH_CACHE["mirror_links"](cells[-1])

            download_url = None
            if mirror_links:
                download_url = await self._resolve_mirror(mirror_links[0].get("href"))

            if title is None:
                return None

            return BookData(
                authors=authors,
                title=title,
                publisher=cells[4].text_content().strip() if len(cells) > 3 else None,
                year=cells[5].text_content().strip() if len(cells) > 4 else None,
                pages=cells[7].text_content().strip() if len(cells) > 6 else None,
                language=cells[6].text_content().strip() if len(cells) > 5 else None,
                size=cells[8].text_content().strip() if len(cells) > 7 else None,
                extension=cells[9].text_content().strip() if len(cells) > 8 else None,
                isbn=isbn,
                cover_url=cover_url,
                download_url=download_url,
            )
        except (IndexError, AttributeError) as e:
            print(f"Error parsing book data: {e}")
            return None

    async def search(self, page: int = 1) -> SearchResults:
        search_page = await self.get_search_page(page)
        tree = html.fromstring(search_page)

        table = self.XPATH_CACHE["table"](tree)
        if not table:
            return SearchResults(
                total_results=0, books=[], next_page_url=None, current_page=page
            )

        rows = self.XPATH_CACHE["rows"](table[0])
        tasks = [self._parse_book_data(row) for row in rows]
        books = [book for book in await asyncio.gather(*tasks) if book]

        total_results_element = self.TOTAL_RESULTS_XPATH(tree)
        total_results_int = (
            int(total_results_element[0].replace(",", ""))
            if total_results_element
            else 0
        )

        next_page_number = page + 1
        if next_page_number <= self.max_pages and (total_results_int > (page * 100)):
            next_page_url = self._build_search_url(self.used_domain, next_page_number)
            self.next_page_url = next_page_url
        else:
            next_page_url = None
            self.next_page_url = next_page_url

        return SearchResults(
            total_results=total_results_int,
            books=books,
            next_page_url=next_page_url,
            current_page=page,
        )

    async def next_page(self) -> SearchResults:
        if self.next_page_url is None:
            raise ValueError("No next page url found")

        match = re.search(r"page=(\d+)", self.next_page_url)
        if not match:
            raise ValueError("No page number found in next page url")

        next_page_number = int(match.group(1))
        return await self.search(next_page_number)
