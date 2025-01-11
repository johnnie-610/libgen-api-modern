# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

import asyncio
import re
<<<<<<< HEAD
import tracemalloc
from asyncio import sslproto
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import Tag

from typing import Optional, List, Dict

tracemalloc.start()
setattr(sslproto._SSLProtocolTransport, "_start_tls_compatible", True)

=======
import httpx
from lxml import html, etree
from typing import Optional, List, Dict, Tuple
from functools import lru_cache
from concurrent.futures import ThreadPoolExecutor
from .models import BookData, BkData
from .enums import SearchType
>>>>>>> origin/main


class SearchRequest:
    DOMAINS = ["libgen.is", "libgen.st", "libgen.rs"]
    BASE_MIRROR = "https://libgen.is"

    # Precompile regular expressions
    EDITION_PATTERN = re.compile(r"\[(.*?ed.*?)\]")
    ISBN_PATTERN = re.compile(r"[\d-]{10,}")

<<<<<<< HEAD
    def __init__(self, query: str, search_type: Optional[str] = "def") -> None:
      
=======
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
        "cover": etree.XPath("//table//a[contains(@href, '/covers/')]/img/@src"),
        "download": etree.XPath(
            "//td[@bgcolor='#A9F5BC']//a[contains(@href, 'get.php')]/@href"
        ),
    }

    def __init__(
        self, query: str, search_type: SearchType = SearchType.DEFAULT
    ) -> None:
        if len(query.strip()) < 3:
            raise ValueError("Query must be at least 3 characters long")
>>>>>>> origin/main
        self.query = query
        self.search_type = search_type
        self.used_domain: Optional[str] = None
        self.client = httpx.AsyncClient(
            timeout=5.0,
            limits=httpx.Limits(max_keepalive_connections=5, max_connections=10),
            http2=True,
        )

<<<<<<< HEAD
        if len(self.query) < 3:
            raise ValueError("Query is too short")
        
    

    async def resolve_mirrors(self, session: ClientSession, mirror: str, proxy: Optional[str] = None) -> Dict[str, str]:
        MIRROR_SOURCES = ["GET", "Cloudflare", "IPFS.io"]

        if mirror is None:
            raise ValueError("No mirror specified")

        response = await (await session.get(mirror, proxy=proxy)).text()
        soup = BeautifulSoup(response, "html.parser")

        links = soup.find_all("a", string=MIRROR_SOURCES)
        download_links = {link.string: link["href"] for link in links}
        
        return download_links
        
        
    async def resolve_download_link(
        self, 
        session: ClientSession, 
        mirror_1: str | None = None,
        mirror_2: str | None = None,
        proxy: Optional[str] = None
    ) -> str | None:
        if mirror_1 is None and mirror_2 is None:
            raise ValueError("No mirrors specified")
        
        download_link = None
        if mirror_1 is not None and mirror_2 is None:
            response = await (await session.get(mirror_1, proxy=proxy)).text()
        
            soup = BeautifulSoup(response, "html.parser")

            try:
                download_link = soup.find("a", string="GET")["href"]
            except AttributeError:
                download_link = None
            except Exception:
                download_link = None

        if  mirror_2 is not None and mirror_1 is None:
            response = await (await session.get(mirror_2, proxy=proxy)).text()
            soup = BeautifulSoup(response, "html.parser")
            
            try:
                save_button = soup.find('button', string='↓ save')
            
                if save_button:
                    onclick_attr = save_button.get('onclick')
                    
                    match = re.search(r"location\.href='(.*?)'", onclick_attr)
                    
                    if match:
                        relative_url = match.group(1)
                        
                        download_link = 'https:' + relative_url

            except AttributeError:
                download_link = None
            except Exception:
                download_link = None
        
        return download_link

    async def strip_i_tag_from_soup(
        self, soup: BeautifulSoup, /) -> None:
      
        # Find all <i> tags
        subheadings: List[Tag] = await asyncio.get_event_loop().run_in_executor(None, soup.find_all, "i")
        
        # Remove each <i> tag
        for subheading in subheadings:
            subheading.decompose()

    async def fetch_page(self, session: ClientSession, url, proxy: Optional[str] = None):
        response = await (await session.get(url, proxy=proxy)).text()
        return response
    
    
    async def get_search_page(self, session: ClientSession, proxy: Optional[str] = None, type: Optional[str] = "default"):
        parsed_query = "+".join(self.query.split(" "))  # type: str
        match type:
            case "default": # searches non-fiction/sci-tech
                search_url = (
                    f"https://libgen.is/search.php?"
                    f"req={parsed_query}&"
                    f"res=100&"
                    f"view=detailed&"
                    f"phrase=1&"
                    f"column={self.search_type}"  # type: str
                )
            case "fiction": # searches fiction
                search_url = f"https://libgen.is/fiction/?q={parsed_query}"
            case "scimag": # searches scientific articles
                search_url = f"https://libgen.is/scimag/?q={parsed_query}"
        

        return await (await session.get(search_url, proxy=proxy)).text()
    

    async def aggregate_request_data(self, proxy: Optional[str] = None) -> List[Dict[str, str]]:

        async with ClientSession() as session:
            search_page = await self.get_search_page(session, proxy=proxy)

            soup = BeautifulSoup(search_page, "html.parser")
            await self.strip_i_tag_from_soup(soup)

            tables = soup.find_all("table", {"border": "0", "rules": "cols", "width": "100%"})

            raw_data = []

            for table in tables:
                rows = table.find_all("tr")[1:] 

                if not rows:
                    continue

                book_data = {}
                img_src = None
                mirror = None

                first_row = rows[0]
                title_td = first_row.find_all("td")[2]
                title = title_td.get_text(strip=True)
                book_data["Title"] = title
                img_tag = first_row.find('img')
                if img_tag:
                    img_src = img_tag.get('src')
                a_tag = first_row.find('a', href=True)
                mirror = "https://libgen.is" + a_tag['href'] if a_tag else None
                



                # Extract other book data
                for row in rows:
                    cells = row.find_all("td")
                    if len(cells) < 2:
                        continue  # Skip rows with insufficient data

                    label = cells[0].get_text(strip=True).replace(":", "")
                    if label in self.col_names:
                        book_data[label] = cells[1].get_text(strip=True)
                        if len(cells) > 3 and cells[2].get_text(strip=True).replace(":", "") in self.col_names:
                            book_data[cells[2].get_text(strip=True).replace(":", "")] = cells[3].get_text(strip=True)

                for col_name in self.col_names:
                    if col_name not in book_data:
                        book_data[col_name] = ""

                if img_src:
                    book_data['Cover'] = f"https://libgen.is{img_src}"
                
                book_data['Mirror'] = mirror
=======
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.aclose()

    async def _fetch_mirror_page(self, md5: str) -> Tuple[Optional[str], Optional[str]]:
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
            return None, None

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
            if "libgen.li" in url:
                md5 = self._extract_md5_from_url(url)
                if md5:
                    return await self._fetch_mirror_page(md5)
        return None, None
>>>>>>> origin/main

    async def _parse_book_data_with_mirrors(
        self, book_data: BookData, mirrors: Dict[str, str]
    ) -> BookData:
        cover_url, download_url = await self._resolve_mirrors(mirrors)

        # Create new BookData with resolved URLs
        return BookData(
            id=book_data.id,
            authors=book_data.authors,
            title=book_data.title,
            series=book_data.series,
            publisher=book_data.publisher,
            year=book_data.year,
            pages=book_data.pages,
            language=book_data.language,
            size=book_data.size,
            extension=book_data.extension,
            isbn=book_data.isbn,
            edition=book_data.edition,
            cover_url=cover_url,
            download_url=download_url,
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

        


<<<<<<< HEAD
            for book in raw_data:
                if "Mirror" in book:
                    mirror = book["Mirror"]
                    if mirror:
                        download_links = await self.resolve_mirrors(session, mirror=mirror, proxy=proxy)
                    else:
                        book["Direct Download Link"] = None
                    for key, value in download_links.items():
                        if key == "GET":
                            book["Direct Download Link 1"] = value
                        elif key == "Cloudflare":
                            book["Direct Download Link 2"] = value
                        elif key == "IPFS.io":
                            book["Direct Download Link 3"] = value
                del book["Mirror"]
            
        

        return raw_data
    
    


    async def aggregate_fiction_data(self, proxy: Optional[str] = None) -> List[Dict[str, str]]:
        fiction_cols = [
            "ID",
            "Title",
            "Series",
            "Language",
            "Publisher",
            "Year",
            "Format",
            "File Size",
        ]

        async with ClientSession() as session:
            search_page_content = await self.get_search_page(session, type="fiction", proxy=proxy)
            soup = BeautifulSoup(search_page_content, "html.parser")
            
            tbody = soup.find("tbody")
            fiction_data = []
            tasks = []

            async def process_row(row):
                title_td = row.find_all('td')[2]
                link_tag = title_td.find('a')
                link = f"https://libgen.is{link_tag['href']}"

                r_soup_content = await self.fetch_page(session, link, proxy=proxy)
                r_soup = BeautifulSoup(r_soup_content, "html.parser")
                
                book = {}
                img_tag = r_soup.find('img', src=lambda x: x and x.startswith('/fictioncovers/'))
                record = r_soup.find('table', class_='record')
                rs = record.find_all('tr')
                for r in rs:
                    cells = r.find_all('td')
                    data = cells[0].get_text(strip=True).replace(":", "")
                    if data in fiction_cols:
                        book[data] = cells[1].get_text(strip=True)

                def get_authors(soup_element):
                    authors = soup_element.find('ul', class_='catalog_authors')
                    if authors:
                        return ', '.join([author.text for author in authors.find_all('a')])
                    else:
                        return ''

                book["Authors"] = get_authors(record)
                book["Cover"] = f"https://libgen.is{img_tag['src']}" if img_tag else None

                download_links = record.find('ul', class_='record_mirrors').find_all('a')
                mirror_link = None
                for link in download_links:
                    if 'library.lol/fiction' in link['href']:
                        mirror_link = link['href']
                        break

                if mirror_link:
                    
                    d_link = await self.resolve_download_link(session, mirror_link, proxy=proxy)
                    book["Direct_Download_Link"] = d_link if d_link else None
                fiction_data.append(book)

            for row in tbody.find_all('tr'):
                tasks.append(process_row(row))

            await asyncio.gather(*tasks)

        return fiction_data
    
    async def aggregate_scimag_data(self, proxy: Optional[str] = None) -> List[Dict[str, str]]:
        scimag_cols = [
            "Title",
            "Authors",
            "DOI",
            "Journal",
            "Publisher",
            "Year",
            "Volume",
            "Issue",
            "Pages",
            "File Size",
            "ID"
        ]

        async with ClientSession() as session:
            search_page = await self.get_search_page(session, type="scimag", proxy=proxy)
            soup = BeautifulSoup(search_page, "html.parser")
            tbody = soup.find("tbody")
            scimag_data = []
            tasks = []

            async def process_row(row):
                title_td = row.find_all('td')[1]
                link_tag = title_td.find('a')
                link = f"https://libgen.is{link_tag['href']}"

                r_soup_content = await self.fetch_page(session, link, proxy=proxy)
                r_soup = BeautifulSoup(r_soup_content, "html.parser")
                
                book = {}
                record = r_soup.find('table', class_='record')
                rs = record.find_all('tr')
                for r in rs:
                    cells = r.find_all('td')
                    data = cells[0].get_text(strip=True).replace(":", "")
                    if data in scimag_cols:
                        book[data] = cells[1].get_text(strip=True)

                download_links = record.find('ul', class_='record_mirrors').find_all('a')
                
                links = []

                for link in download_links:
                    
                    if 'library.lol/scimag' in link['href']:
                        mirror_1 = link['href']
                        d_link = await self.resolve_download_link(session, mirror_1 = mirror_1, proxy=proxy)
                        links.append(d_link)

                    elif 'sci-hub.ru' in link['href']:
                        mirror_2 = link['href']
                        d_link = await self.resolve_download_link(session, mirror_2 = mirror_2, proxy=proxy)
                        links.append(d_link)
                
                book["Direct_Download_Link_1"] = "" if link[0] is None else links[0]
                book["Direct_Download_Link_2"] = "" if link[1] is None else links[1]

                scimag_data.append(book)
            for row in tbody.find_all('tr'):
                tasks.append(process_row(row))

            await asyncio.gather(*tasks)
        
        # TODO: Add Journal links

        return scimag_data
=======
        return final_results
>>>>>>> origin/main
