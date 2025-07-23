# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from .client import search_async, search_sync
from .errors import (
    LibgenError,
    LibgenNetworkError,
    LibgenSearchError,
    LibgenParseError,
)
from .models import BookData, DownloadLinks

__all__ = [
    # Core search functions
    "search_async",
    "search_sync",
    # Error classes
    "LibgenError",
    "LibgenNetworkError",
    "LibgenSearchError",
    "LibgenParseError",
    # Models
    "BookData",
    "DownloadLinks",
]

__version__ = "1.0.0"