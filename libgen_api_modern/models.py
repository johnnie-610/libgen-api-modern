from dataclasses import dataclass


@dataclass(frozen=True)
class BookData:
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
    isbn: str | None
    edition: str | None
    cover_url: str | None
    download_url: str | None


@dataclass(frozen=True)
class BkData:
    id: str
    authors: tuple[str, ...]  # Tuple for immutability and better performance
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
