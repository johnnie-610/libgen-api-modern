# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/old/search_request.py
#
# This file is part of the libgen-api-modern library

import asyncio
import re
import logging
from concurrent.futures import ThreadPoolExecutor
from functools import lru_cache
from typing import Optional, List, Dict

import aiohttp
import requests
from bs4 import BeautifulSoup

from libgen.enums import SearchType
from ..models import BookData, BkData, DownloadLinks


logger = logging.getLogger(__name__)


class SearchRequest:
    DOMAINS = ["libgen.is", "libgen.st", "libgen.rs"]
    BASE_MIRROR = "https://libgen.is"

    # Precompile regular expressions
    EDITION_PATTERN = re.compile(r"\[(.*?ed.*?)\]")
    ISBN_PATTERN = re.compile(r"[\d-]{10,}")

    # CSS selectors for search results
    CSS_SELECTORS = {
        "table": "table[width='100%'][cellspacing='1']",
        "rows": "tr:not(:first-child)",
        "cells": "td",
        "author_links": "a",
        "title_link": "a[href*='book/index.php']",
        "series_elem": "font[face='Times'][color='green'] > i:not(a i)",
        "isbn_elem": "font[face='Times'][color='green'] > i:last-child",
    }

    # CSS selectors for mirror page
    MIRROR_SELECTORS = {
        "get": "div#download > h2:first-child > a",
        "cloudflare": "ul > li > a[href*='cloudflare-ipfs.com']",
        "ipfs": "ul > li > a[href*='gateway.ipfs.io']",
        "pinata": "ul > li > a[href*='pinata.cloud']",
        "cover": "div > img",
    }

    def __init__(
        self, query: str, search_type: SearchType = SearchType.DEFAULT
    ) -> None:
        if len(query.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
        self.query = query
        self.search_type = search_type
        self.used_domain: Optional[str] = None
        self.async_client = None  # Will be initialized in __aenter__
        self.sync_client = None  # Will be initialized in __enter__

    # Synchronous context manager methods
    def __enter__(self):
        self.sync_client = requests.Session()
        self.sync_client.timeout = 5.0
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.sync_client:
            self.sync_client.close()

    # Asynchronous context manager methods
    async def __aenter__(self):
        self.async_client = aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=5.0),
            connector=aiohttp.TCPConnector(limit=10, limit_per_host=5),
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.async_client:
            await self.async_client.close()

    async def _fetch_mirror_page(self, md5: str) -> DownloadLinks | None:
        try:
            url = f"https://books.ms/main/{md5}"

            async with self.async_client.get(url) as response:
                if response.status != 200:
                    return None

                html_content = await response.text()
                soup = BeautifulSoup(html_content, "html.parser")

                get_elem = soup.select_one(self.MIRROR_SELECTORS["get"])
                get_link = get_elem["href"] if get_elem else None

                cloudflare_elem = soup.select_one(self.MIRROR_SELECTORS["cloudflare"])
                cloudflare = cloudflare_elem["href"] if cloudflare_elem else None

                ipfs_elem = soup.select_one(self.MIRROR_SELECTORS["ipfs"])
                ipfs = ipfs_elem["href"] if ipfs_elem else None

                pinata_elem = soup.select_one(self.MIRROR_SELECTORS["pinata"])
                pinata = pinata_elem["href"] if pinata_elem else None

                cover_elem = soup.select_one(self.MIRROR_SELECTORS["cover"])
                cover = cover_elem["src"] if cover_elem else None
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
            logger.warning(
                f"Error fetching mirror page for MD5 {md5} using URL {url}: {e}",
                exc_info=True,
            )  # New

            return None

    def _fetch_mirror_page_sync(self, md5: str) -> DownloadLinks | None:
        try:
            url = f"https://books.ms/main/{md5}"

            response = self.sync_client.get(url, timeout=5.0)
            if response.status_code != 200:
                return None

            html_content = response.text
            soup = BeautifulSoup(html_content, "html.parser")

            get_elem = soup.select_one(self.MIRROR_SELECTORS["get"])
            get_link = get_elem["href"] if get_elem else None

            cloudflare_elem = soup.select_one(self.MIRROR_SELECTORS["cloudflare"])
            cloudflare = cloudflare_elem["href"] if cloudflare_elem else None

            ipfs_elem = soup.select_one(self.MIRROR_SELECTORS["ipfs"])
            ipfs = ipfs_elem["href"] if ipfs_elem else None

            pinata_elem = soup.select_one(self.MIRROR_SELECTORS["pinata"])
            pinata = pinata_elem["href"] if pinata_elem else None

            cover_elem = soup.select_one(self.MIRROR_SELECTORS["cover"])
            cover = cover_elem["src"] if cover_elem else None
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
            # print(f"Error fetching mirror page: {e}") # Old
            logger.warning(
                f"Error fetching mirror page for MD5 {md5} using URL {url}: {e}",
                exc_info=True,
            )  # New
            return None

    def _extract_md5_from_url(self, url: str) -> Optional[str]:
        md5_match = re.search(r"md5=([a-fA-F0-9]{32})", url)
        return md5_match.group(1) if md5_match else None

    async def _resolve_mirrors(self, mirrors: Dict[str, str]) -> DownloadLinks | None:
        """
        TODO: Add support for library.gift mirror when it's back online
        """
        # For now, we only use libgen.li mirror
        for title, url in mirrors.items():

            if any(mirror in url for mirror in ["libgen.li", "books.ms"]):
                md5 = self._extract_md5_from_url(url)
                if md5:
                    return await self._fetch_mirror_page(md5)

        return None

    def _resolve_mirrors_sync(self, mirrors: Dict[str, str]) -> DownloadLinks | None:
        """
        Synchronous version of _resolve_mirrors
        """
        # For now, we only use libgen.li mirror
        for title, url in mirrors.items():

            if any(mirror in url for mirror in ["libgen.li", "books.ms"]):
                md5 = self._extract_md5_from_url(url)
                if md5:
                    return self._fetch_mirror_page_sync(md5)

        return None

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

    def _parse_book_data_with_mirrors_sync(
        self, book_data: BookData, mirrors: Dict[str, str]
    ) -> BookData:
        download_links: DownloadLinks | None = self._resolve_mirrors_sync(mirrors)

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
            async with self.async_client.get(url) as response:
                if response.status != 200:
                    return None
                return await response.text()

        except Exception:
            return None

    def _fetch_with_timeout_sync(self, domain: str) -> Optional[str]:
        try:
            url = self._build_search_url(domain)
            response = self.sync_client.get(url, timeout=5.0)
            if response.status_code != 200:
                return None
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

    def get_search_page_sync(self) -> str:
        for domain in self.DOMAINS:
            response = self._fetch_with_timeout_sync(domain)
            if response:
                self.used_domain = domain
                return response

        raise ConnectionError("All LibGen mirrors are unreachable")

    def _extract_authors(self, cell: BeautifulSoup) -> tuple[str, ...]:
        return tuple(
            author.text.strip()
            for author in cell.select(self.CSS_SELECTORS["author_links"])
            if author.text.strip()
        )

    def _extract_title_info(
        self, cell: BeautifulSoup
    ) -> tuple[str, Optional[str], Optional[str], Optional[str]]:
        series = None
        isbn = None
        edition = None

        series_elem = cell.select(self.CSS_SELECTORS["series_elem"])
        if series_elem:
            series = series_elem[0].text.strip()

        title_link = cell.select_one(self.CSS_SELECTORS["title_link"])
        title = title_link.text.strip() if title_link else ""

        isbn_elem = cell.select_one(self.CSS_SELECTORS["isbn_elem"])
        if isbn_elem:
            isbn_text = isbn_elem.text
            isbn_matches = self.ISBN_PATTERN.findall(isbn_text)
            if isbn_matches:
                isbn = isbn_matches[0]

        edition_match = self.EDITION_PATTERN.search(cell.text)
        if edition_match:
            edition = edition_match.group(1)

        return title, series, isbn, edition

    def _extract_mirrors(self, cells: List[BeautifulSoup]) -> Dict[str, str]:
        mirrors = {}
        for cell in cells:
            for link in cell.select(self.CSS_SELECTORS["author_links"]):
                title = link.get("title")
                href = link.get("href")
                if title and href:
                    mirrors[title] = href
        return mirrors

    def _parse_book_data(self, row: BeautifulSoup) -> Optional[BkData]:
        try:
            cells = row.select(self.CSS_SELECTORS["cells"])
            if len(cells) < 10:
                return None

            authors = self._extract_authors(cells[1])
            title, series, isbn, edition = self._extract_title_info(cells[2])

            return BkData(
                id=cells[0].text.strip(),
                authors=authors,
                title=title,
                series=series,
                publisher=cells[3].text.strip(),
                year=cells[4].text.strip(),
                pages=cells[5].text.strip(),
                language=cells[6].text.strip(),
                size=cells[7].text.strip(),
                extension=cells[8].text.strip(),
                mirrors=self._extract_mirrors(cells[9:11]),
                isbn=isbn,
                edition=edition,
            )
        except (IndexError, AttributeError):
            return None

    async def search(self) -> List[BookData]:
        """
        Asynchronous search method that returns a list of BookData objects.
        """
        # Get initial search results
        search_page = await self.get_search_page()
        soup = BeautifulSoup(search_page, "html.parser")

        table = soup.select_one(self.CSS_SELECTORS["table"])
        if not table:
            return []

        # Process rows in parallel
        rows = table.select(self.CSS_SELECTORS["rows"])
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

    def search_sync(self) -> List[BookData]:
        """
        Synchronous search method that returns a list of BookData objects.
        """
        # Get initial search results
        search_page = self.get_search_page_sync()
        soup = BeautifulSoup(search_page, "html.parser")

        table = soup.select_one(self.CSS_SELECTORS["table"])
        if not table:
            return []

        # Process rows in parallel
        rows = table.select(self.CSS_SELECTORS["rows"])
        with ThreadPoolExecutor(max_workers=min(32, len(rows))) as executor:
            initial_results = list(
                filter(None, executor.map(self._parse_book_data, rows))
            )

        # Resolve mirrors for each book
        final_results = []
        for book in initial_results:
            result = self._parse_book_data_with_mirrors_sync(book, book.mirrors)
            final_results.append(result)

        return final_results
