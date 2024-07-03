# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library

import requests
import logging
import urllib.parse

from bs4 import BeautifulSoup
from bs4.element import Tag

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

    def strip_i_tag_from_soup(
        self, soup: BeautifulSoup, /) -> None:
        """
        Remove <i> tags from a BeautifulSoup object.

        Args:
            soup (BeautifulSoup): The BeautifulSoup object to modify.

        Returns:
            None
        """
        # Find all <i> tags
        subheadings: List[Tag] = soup.find_all("i")
        
        # Remove each <i> tag
        for subheading in subheadings:
            subheading.decompose()

    def get_search_page(self) -> requests.Response:
        """
        Get the search page from libgen.rs.

        Args:
            self (SearchRequest): The search request object.

        Returns:
            requests.Response: The search page as a response object.
        """
        # Join the query words with a '+' to form the parsed query
        parsed_query = "+".join(self.query.split(" "))  # type: str

        # Form the search URL with the parsed query and search type
        search_url = (
            f"https://libgen.rs/search.php?"
            f"req={parsed_query}&"
            f"res=100&"
            f"view=detailed&"
            f"phrase=1&"
            f"column={self.search_type.lower()}"  # type: str
        )

        # Send a GET request to the search URL and return the response
        search_page = requests.get(search_url)  # type: requests.Response
        return search_page
    

    def aggregate_request_data(self) -> List[Dict[str, str]]:
        """
        Aggregate the request data from the search page.

        Args:
            self (SearchRequest): The search request object.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the aggregated request data.
        """
        # Get the search page
        search_page = self.get_search_page()

        # Parse the search page using BeautifulSoup
        soup = BeautifulSoup(search_page.content, "html.parser")
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
                book['Direct_Download_Link'] = f"http://download.library.lol/main/{download_id}/{md5}/{title}.{extension}"

        return raw_data



x = SearchRequest("prince and the pauper")
print(x.aggregate_request_data())