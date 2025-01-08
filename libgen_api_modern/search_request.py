# Copyright (c) 2024 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

import asyncio
import re
import httpx
from lxml import html
from typing import Optional, List, Dict
from typing import Optional, List, Dict


class SearchRequest:

    domains = ["libgen.is", "libgen.st", "libgen.rs"]  # List of fallback domains
    used_domain = None
    col_names = [
        "ID", "Author(s)", "Title", "Publisher",
        "Year", "Pages", "Language", "Size", "Extension"
    ]

    def __init__(self, query: str, search_type: Optional[str] = "def") -> None:
        self.query = query
        self.search_type = search_type
        if len(self.query) < 3:
            raise ValueError("Query is too short")

    async def resolve_mirrors(self, client: httpx.AsyncClient, mirror: str) -> Dict[str, str]:
        


    async def fetch_page(self, client: httpx.AsyncClient, url: str) -> str:
        response = await client.get(url, timeout=10)
        return response.text

    async def get_search_page(self, client: httpx.AsyncClient, type: str = "default") -> str:
        parsed_query = "+".join(self.query.split(" "))

        for domain in self.domains:
            search_url = {
                "default": f"https://{domain}/search.php?req={parsed_query}&lg_topic=libgen&open=0&view=simple&res=100&phrase=1&column={self.search_type}",
                "fiction": f"https://{domain}/fiction/?q={parsed_query}",
                "scimag": f"https://{domain}/scimag/?q={parsed_query}"
            }.get(type, "default")

            try:
                res = await self.fetch_page(client, search_url)
                if res:
                    self.used_domain = domain
                    return res
            except httpx.HTTPError:
                print(f"Failed to fetch from {domain}, trying next...")

        raise Exception("All LibGen mirrors are unreachable.")

    async def aggregate_request_data(self) -> List[Dict[str, str]]:
        async with httpx.AsyncClient() as client:
            search_page = await self.get_search_page(client)
            # with open("search_page.html", "w") as f:
                # f.write(search_page)
            # return
            tree = html.fromstring(search_page)
            table = tree.xpath("//table[@width='100%']")
            raw_data = []
            print(table)

            rows = table[0].xpath(".//tr")[1:]
            if not rows:
                return "No results"


            for row in rows:
                book_data = {}
                cells = row.xpath(".//td")
                if len(cells) < 2:
                    continue
                for cell in cells:
                    value = cell.text_content().strip()
                    if not value:
                        value = ""
                    book_data[self.col_names[len(book_data)]] = value
                    mirrors = {}
                    m_sources = cell.xpath(".//a")
                    if m_sources:
                        for m_source in m_sources:
                            mirrors[m_source.get('title')] = m_source.get('href')

                    book_data["Mirrors"] = mirrors

                raw_data.append(book_data)

            return raw_data





            tables = tree.xpath("//table[@border='0' and @rules='rows' and @width='100%' and @align='center']")


            for table in tables:
                rows = table.xpath(".//tr")[1:]
                if not rows:
                    continue

                book_data = {}
                cover = table.xpath(".//td[@rowspan]/a/img/@src")
                book_data["Cover"] = f"https://{self.used_domain}{cover[0]}" if cover else None

                title_link = table.xpath(".//tr[td/b]/td[3]//a")
                if title_link:
                    book_data["Title"] = title_link[0].text_content().strip()
                    book_data["Mirror"] = f"https://{self.used_domain}{title_link[0].get('href')[2:] if title_link[0].get('href').startswith('../') else title_link[0].get('href')}"

                for row in rows:
                    cells = row.xpath(".//td")
                    if len(cells) < 2:
                        continue # Skip rows with less data
                    label = cells[0].text_content().strip().replace(":", "")
                    value = cells[1].text_content().strip()
                    if label in self.col_names:
                        book_data[label] = value
                        if len(cells) > 3 and cells[2].text_content().strip().replace(":", "") in self.col_names:
                            book_data[cells[2].text_content().strip().replace(":", "")] = cells[3].text_content().strip()

                for col_name in self.col_names:
                    book_data.setdefault(col_name, "")

                raw_data.append(book_data)

            tasks = [self.resolve_mirrors(client, book["Mirror"]) for book in raw_data if "Mirror" in book]
            mirror_results = await asyncio.gather(*tasks)

            for book, mirrors in zip(raw_data, mirror_results):
                book.pop("Mirror", None)
                book.update({f"Direct Download Link {i+1}": link for i, link in enumerate(mirrors.values())})

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
