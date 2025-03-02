import asyncio
import aiohttp
import logging
import re

from .parser import LibgenHTMLParser

# List of Libgen alternative domains
LIBGEN_URLS = [
    "https://libgen.li",
    "https://libgen.gs",
    "https://libgen.vg",
    "https://libgen.la",
    "https://libgen.bz",
]


class LibgenError(Exception):
    """Custom exception for Libgen errors."""

    pass


async def fetch_page(
    session: aiohttp.ClientSession, url: str, params: dict = None, proxy: str = None
) -> str:
    async with session.get(url, params=params, proxy=proxy, timeout=10) as resp:
        if resp.status != 200:
            raise LibgenError(f"HTTP error {resp.status} for URL: {url}")
        return await resp.text()


async def resolve_mirror_link(
    mirror_partial: str, base_url: str, session: aiohttp.ClientSession
) -> str:
    """
    Given a mirror link extracted from the table (which may be incomplete),
    check if it already contains 'get.php?md5='. If not, fetch that page and extract the
    actual GET link.
    """
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


def parse_results(html: str) -> list:
    parser = LibgenHTMLParser()
    parser.feed(html)
    return parser.get_results()


async def search(query: str, proxies: list = None) -> list:
    """
    Search Libgen for a given query. After parsing the raw HTML into results,
    we post-process each result to update cover and mirror links.

    :param query: The search query string.
    :param proxies: Optional list of proxy URLs.
    :return: A list of result dictionaries with complete links.
    """
    params = {
        "req": query,
        "res": "100",  # results per page
        "covers": "on",
        "filesuns": "all",
    }
    results = None
    async with aiohttp.ClientSession() as session:
        for base_url in LIBGEN_URLS:
            search_url = f"{base_url}/index.php"
            logging.info(f"Trying {search_url}")
            try:
                if proxies:
                    for proxy in proxies:
                        try:
                            html = await fetch_page(
                                session, search_url, params=params, proxy=proxy
                            )
                            results = parse_results(html)
                            if results:
                                break
                        except Exception as e:
                            logging.warning(
                                f"Error with proxy {proxy} on {search_url}: {e}"
                            )
                            continue
                else:
                    html = await fetch_page(session, search_url, params=params)
                    results = parse_results(html)
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
                            result["mirror"] = await resolve_mirror_link(
                                mirror_link, base_url, session
                            )
                return results
    if results is None:
        raise LibgenError("Failed to retrieve results from Libgen sites.")
    return results
