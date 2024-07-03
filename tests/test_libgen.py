# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library

import pytest
from bs4 import BeautifulSoup
from libgen_api_modern.search_request import SearchRequest
from libgen_api_modern.libgen_search import LibgenSearch

# Test cases for SearchRequest class
class TestSearchRequest:

    @pytest.fixture
    def search_request(self):
        return SearchRequest("Python", "title")

    def test_initialization(self, search_request):
        assert search_request.query == "Python"
        assert search_request.search_type == "title"

    def test_initialization_short_query(self):
        with pytest.raises(ValueError):
            SearchRequest("Py")

    def test_get_search_page(self, search_request):
        response = search_request.get_search_page()
        assert response.status_code == 200

    def test_strip_i_tag_from_soup(self, search_request):
        html = "<html><body><i>italic</i><p>paragraph</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        search_request.strip_i_tag_from_soup(soup)
        assert soup.find('i') is None

    def test_aggregate_request_data(self, search_request):
        results = search_request.aggregate_request_data()
        assert len(results) > 0


# Test cases for LibgenSearch class
class TestLibgenSearch:

    @pytest.fixture
    def libgen_search(self):
        return LibgenSearch()

    def test_search(self, libgen_search):
        results = libgen_search.search("Python", "title")
        assert len(results) > 0
        assert "Title" in results[0]

    def test_search_filtered(self, libgen_search):
        filters = {"Author(s)": "Mark Lutz"}
        results = libgen_search.search_filtered("Learning Python", filters, "title")
        assert len(results) > 0
        assert results[0]['Author(s)'] == "Mark Lutz"

    def test_search_title(self, libgen_search):
        results = libgen_search.search_title("Python")
        assert len(results) > 0
        assert "Title" in results[0]

    def test_search_author(self, libgen_search):
        results = libgen_search.search_author("Mark Lutz")
        assert len(results) > 0
        assert "Author(s)" in results[0]

    def test_search_title_filtered(self, libgen_search):
        filters = {"Author(s)": "Mark Lutz"}
        results = libgen_search.search_title_filtered("Learning Python", filters)
        assert len(results) > 0
        assert results[0]['Author(s)'] == "Mark Lutz"

    def test_search_author_filtered(self, libgen_search):
        filters = {"Title": "Learning Python"}
        results = libgen_search.search_author_filtered("Mark Lutz", filters)
        assert len(results) > 0
        assert results[0]['Title'] == "Learning Python"


if __name__ == '__main__':
    pytest.main()
