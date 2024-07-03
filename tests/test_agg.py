import unittest
from unittest.mock import Mock
from libgen_api_modern.search_request import SearchRequest

class TestSearchRequest(unittest.TestCase):

    def setUp(self):
        self.search_request = SearchRequest("test query")

    def test_aggregate_request_data_keys(self):
        # Mock the necessary methods to isolate the function
        self.search_request.get_search_page = Mock(return_value=Mock(text='<html><table><tr><td>test</td></tr></table></html>'))
        self.search_request.strip_i_tag_from_soup = Mock()
        self.search_request.col_names = ['ID', 'Title', 'Author(s)', 'Year', 'Pages', 'Language', 'Extension', 'Size']

        result = self.search_request.aggregate_request_data()

        self.assertTrue(all('ID' in book for book in result))
        self.assertTrue(all('Title' in book for book in result))
        self.assertTrue(all('Author(s)' in book for book in result))
        self.assertTrue(all('Year' in book for book in result))
        self.assertTrue(all('Pages' in book for book in result))
        self.assertTrue(all('Language' in book for book in result))
        self.assertTrue(all('Extension' in book for book in result))
        self.assertTrue(all('Size' in book for book in result))

    def test_aggregate_request_data_missing_cover(self):
        self.search_request.get_search_page = Mock(return_value=Mock(text='<html><table><tr><td><a>test</a></td></tr></table></html>'))
        self.search_request.strip_i_tag_from_soup = Mock()
        self.search_request.col_names = ['ID', 'Title', 'Author(s)', 'Year', 'Pages', 'Language', 'Extension', 'Size']

        result = self.search_request.aggregate_request_data()

        self.assertTrue(all('Cover' not in book or book['Cover'] is None for book in result))

    def test_aggregate_request_data_missing_md5(self):
        self.search_request.get_search_page = Mock(return_value=Mock(text='<html><table><tr><td><a href="md5=test">test</a></td></tr></table></html>'))
        self.search_request.strip_i_tag_from_soup = Mock()
        self.search_request.col_names = ['ID', 'Title', 'Author(s)', 'Year', 'Pages', 'Language', 'Extension', 'Size']

        result = self.search_request.aggregate_request_data()

        self.assertTrue(all('MD5' not in book or book['MD5'] is None for book in result))

    def test_aggregate_request_data_direct_download_links(self):
        self.search_request.get_search_page = Mock(return_value=Mock(text='<html><table></table><table></table><table><tr><td><a>test</a></td></tr></table></html>'))
        self.search_request.strip_i_tag_from_soup = Mock()
        self.search_request.col_names = ['ID', 'Title', 'Author(s)', 'Year', 'Pages', 'Language', 'Extension', 'Size']

        result = self.search_request.aggregate_request_data()

        for book in result:
            self.assertTrue('Direct_Download_Link' in book)
            self.assertTrue(book['Direct_Download_Link'].startswith('http://download.library.lol/main/'))

if __name__ == '__main__':
    unittest.main()