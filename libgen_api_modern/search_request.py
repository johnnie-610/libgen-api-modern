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
            List[Dict[str, str]]: A list of dictionaries representing the search results,
                where each dictionary contains the book data.
        """
        # Fetch the search page
        search_page = self.get_search_page()

        # Parse the search page
        soup = BeautifulSoup(search_page.text, "html.parser")

        # Remove any <i> tags from the soup
        self.strip_i_tag_from_soup(soup)

        # Find all tables with the specified attributes
        tables = soup.find_all("table", {"border": "0", "rules": "cols", "width": "100%"})

        # Initialize a list to store the raw book data
        raw_data = []

        # Iterate over each table
        for table in tables:
            # Find all rows in the table
            rows = table.find_all("tr")[1:]

            # Iterate over each row
            for row in rows:
                # Extract the cover image source and md5 hash
                self.extract_cover_image_and_md5(row, raw_data)

                # Extract other book data
                self.extract_book_data(row, raw_data)

        # Add a direct download link to each result
        self.add_direct_download_links(raw_data)

        return raw_data

    def extract_cover_image_and_md5(
            self, row: Tag, raw_data: List[Dict[str, str]]
    ) -> None:
        """
        Extract the cover image source and md5 hash from the given row.

        Args:
            row (Tag): The row to extract the data from.
            raw_data (List[Dict[str, str]]): The list to store the raw book data.

        Returns:
            None
        """
        # Extract the cover image source
        img_tag: Optional[Tag] = row.find('img')
        img_src: Optional[str] = img_tag.get('src') if img_tag else None

        # Extract the md5 hash
        a_tag: Optional[Tag] = row.find('a', href=True)
        md5: Optional[str] = a_tag['href'].split('md5=')[-1] if a_tag and 'md5' in a_tag['href'] else None

        # Store the extracted data
        book_data: Dict[str, str] = {
            'Title': row.find_all("td")[2].get_text(strip=True),
            'Cover': f"https://libgen.rs{img_src}" if img_src else "",
            'MD5': md5.lower() if md5 else ""
        }
        raw_data.append(book_data)

    def extract_book_data(
            self, row: Tag, raw_data: List[Dict[str, str]]
    ) -> None:
        """
        Extract other book data from the given row.

        Args:
            row (Tag): The row to extract the data from.
            raw_data (List[Dict[str, str]]): The list to store the raw book data.

        Returns:
            None
        """
        # Extract book data from the row
        cells = row.find_all("td")
        for i in range(len(cells)):
            if len(cells) < 2:
                continue  # Skip rows with insufficient data

            label: str = cells[i].get_text(strip=True).replace(":", "")
            if label in self.col_names:
                try:
                    raw_data[-1][label] = cells[i + 1].get_text(strip=True)
                except Exception as e:
                    logging.error(f"An error occurred while extracting the book data: {e}")

            if len(cells) > 3 and cells[i + 2].get_text(strip=True).replace(":", "") in self.col_names:
                try:
                    raw_data[-1][cells[i + 2].get_text(strip=True).replace(":", "")] = cells[i + 3].get_text(strip=True)
                except Exception as e:
                    logging.error(f"An error occurred while extracting the additional book data: {e}")

    def add_direct_download_links(
        self,
        raw_data: List[Dict[str, str]]
    ) -> None:
        """
        Add a direct download link to each result.

        Args:
            raw_data (List[Dict[str, str]]): The list of raw book data.

        Returns:
            None
        """
        for book in raw_data:
            if (
                "ID" in book
                and "MD5" in book
                and "Title" in book
                and "Extension" in book
            ):
                id: int = book["ID"]
                download_id: str = str(id)[:-3] + "000"
                md5: str = book["MD5"]
                title: str = urllib.parse.quote(book["Title"])
                extension: str = book["Extension"]
                book['Direct_Download_Link'] = (
                    f"http://download.library.lol/main/{download_id}/{md5}/{title}.{extension}"
                )

        