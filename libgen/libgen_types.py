# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/types.py
#
# This file is part of the libgen-api-modern library

from typing import Dict, List, Optional, Union, TypedDict, Literal, Any, Tuple, Protocol, Callable, TypeVar, Awaitable

# Type aliases for basic types
LibgenID = str
ISBN = str
MD5Hash = str
URL = str
FileSize = str
FileExtension = str
Language = str
Year = str
Pages = str

# Type aliases for complex types
AuthorList = Tuple[str, ...]
MirrorDict = Dict[str, URL]
ProxyList = List[str]

# Search types
SearchField = Literal["def", "title", "author", "series", "publisher", "year", "language", "isbn", "md5"]

# TypedDict for raw search results
class RawBookResult(TypedDict, total=False):
    """Dictionary representation of a book search result."""
    id: str
    title: str
    authors: str
    publisher: str
    year: str
    language: str
    pages: str
    size: str
    extension: str
    mirror: str
    cover: str

# TypedDict for search parameters
class SearchParams(TypedDict, total=False):
    """Dictionary representation of search parameters."""
    req: str
    res: str
    covers: str
    filesuns: str
    page: str

# TypedDict for mirror links
class MirrorLinks(TypedDict, total=False):
    """Dictionary representation of mirror links."""
    get: Optional[URL]
    cloudflare: Optional[URL]
    ipfs: Optional[URL]
    pinata: Optional[URL]
    cover: Optional[URL]

# Protocol for HTTP clients
class HTTPClient(Protocol):
    """Protocol for HTTP clients."""
    async def get(self, url: str, **kwargs) -> Any: ...
    async def close(self) -> None: ...

# Type variables for generic functions
T = TypeVar('T')
R = TypeVar('R')

# Type aliases for callback functions
AsyncCallback = Callable[[T], Awaitable[R]]
SyncCallback = Callable[[T], R]

# Type alias for search result
SearchResult = Union[List[RawBookResult], List['BookData']]

# Forward references
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    pass