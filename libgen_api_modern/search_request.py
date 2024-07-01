# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library

import requests
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


    def aggregate_request_data(self) -> List[Dict[str, Union[str, int, None]]]:
        """
        Aggregate the request data from the search page.

        Returns:
            List[Dict[str, Union[str, int, None]]]: A list of dictionaries containing the request data.
                Each dictionary represents a book and contains the following keys:
                - 'ID': The ID of the book.
                - 'Title': The title of the book.
                - 'Author(s)': The author(s) of the book.
                - 'Year': The year of publication of the book.
                - 'Pages': The number of pages in the book.
                - 'Language': The language of the book.
                - 'Extension': The file extension of the book.
                - 'Size': The size of the book.
                - 'Cover': The URL of the cover image of the book.
                - 'MD5': The MD5 hash of the book.
                - 'Direct_Download_Link': The direct download link of the book.
        """
        search_page = self.get_search_page()
        soup = BeautifulSoup(search_page.text, "html.parser")
        self.strip_i_tag_from_soup(soup)

        # Locate the relevant data table
        information_table = soup.find_all("table")[2]

        raw_data = []
        for row in information_table.find_all("tr")[1:]:  # Skip row 0 as it is the headings row
            row_data = []
            img_src = None
            md5 = None
            
            for td in row.find_all("td"):
                if td.find("a") and td.find("a").has_attr("title") and td.find("a")["title"] != "":
                    row_data.append(td.a["href"])
                else:
                    row_data.append("".join(td.stripped_strings))

                # Check for the <img> tag in the current cell
                img_tag = td.find('img')
                if img_tag:
                    img_src = img_tag.get('src')

                # Check for the <a> tag with the href attribute containing md5
                a_tag = td.find('a', href=True)
                if a_tag and 'md5' in a_tag['href']:
                    md5 = a_tag['href'].split('md5=')[-1]

            data_dict = dict(zip(self.col_names, row_data))
            
            # Add the cover image source to the current entry
            if img_src:
                data_dict['Cover'] = f"https://libgen.rs{img_src}"
            else:
                data_dict['Cover'] = None

            # Add the md5 value to the current entry
            if md5:
                data_dict['MD5'] = md5.lower()
            else:
                data_dict['MD5'] = None

            raw_data.append(data_dict)

        # Add a direct download link to each result
        for book in raw_data:
            id = book["ID"]
            download_id = str(id)[:-3] + "000"
            md5 = book["MD5"]
            title = urllib.parse.quote(book["Title"])
            extension = book["Extension"]
            book['Direct_Download_Link'] = (
                f"http://download.library.lol/main/{download_id}/{md5}/{title}.{extension}"
            )

        return raw_data
