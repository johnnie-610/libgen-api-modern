import pytest
from libgen_api_modern.libgen_search import LibgenSearch

class TestLibgenSearch:

    # search_fiction returns a list of fiction books for a valid query
    @pytest.mark.asyncio
    async def test_search_fiction_valid_query(self, mocker):
        mocker.patch('libgen_api_modern.search_request.SearchRequest.aggregate_fiction_data', return_value=[{"Title": "Pirate Adventures"}])
        result = await LibgenSearch.search_fiction("pirate")
        assert result == [{"Title": "Pirate Adventures"}], "Arrr! The search results be not what I expected!"

    # search_fiction_filtered returns filtered fiction books based on provided filters
    @pytest.mark.asyncio
    async def test_search_fiction_filtered_valid_query(self, mocker):
        mocker.patch('libgen_api_modern.search_request.SearchRequest.aggregate_fiction_data', return_value=[{"Title": "Pirate Adventures", "Author": "Blackbeard"}])
        filters = {"Author": "Blackbeard"}
        result = await LibgenSearch().search_fiction_filtered("pirate", filters)
        assert result == [{"Title": "Pirate Adventures", "Author": "Blackbeard"}], "Shiver me timbers! The filtered results be off course!"

    # search returns a list of books for a valid query and search type
    @pytest.mark.asyncio
    async def test_search_valid_query_and_type(self, mocker):
        mocker.patch('libgen_api_modern.search_request.SearchRequest.aggregate_request_data', return_value=[{"Title": "Pirate Code"}])
        result = await LibgenSearch.search("pirate", "title")
        assert result == [{"Title": "Pirate Code"}], "Blimey! The search results be not what I charted!"

    # search_filtered returns filtered books based on provided filters and search type
    @pytest.mark.asyncio
    async def test_search_filtered_valid_query_and_type(self, mocker):
        mocker.patch('libgen_api_modern.search_request.SearchRequest.aggregate_request_data', return_value=[{"Title": "Pirate Code", "Author": "Blackbeard"}])
        filters = {"Author": "Blackbeard"}
        result = await LibgenSearch.search_filtered("pirate", filters, "title")
        assert result == [{"Title": "Pirate Code", "Author": "Blackbeard"}], "Arrr! The filtered results be not what I expected!"

    # search_title returns a list of books for a valid title query
    @pytest.mark.asyncio
    async def test_search_title_valid_query(self, mocker):
        mocker.patch('libgen_api_modern.search_request.SearchRequest.aggregate_request_data', return_value=[{"Title": "Pirate Code"}])
        result = await LibgenSearch.search_title("pirate")
        assert result == [{"Title": "Pirate Code"}], "Blimey! The title search results be not what I charted!"

    # search_fiction raises ValueError for queries shorter than 3 characters
    @pytest.mark.asyncio
    async def test_search_fiction_short_query(self):
        with pytest.raises(ValueError, match="Search query is too short"):
            await LibgenSearch.search_fiction("pi")

    # search_fiction_filtered raises ValueError for queries shorter than 3 characters
    @pytest.mark.asyncio
    async def test_search_fiction_filtered_short_query(self):
        with pytest.raises(ValueError, match="Search query is too short"):
            await LibgenSearch().search_fiction_filtered("pi", {})

    # search raises ValueError for queries shorter than 3 characters
    @pytest.mark.asyncio
    async def test_search_short_query(self):
        with pytest.raises(ValueError, match="Search query is too short"):
            await LibgenSearch.search("pi")

    # search_filtered raises ValueError for queries shorter than 3 characters
    @pytest.mark.asyncio
    async def test_search_filtered_short_query(self):
        with pytest.raises(ValueError, match="Search query is too short"):
            await LibgenSearch.search_filtered("pi", {})

    # search_fiction raises Exception for unexpected errors during search
    @pytest.mark.asyncio
    async def test_search_fiction_unexpected_error(self, mocker):
        mocker.patch('libgen_api_modern.search_request.SearchRequest.aggregate_fiction_data', side_effect=Exception("Unexpected error"))
        with pytest.raises(Exception, match="An error occurred during the search"):
            await LibgenSearch.search_fiction("pirate")