from dataclasses import dataclass

@dataclass(frozen=True)
class BkData:
    id: str
    authors: tuple[str, ...]
    title: str
    series: str | None
    publisher: str
    year: str
    pages: str
    language: str
    size: str
    extension: str
    mirrors: dict[str, str]
    isbn: str | None = None
    edition: str | None = None


@dataclass(frozen=True)
class DownloadLinks:
    get_link: str | None
    cloudflare_link: str | None
    ipfs_link: str | None
    pinata_link: str | None
    cover_link: str | None


@dataclass(frozen=True)
class BookData:
    id: str
    authors: tuple[str, ...]
    title: str
    publisher: str | None
    year: str | None
    pages: str | None
    language: str | None
    size: str | None
    extension: str | None
    isbn: str | None
    cover_url: str | None
    download_links: DownloadLinks | None


@dataclass(frozen=True)
class SearchResults:
    total_results: int
    books: list[BookData]
    next_page_url: str | None
    current_page: int
