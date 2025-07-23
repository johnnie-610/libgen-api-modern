import pytest
from libgen.client import search_async, search_sync
from libgen.errors import LibgenSearchError
from libgen.models import BookData

@pytest.mark.asyncio
async def test_search_async_success():
    """Tests a successful async search."""
    results = await search_async("python data science")
    assert isinstance(results, list)
    assert len(results) > 0
    book = results[0]
    assert isinstance(book, BookData)
    assert book.title is not None
    assert book.id is not None
    # Check if at least some download links were resolved
    assert any(b.download_links and b.download_links.get_link for b in results)

def test_search_sync_success():
    """Tests a successful sync search."""
    results = search_sync(" Principia Mathematica")
    assert isinstance(results, list)
    assert len(results) > 0
    book = results[0]
    assert isinstance(book, BookData)
    assert "Principia" in book.title
    assert any(b.download_links and b.download_links.get_link for b in results)

@pytest.mark.asyncio
async def test_search_async_no_results():
    """Tests an async search that returns no results."""
    results = await search_async("nonexistentbookxyz123abc")
    assert isinstance(results, list)
    assert len(results) == 0

def test_search_sync_no_results():
    """Tests a sync search that returns no results."""
    results = search_sync("nonexistentbookxyz123abc")
    assert isinstance(results, list)
    assert len(results) == 0

def test_bookdata_model():
    """Tests the integrity of the BookData model."""
    book = BookData(
        id="12345",
        title="Test Book",
        authors=("Author One",),
        year="2024",
        extension="pdf",
        size="10 MB",
        pages="300",
        publisher="Test Publisher",
        language="English",
        mirror_url="http://example.com"
    )
    assert book.title == "Test Book"
    assert book.language == "English"
    assert book.download_links is None