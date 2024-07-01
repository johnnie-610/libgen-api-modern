# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library

import pytest
from unittest.mock import patch, MagicMock
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

    @patch('api.search_request.requests.get')
    def test_get_search_page(self, mock_get, search_request):
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_get.return_value = mock_response

        response = search_request.get_search_page()
        assert response.status_code == 200
        mock_get.assert_called_once()

    def test_strip_i_tag_from_soup(self, search_request):
        html = "<html><body><i>italic</i><p>paragraph</p></body></html>"
        soup = BeautifulSoup(html, 'html.parser')
        search_request.strip_i_tag_from_soup(soup)
        assert soup.find('i') is None

    @patch('api.search_request.SearchRequest.get_search_page')
    def test_aggregate_request_data(self, mock_get_search_page, search_request):
        html = '''
        <html><body>
        <table></table>
        <table></table>
        <table>
            <tr><td></td></tr>
            <tr><td>1</td><td>Author</td><td>Title</td><td>Series</td><td>Publisher</td><td>Edition</td><td>2024</td><td>123</td><td>English</td><td>1 MB</td><td>1234567890</td><td>Periodical</td><td>City</td><td>pdf</td></tr>
        </table>
        </body></html>
        '''
        mock_response = MagicMock()
        mock_response.text = html
        mock_get_search_page.return_value = mock_response

        results = search_request.aggregate_request_data()
        assert len(results) == 1
        assert results[0]['ID'] == '1'


# Test cases for LibgenSearch class
class TestLibgenSearch:

    @pytest.fixture
    def libgen_search(self):
        return LibgenSearch()

    @patch('api.libgen_search.SearchRequest.aggregate_request_data')
    def test_search(self, mock_aggregate_request_data, libgen_search):
        mock_aggregate_request_data.return_value = [{"Title": "Some Book"}]

        results = libgen_search.search("Python", "title")
        assert len(results) == 1
        assert results[0]['Title'] == "Some Book"

    @patch('api.libgen_search.SearchRequest.aggregate_request_data')
    def test_search_filtered(self, mock_aggregate_request_data, libgen_search):
        mock_aggregate_request_data.return_value = [{"Author(s)": "Author", "Title": "Some Book"}]

        filters = {"Author(s)": "Author"}
        results = libgen_search.search_filtered("Python", filters, "title")
        assert len(results) == 1
        assert results[0]['Author(s)'] == "Author"

    @patch('api.libgen_search.SearchRequest.aggregate_request_data')
    def test_search_title(self, mock_aggregate_request_data, libgen_search):
        mock_aggregate_request_data.return_value = [{"Title": "Some Book"}]

        results = libgen_search.search_title("Python")
        assert len(results) == 1
        assert results[0]['Title'] == "Some Book"

    @patch('api.libgen_search.SearchRequest.aggregate_request_data')
    def test_search_author(self, mock_aggregate_request_data, libgen_search):
        mock_aggregate_request_data.return_value = [{"Author(s)": "Author"}]

        results = libgen_search.search_author("Python")
        assert len(results) == 1
        assert results[0]['Author(s)'] == "Author"

    @patch('api.libgen_search.SearchRequest.aggregate_request_data')
    def test_search_title_filtered(self, mock_aggregate_request_data, libgen_search):
        mock_aggregate_request_data.return_value = [{"Author(s)": "Author", "Title": "Some Book"}]

        filters = {"Author(s)": "Author"}
        results = libgen_search.search_title_filtered("Python", filters)
        assert len(results) == 1
        assert results[0]['Author(s)'] == "Author"

    @patch('api.libgen_search.SearchRequest.aggregate_request_data')
    def test_search_author_filtered(self, mock_aggregate_request_data, libgen_search):
        mock_aggregate_request_data.return_value = [{"Author(s)": "Author", "Title": "Some Book"}]

        filters = {"Author(s)": "Author"}
        results = libgen_search.search_author_filtered("Python", filters)
        assert len(results) == 1
        assert results[0]['Author(s)'] == "Author"


if __name__ == '__main__':
    pytest.main()
