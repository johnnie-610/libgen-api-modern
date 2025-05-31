# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/__init__.py
#
# This file is part of the libgen-api-modern library

# Main unified search functions with fallback logic
from .lib import (
    search_unified_async as search_async,
    search_unified_sync as search_sync,
    search_filtered_async,
    search_filtered_sync,
)

# Expose underlying clients and specific search functions if advanced users need direct access
from .new.client import LibgenClient
from .new.client import search as new_api_search_async # Expose new API direct search if needed
from .new.client import search_sync as new_api_search_sync

from .old.libgen_search import LibgenSearch

# Errors
from .errors import (
    LibgenError, LibgenNetworkError, LibgenSearchError,
    LibgenParseError, LibgenResourceError, LibgenConfigError
)
# Common types and models
from .models import BookData, DownloadLinks
from .enums import SearchType
from .types import URL, LibgenID, AuthorList, ProxyList

__all__ = [
    # Unified search functions (recommended for most users)
    "search_async", "search_sync",
    "search_filtered_async",
    "search_filtered_sync",

    # Client classes for direct/advanced access
    "LibgenClient", "LibgenSearch",

    # Direct new API search (without old API fallback)
    "new_api_search_async", "new_api_search_sync",

    # Error classes
    "LibgenError", "LibgenNetworkError", "LibgenSearchError",
    "LibgenParseError", "LibgenResourceError", "LibgenConfigError",

    # Models and Enums
    "BookData", "DownloadLinks", "SearchType",

    # Basic Types
    "URL", "LibgenID", "AuthorList", "ProxyList",
]

__version__ = "0.2.1"