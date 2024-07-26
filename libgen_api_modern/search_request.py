# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library
import time
import aiohttp
import requests
import asyncio
import urllib.parse

from bs4 import BeautifulSoup
from bs4.element import Tag

from json import dumps

from typing import Optional, List, Dict, Union



class SearchRequest:

    col_names = [
        "ID",
        "Author(s)",
        "Title",
        "Series",
        "Publisher",
        "Edition",
        "Year",
        "Pages",
        "Language",
        "Size",
        "ISBN",
        "Periodical",
        "City",
        "Extension",
    ]

    def __init__(self, query: str, search_type: Optional[str] = "def") -> None:
        """
        Initialize a search request object.

        Args:
            query (str): The search query.
            search_type (Optional[str], optional): The type of search to perform.
                Defaults to "def" for default search.

        Raises:
            ValueError: If the query is shorter than 3 characters.

        Returns:
            None
        """
        # Set the query and search type
        self.query = query
        self.search_type = search_type

        # Check if the query is too short
        if len(self.query) < 3:
            raise ValueError("Query is too short")
        
    def __str__(self) -> str:
        return dumps(self, indent=4, default=self.default, ensure_ascii=False)

    def __repr__(self) -> str:
        return f"SearchRequest({', '.join(f'{attr}={repr(getattr(self, attr))}' for attr in self.__dict__ if not attr.startswith('_') and getattr(self, attr) is not None)})"

    @staticmethod
    def default(obj):
        
        if isinstance(obj, SearchRequest):
            return {
                "_": obj.__class__.__name__,
                **{attr: getattr(obj, attr) for attr in obj.__dict__ if not attr.startswith('_') and attr not in ["raw"] and getattr(obj, attr) is not None}
            }
        
        return str(obj)
        
    async def resolve_download_link(self, mirror_link: str) -> Dict[str, str]:
        SOURCES = {"GET", "Cloudflare", "IPFS.io"}
        async with aiohttp.ClientSession() as session:
            async with session.get(mirror_link) as response:
                soup = BeautifulSoup((await response.text()), "html.parser")
                links = {a.string: a["href"] for a in soup.find_all("a", string=SOURCES)}
                return links

    async def strip_i_tag_from_soup(
        self, soup: BeautifulSoup, /) -> None:
        """
        Remove <i> tags from a BeautifulSoup object.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to modify.

        Returns:
            None
        """
        # Find all <i> tags
        subheadings: List[Tag] = await asyncio.get_event_loop().run_in_executor(None, soup.find_all, "i")
        
        # Remove each <i> tag
        for subheading in subheadings:
            subheading.decompose()

    async def get_search_page(self, type: Optional[str] = "default") -> aiohttp.ClientResponse:
        """
        Get the search page from libgen.rs.

        Args:
            self (SearchRequest): The search request object.
            type (Optional[str], optional): The type of search to perform.
                Defaults to "default" for default search(non-fiction/sci-tech).

        Returns:
            aiohttp.ClientResponse: The search page as a response object.
        """
        # Join the query words with a '+' to form the parsed query
        parsed_query = "+".join(self.query.split(" "))  # type: str
        # Form the search URL with the parsed query and search type
        match type:
            case "default": # searches non-fiction/sci-tech
                search_url = (
                    f"https://libgen.rs/search.php?"
                    f"req={parsed_query}&"
                    f"res=100&"
                    f"view=detailed&"
                    f"phrase=1&"
                    f"column={self.search_type}"  # type: str
                )
            case "fiction": # searches fiction
                search_url = f"https://libgen.rs/fiction/?q={parsed_query}"
            case "scimag": # searches scientific articles
                search_url = f"https://libgen.rs/scimag/?q={parsed_query}"
        

        # Send a GET request to the search URL and return the response
        async with aiohttp.ClientSession() as session:
            search_page = await session.get(search_url)  # type: aiohttp.ClientResponse
            return search_page
    

    async def aggregate_request_data(self) -> List[Dict[str, str]]:
        """
        Aggregate the request data from the search page.

        Args:
            self (SearchRequest): The search request object.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the aggregated request data.
        """
        # Get the search page
        search_page = await self.get_search_page()

        # Parse the search page using BeautifulSoup
        soup = BeautifulSoup(await search_page.text(), "html.parser")
        self.strip_i_tag_from_soup(soup)

        tables = soup.find_all("table", {"border": "0", "rules": "cols", "width": "100%"})

        raw_data = []

        for table in tables:
            rows = table.find_all("tr")[1:]  # Skip the first row with brown background

            if not rows:
                continue

            book_data = {}
            img_src = None
            md5 = None

            # Extract cover image and md5 hash
            first_row = rows[0]
            title_td = first_row.find_all("td")[2]
            title = title_td.get_text(strip=True)
            book_data["Title"] = title
            img_tag = first_row.find('img')
            if img_tag:
                img_src = img_tag.get('src')
            a_tag = first_row.find('a', href=True)
            if a_tag and 'md5' in a_tag['href']:
                md5 = a_tag['href'].split('md5=')[-1]



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

            # Ensure book_data has all keys from self.col_names
            for col_name in self.col_names:
                if col_name not in book_data:
                    book_data[col_name] = ""

            # Add the cover image source and md5 hash to the book data
            if img_src:
                book_data['Cover'] = f"https://libgen.rs{img_src}"
            if md5:
                book_data['MD5'] = md5.lower()

            raw_data.append(book_data)

        # Add a direct download link to each result
        for book in raw_data:
            if "ID" in book and "MD5" in book and "Title" in book and "Extension" in book:
                id = book["ID"]
                download_id = str(id)[:-3] + "000"
                md5 = book["MD5"]
                title = urllib.parse.quote(book["Title"])
                extension = book["Extension"]
                book['Direct_Download_Link'] = f"https://download.library.lol/main/{download_id}/{md5}/{title}.{extension}"
            
        # TODO: Handle scenarios where direct download link is not available or changes

        return raw_data
    
    async def aggregate_fiction_data(self) -> List[Dict[str, str]]:
        """
        Aggregate the fiction request data from the search page.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the aggregated fiction request data.
        """
        
        search_page = await self.get_search_page(type="fiction")
        soup = BeautifulSoup(await search_page.text(), "html.parser")
        
        tbody = soup.find("tbody")
        if not tbody:
            return []

        book_links = [
            f"https://libgen.rs/{a['href']}"
            for tr in tbody.find_all('tr')
            for a in tr.find_all('a', href=True)
        ]

        async with aiohttp.ClientSession() as session:
            tasks = [self.process_book(link, session) for link in book_links]
            with concurrent.futures.ThreadPoolExecutor() as executor:
                loop = asyncio.get_event_loop()
                fiction_data = await loop.run_in_executor(executor, lambda: list(asyncio.gather(*tasks)))

        return fiction_data

    async def process_book(self, link: str) -> Dict[str, str]:
        fiction_cols = {
            "ID", "Title", "Series", "Language", "Publisher", "Year", "Format", "File Size"
        }
        async with aiohttp.ClientSession() as session:
            async with session as client:
                async with client.get(link) as response:
                    r_soup = BeautifulSoup(await response.text(), "html.parser")
        
        book = {}
        img_tag = r_soup.find('img', src=lambda x: x and x.startswith('/fictioncovers/'))
        record = r_soup.find('table', class_='record')
        
        if record:
            cells = record.find_all('tr')
            for cell in cells:
                data = cell.find('td', class_='field').get_text(strip=True).replace(":", "")
                if data in fiction_cols:
                    book[data] = cell.find('td', class_='record_title').get_text(strip=True)

            authors_ul = record.find('ul', class_='catalog_authors')
            if authors_ul:
                book["Authors"] = ', '.join(a.text for a in authors_ul.find_all('a'))

            book["Cover"] = f"https://libgen.rs{img_tag['src']}" if img_tag else None

            download_links = record.find('ul', class_='record_mirrors')
            if download_links:
                for link in download_links.find_all('a'):
                    if 'library.lol/fiction' in link['href']:
                        mirror_link = link['href']
                        d_link = await self.resolve_download_link(mirror_link)
                        
                        book["Direct_Download_Link"] = d_link["GET"] or None
                    break
        return book

        # TODO: add method to get scimag data
async def test():
    sr = SearchRequest("romance")

    x = await sr.aggregate_fiction_data()

    print(x)


asyncio.run(test())
