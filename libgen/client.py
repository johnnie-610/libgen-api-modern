# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/new/client.py
#
# This file is part of the libgen-api-modern library
import asyncio

import aiohttp
import requests
import logging
import re

from typing import Any
from parser import LibgenHTMLParser
from models import BookData, DownloadLinks

from errors import (
    LibgenNetworkError,
    LibgenSearchError,
    LibgenParseError,
)

from libgen_types import (
    URL,
    ProxyList,
    RawBookResult,
)

# List of Libgen alternative domains
LIBGEN_URLS = [
    "https://libgen.gl",
    "https://libgen.gs",
    "https://libgen.vg",
    "https://libgen.la",
    "https://libgen.bz",
]


class LibgenClient:
    """
    A client for interacting with Library Genesis.
    Supports both synchronous and asynchronous operations.
    """

    def __init__(self, timeout: int = 10, max_connections: int = 10):

        self.timeout = timeout
        self.max_connections = max_connections
        self._async_session = None
        self._sync_session = None

    async def __aenter__(self):
        if self._async_session is None:
            self._async_session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=self.timeout),
                connector=aiohttp.TCPConnector(limit=self.max_connections),
            )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self._async_session:
            await self._async_session.close()
            self._async_session = None

    def __enter__(self):
        if self._sync_session is None:
            self._sync_session = requests.Session()
            self._sync_session.timeout = self.timeout
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self._sync_session:
            self._sync_session.close()
            self._sync_session = None

    async def fetch_page_async(
        self, url: URL, params: dict[str, Any] = None, proxy: str = None
    ) -> str:

        if self._async_session is None:
            raise RuntimeError(
                "Client not initialized. Use async with LibgenClient() as client: ..."
            )

        async with self._async_session.get(
            url, params=params, proxy=proxy, timeout=self.timeout
        ) as resp:
            if resp.status != 200:
                raise LibgenNetworkError("HTTP error", status_code=resp.status, url=url)
            return await resp.text()

    def fetch_page_sync(
        self, url: URL, params: dict[str, Any] = None, proxy: str = None
    ) -> str:

        if self._sync_session is None:
            raise RuntimeError(
                "Client not initialized. Use with LibgenClient() as client: ..."
            )

        proxies = {"http": proxy, "https": proxy} if proxy else None
        response = self._sync_session.get(
            url, params=params, proxies=proxies, timeout=self.timeout
        )

        if response.status_code != 200:
            raise LibgenNetworkError(
                f"HTTP error", status_code=response.status_code, url=url
            )
        return response.text

    async def resolve_mirror_link_async(
        self, mirror_partial: str, base_url: URL
    ) -> URL:

        # Ensure the mirror_partial starts with a slash
        if not mirror_partial.startswith("/"):
            mirror_partial = "/" + mirror_partial
        url = base_url + mirror_partial

        try:
            html = await self.fetch_page_async(url)
            # Look for a GET link in the fetched HTML.
            # The expected pattern is something like: href="get.php?md5=...."
            match = re.search(r'href="(get\.php\?md5=[^"]+)"', html)
            if match:
                get_link = match.group(1)
                if not get_link.startswith("/"):
                    get_link = "/" + get_link
                return base_url + get_link
            else:
                # If no GET link is found, return the original URL.
                return url
        except Exception as e:
            logging.warning(f"Error resolving mirror link {url}: {e}")
            return url

    def resolve_mirror_link_sync(self, mirror_partial: str, base_url: URL) -> URL:

        # Ensure the mirror_partial starts with a slash
        if not mirror_partial.startswith("/"):
            mirror_partial = "/" + mirror_partial
        url = base_url + mirror_partial

        try:
            html = self.fetch_page_sync(url)
            # Look for a GET link in the fetched HTML.
            # The expected pattern is something like: href="get.php?md5=...."
            match = re.search(r'href="(get\.php\?md5=[^"]+)"', html)
            if match:
                get_link = match.group(1)
                if not get_link.startswith("/"):
                    get_link = "/" + get_link
                return base_url + get_link
            else:
                # If no GET link is found, return the original URL.
                return url
        except Exception as e:
            logging.warning(f"Error resolving mirror link {url}: {e}")
            return url

    def _parse_results(self, html: str) -> list[RawBookResult]:

        parser = LibgenHTMLParser()
        parser.feed(html)
        return parser.get_results()

    def _convert_to_book_data(
        self, result: RawBookResult, download_link: URL | None = None
    ) -> BookData:

        # Extract authors as a tuple
        authors_str = result.get("authors", "")
        authors = tuple(
            author.strip() for author in authors_str.split(",") if author.strip()
        )

        # Create DownloadLinks object if download_link is provided
        download_links = None
        if download_link:
            download_links = DownloadLinks(
                get_link=download_link,
                cloudflare_link=None,
                ipfs_link=None,
                pinata_link=None,
                cover_link=result.get("cover"),
            )

        return BookData(
            id=result.get("id", ""),
            authors=authors,
            title=result.get("title", ""),
            publisher=result.get("publisher"),
            year=result.get("year"),
            pages=result.get("pages"),
            language=result.get("language"),
            size=result.get("size"),
            extension=result.get("extension"),
            isbn=None,  # Not available in the raw results
            cover_url=result.get("cover"),
            download_links=download_links,
        )

    async def search_async(
        self, query: str, proxies: ProxyList = None
    ) -> list[BookData]:
        params = {
            "req": query,
            "res": "100",  # results per page
            "covers": "on",
            "filesuns": "all",
        }


        for base_url in LIBGEN_URLS:
            search_url = f"{base_url}/index.php"
            logging.info(f"Trying {search_url}")
            raw_results_list = None
            try:
                if proxies:
                    for proxy in proxies:
                        # ... try proxy ...
                        html = await self.fetch_page_async(
                            search_url, params=params, proxy=proxy
                        )
                        raw_results_list = self._parse_results(html)
                        if raw_results_list:
                            break
                else:
                    html = await self.fetch_page_async(search_url, params=params)
                    raw_results_list = self._parse_results(html)

            except Exception as e:
                logging.warning(f"Error accessing {search_url}: {e}")
                continue

            if raw_results_list:

                async def _process_single_result(
                    result_item: RawBookResult, base_url_for_item: str
                ) -> BookData:
                    if result_item.get("cover") and not result_item["cover"].startswith(
                        "http"
                    ):
                        result_item["cover"] = base_url_for_item + result_item["cover"]
                    mirror_link_val = result_item.get("mirror", "")
                    resolved_mirror_url = None
                    if mirror_link_val:
                        if "get.php?md5=" in mirror_link_val:
                            resolved_mirror_url = (
                                base_url_for_item + mirror_link_val
                                if not mirror_link_val.startswith("http")
                                else mirror_link_val
                            )
                        else:
                            resolved_mirror_url = await self.resolve_mirror_link_async(
                                mirror_link_val, base_url_for_item
                            )
                    return self._convert_to_book_data(result_item, resolved_mirror_url)

                processing_tasks = [
                    _process_single_result(r, base_url) for r in raw_results_list
                ]
                final_book_data_list = await asyncio.gather(*processing_tasks)
                return final_book_data_list

        raise LibgenSearchError(
            "Failed to retrieve results from all tried Libgen sites.", query=query
        )

    def search_sync(self, query: str, proxies: ProxyList = None) -> list[BookData]:

        params = {
            "req": query,
            "res": "100",  # results per page
            "covers": "on",
            "filesuns": "all",
        }

        results = None
        book_results = []

        for base_url in LIBGEN_URLS:
            search_url = f"{base_url}/index.php"
            logging.info(f"Trying {search_url}")

            try:
                if proxies:
                    for proxy in proxies:
                        try:
                            html = self.fetch_page_sync(
                                search_url, params=params, proxy=proxy
                            )
                            results = self._parse_results(html)
                            if results:
                                break
                        except Exception as e:
                            logging.warning(
                                f"Error with proxy {proxy} on {search_url}: {e}"
                            )
                            continue
                else:
                    html = self.fetch_page_sync(search_url, params=params)
                    results = self._parse_results(html)
            except Exception as e:
                logging.warning(f"Error accessing {search_url}: {e}")
                continue

            if results:
                # Post-process each result: fix cover and mirror links.
                for result in results:
                    # For cover: if it is relative, prefix with the base URL.
                    if result.get("cover") and not result["cover"].startswith("http"):
                        result["cover"] = base_url + result["cover"]

                    # For mirror:
                    mirror_link = result.get("mirror", "")
                    if mirror_link:
                        if "get.php?md5=" in mirror_link:
                            if not mirror_link.startswith("http"):
                                result["mirror"] = base_url + mirror_link
                        else:
                            # Resolve the mirror link by fetching the page and extracting the GET link.
                            result["mirror"] = self.resolve_mirror_link_sync(
                                mirror_link, base_url
                            )

                    # Convert to BookData
                    book_data = self._convert_to_book_data(result, result.get("mirror"))
                    book_results.append(book_data)

                return book_results

        if not book_results:
            raise LibgenSearchError(
                "Failed to retrieve results from Libgen sites.", query=query
            )

        return book_results


# Standalone functions for backward compatibility
async def fetch_page(
    session: aiohttp.ClientSession,
    url: URL,
    params: dict[str, Any] = None,
    proxy: str = None,
) -> str:

    async with session.get(url, params=params, proxy=proxy, timeout=10) as resp:
        if resp.status != 200:
            raise LibgenNetworkError(f"HTTP error", status_code=resp.status, url=url)
        return await resp.text()


async def resolve_mirror_link(
    mirror_partial: str, base_url: URL, session: aiohttp.ClientSession
) -> URL:

    # Ensure the mirror_partial starts with a slash
    if not mirror_partial.startswith("/"):
        mirror_partial = "/" + mirror_partial
    url = base_url + mirror_partial
    try:
        html = await fetch_page(session, url)
        # Look for a GET link in the fetched HTML.
        # The expected pattern is something like: href="get.php?md5=...."
        match = re.search(r'href="(get\.php\?md5=[^"]+)"', html)
        if match:
            get_link = match.group(1)
            if not get_link.startswith("/"):
                get_link = "/" + get_link
            return base_url + get_link
        else:
            # If no GET link is found, return the original URL.
            return url
    except Exception as e:
        logging.warning(f"Error resolving mirror link {url}: {e}")
        return url


def parse_results(html: str) -> list[RawBookResult]:

    try:
        parser = LibgenHTMLParser()
        parser.feed(html)
        return parser.get_results()
    except Exception as e:
        raise LibgenParseError(f"Failed to parse HTML: {e}")


async def search_async(query: str, proxies: ProxyList = None) -> list[BookData]:
    """
    Search Libgen for a given query. After parsing the raw HTML into results,
    we post-process each result to update cover and mirror links.

    Args:
        query: The search query string.
        proxies: Optional list of proxy URLs.

    Returns:
        A list of result dictionaries with complete links.

    Raises:
        LibgenSearchError: If the search fails
        LibgenNetworkError: If there's a network error
    """
    async with LibgenClient() as client:
        return await client.search_async(query, proxies)


def search_sync(query: str, proxies: ProxyList = None) -> list[BookData]:
    """
    Synchronously search Libgen for a given query.

    Args:
        query: The search query string.
        proxies: Optional list of proxy URLs.

    Returns:
        A list of result dictionaries with complete links.

    Raises:
        LibgenSearchError: If the search fails,
        LibgenNetworkError: If there's a network error,
        LibgenParseError: If parsing fails
    """
    with LibgenClient() as client:
        return client.search_sync(query, proxies)