# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library

import asyncio
import re
import tracemalloc
from asyncio import sslproto
from aiohttp import ClientSession
from bs4 import BeautifulSoup
from bs4.element import Tag

from typing import Optional, List, Dict

tracemalloc.start()
setattr(sslproto._SSLProtocolTransport, "_start_tls_compatible", True)



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
      
        self.query = query
        self.search_type = search_type

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

                raw_data.append(book_data)

        


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
                    if 'library.lol/fiction' in link['href'] or 'library.gift/fiction' in link['href']:
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