# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library

import httpx
import asyncio
import urllib.parse

from bs4 import BeautifulSoup
from bs4.element import Tag

from json import dumps
from typing import Optional, List, Dict



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
        self.query = query
        self.search_type = search_type

        if len(self.query) < 3:
            raise ValueError("Query is too short")
        
    # def __str__(self) -> str:
    #     return dumps(self, indent=4, default=self.default, ensure_ascii=False)

    # def __repr__(self) -> str:
    #     return f"SearchRequest({', '.join(f'{attr}={repr(getattr(self, attr))}' for attr in self.__dict__ if not attr.startswith('_') and getattr(self, attr) is not None)})"

    # @staticmethod
    # def default(obj):
        
    #     if isinstance(obj, SearchRequest):
    #         return {
    #             "_": obj.__class__.__name__,
    #             **{attr: getattr(obj, attr) for attr in obj.__dict__ if not attr.startswith('_') and attr not in ["raw"] and getattr(obj, attr) is not None}
    #         }
        
    #     return str(obj)
        
    async def resolve_download_link(self, client, mirror_link: str) -> Dict[str, str]:
        SOURCES = {"GET", "Cloudflare", "IPFS.io"}
        response = (await client.get(mirror_link)).content
        soup = BeautifulSoup(response, "html.parser")
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

    async def fetch_page(self, client: httpx.AsyncClient, url):
        response = (await client.get(url)).content
        return response
    
    
    async def get_search_page(self, client: httpx.AsyncClient, type: Optional[str] = "default"):
        """
        Get the search page from libgen.rs.

        Args:
            self (SearchRequest): The search request object.
            type (Optional[str], optional): The type of search to perform.
                Defaults to "default" for default search(non-fiction/sci-tech).

        Returns:
            aiohttp.ClientResponse: The search page as a response object.
        """
        parsed_query = "+".join(self.query.split(" "))  # type: str
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
        

        return (await client.get(search_url)).content
    

    async def aggregate_request_data(self) -> List[Dict[str, str]]:
        """
        Aggregate the request data from the search page.

        Args:
            self (SearchRequest): The search request object.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the aggregated request data.
        """
        # FIXME: Handle adding direct download links better 
        async with httpx.AsyncClient() as client:
            search_page = await self.get_search_page(client)

            soup = BeautifulSoup(search_page, "html.parser")
            self.strip_i_tag_from_soup(soup)

            tables = soup.find_all("table", {"border": "0", "rules": "cols", "width": "100%"})

            raw_data = []

            for table in tables:
                rows = table.find_all("tr")[1:] 

                if not rows:
                    continue

                book_data = {}
                img_src = None
                md5 = None

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

                for col_name in self.col_names:
                    if col_name not in book_data:
                        book_data[col_name] = ""

                if img_src:
                    book_data['Cover'] = f"https://libgen.rs{img_src}"
                if md5:
                    book_data['MD5'] = md5.lower()

                raw_data.append(book_data)


            for book in raw_data:
                if "ID" in book and "MD5" in book and "Title" in book and "Extension" in book:
                    id = book["ID"]
                    download_id = str(id)[:-3] + "000"
                    md5 = book["MD5"]
                    title = urllib.parse.quote(book["Title"])
                    extension = book["Extension"]
                    book['Direct_Download_Link'] = f"https://download.library.lol/main/{download_id}/{md5}/{title}.{extension}"
                    del book['MD5']
            
        

        return raw_data
    
    

        # TODO: add method to get scimag data

    async def aggregate_fiction_data(self) -> List[Dict[str, str]]:
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

        async with httpx.AsyncClient() as client:
            search_page_content = await self.get_search_page(client, type="fiction")
            soup = BeautifulSoup(search_page_content, "html.parser")
            
            tbody = soup.find("tbody")
            fiction_data = []
            tasks = []

            async def process_row(row):
                title_td = row.find_all('td')[2]
                link_tag = title_td.find('a')
                link = f"https://libgen.rs{link_tag['href']}"

                r_soup_content = await self.fetch_page(client, link)
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
                book["Cover"] = f"https://libgen.rs{img_tag['src']}" if img_tag else None

                download_links = record.find('ul', class_='record_mirrors').find_all('a')
                mirror_link = None
                for link in download_links:
                    if 'library.lol/fiction' in link['href']:
                        mirror_link = link['href']
                        break

                if mirror_link:
                    
                    d_link = await self.resolve_download_link(client, mirror_link)
                    book["Direct_Download_Link"] = d_link.get("GET", d_link.get("Cloudflare", d_link.get("IPFS.io", None)))
                fiction_data.append(book)

            for row in tbody.find_all('tr'):
                tasks.append(process_row(row))

            await asyncio.gather(*tasks)

        return fiction_data
