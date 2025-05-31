# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/lib.py
#
# This file is part of the libgen-api-modern library

import logging
from typing import List, Dict, Any

from .models import BookData
from .new.client import search as new_search_async, search_sync as new_search_sync
from .old.libgen_search import LibgenSearch as OldLibgenSearch
from .enums import SearchType
from .errors import LibgenSearchError, LibgenError # LibgenNetworkError not directly raised here but good to have
from .types import ProxyList

logger = logging.getLogger(__name__)

async def search_unified_async(
        query: str,
        search_type: SearchType = SearchType.DEFAULT,
        proxies: ProxyList | None = None
) -> List[BookData]:
    """
    Asynchronously searches for books using the Libgen API, prioritizing the old API,
    and falling back to the new API if the old API fails.

    Args:
        query: The search query.
        search_type: The type of search to perform (e.g., "def", "author", "title").
                     Mainly used by the old API.
        proxies: The list of proxies, primarily for the new API.

    Returns:
        A list of BookData objects representing the search results.

    Raises:
        LibgenSearchError: If both API searches fail or the query is invalid.
    """
    last_error_old_api: Exception | None = None
    try:
        logger.info("Attempting search with old Libgen client for query: '%s'", query)
        # OldLibgenSearch.search does not currently accept proxies.
        results = await OldLibgenSearch.search(query, search_type)
        if results: # Old API might return empty list for "no results"
            logger.info("Old Libgen client found %d results for query: '%s'", len(results), query)
            return results
        logger.info("Old Libgen client returned no results for query: '%s'.", query)
    except LibgenError as e: # Catch Libgen specific errors from old API if any
        logger.warning("Old Libgen search failed for query '%s': %s", query, e)
        last_error_old_api = e
    except Exception as e: # Catch other errors like ValueError for short query
        logger.warning("Old Libgen search failed unexpectedly for query '%s': %s", query, e, exc_info=True)
        last_error_old_api = e
        # If it's a ValueError (e.g. query too short), re-raise immediately or wrap
        if isinstance(e, ValueError):
            raise LibgenSearchError(f"Invalid query for old API: {e}", query=query)


    logger.info("Falling back to new Libgen client for query: '%s'", query)
    try:
        # new_search_async (from new.client) returns List[BookData]
        # It does not use search_type directly.
        results = await new_search_async(query, proxies=proxies)
        if results:
            logger.info("New Libgen client found %d results for query: '%s'", len(results), query)
            return results

        # New API found no results
        logger.info("New Libgen client found no results for query: '%s'", query)
        if last_error_old_api:
            # Old API failed, New API found nothing
            raise LibgenSearchError(
                f"Old API search failed ({type(last_error_old_api).__name__}: {last_error_old_api}). "
                f"New API search found no results.",
                query=query
            )
        else:
            # Old API found nothing, New API found nothing
            return [] # Consistent with finding no results

    except LibgenError as e2: # Catch specific Libgen errors from new_search_async
        logger.warning("New Libgen search failed for query '%s': %s", query, e2)
        if last_error_old_api:
            raise LibgenSearchError(
                f"Old API search failed ({type(last_error_old_api).__name__}: {last_error_old_api}). "
                f"New API search also failed ({type(e2).__name__}: {e2}).",
                query=query
            )
        else: # Old API found nothing, New API failed
            raise LibgenSearchError(
                f"Old API found no results. New API search failed ({type(e2).__name__}: {e2}).",
                query=query
            )
    except Exception as e2: # Catch other unexpected errors
        logger.error("New Libgen search failed unexpectedly for query '%s': %s", query, e2, exc_info=True)
        if last_error_old_api:
            raise LibgenSearchError(
                f"Old API search failed ({type(last_error_old_api).__name__}: {last_error_old_api}). "
                f"New API search also failed unexpectedly ({type(e2).__name__}: {e2}).",
                query=query
            )
        else: # Old API found nothing, New API failed unexpectedly
            raise LibgenSearchError(
                f"Old API found no results. New API search failed unexpectedly ({type(e2).__name__}: {e2}).",
                query=query
            )

def search_unified_sync(
        query: str,
        search_type: SearchType = SearchType.DEFAULT,
        proxies: ProxyList | None = None
) -> List[BookData]:
    """
    Synchronously searches for books using the Libgen API, prioritizing the old API,
    and falling back to the new API if the old API fails.
    (Implementation similar to async, using sync calls and logging)
    """
    last_error_old_api: Exception | None = None
    try:
        logger.info("Attempting search with old Libgen client (sync) for query: '%s'", query)
        results = OldLibgenSearch.search_sync(query, search_type)
        if results:
            logger.info("Old Libgen client (sync) found %d results for query: '%s'", len(results), query)
            return results
        logger.info("Old Libgen client (sync) returned no results for query: '%s'.", query)
    except LibgenError as e:
        logger.warning("Old Libgen search (sync) failed for query '%s': %s", query, e)
        last_error_old_api = e
    except Exception as e:
        logger.warning("Old Libgen search (sync) failed unexpectedly for query '%s': %s", query, e, exc_info=True)
        last_error_old_api = e
        if isinstance(e, ValueError):
            raise LibgenSearchError(f"Invalid query for old API (sync): {e}", query=query)

    logger.info("Falling back to new Libgen client (sync) for query: '%s'", query)
    try:
        results = new_search_sync(query, proxies=proxies)
        if results:
            logger.info("New Libgen client (sync) found %d results for query: '%s'", len(results), query)
            return results

        logger.info("New Libgen client (sync) found no results for query: '%s'", query)
        if last_error_old_api:
            raise LibgenSearchError(
                f"Old API search (sync) failed ({type(last_error_old_api).__name__}: {last_error_old_api}). "
                f"New API search (sync) found no results.",
                query=query
            )
        else:
            return []

    except LibgenError as e2:
        logger.warning("New Libgen search (sync) failed for query '%s': %s", query, e2)
        if last_error_old_api:
            raise LibgenSearchError(
                f"Old API search (sync) failed ({type(last_error_old_api).__name__}: {last_error_old_api}). "
                f"New API search (sync) also failed ({type(e2).__name__}: {e2}).",
                query=query
            )
        else:
            raise LibgenSearchError(
                f"Old API (sync) found no results. New API search (sync) failed ({type(e2).__name__}: {e2}).",
                query=query
            )
    except Exception as e2:
        logger.error("New Libgen search (sync) failed unexpectedly for query '%s': %s", query, e2, exc_info=True)
        if last_error_old_api:
            raise LibgenSearchError(
                f"Old API search (sync) failed ({type(last_error_old_api).__name__}: {last_error_old_api}). "
                f"New API search (sync) also failed unexpectedly ({type(e2).__name__}: {e2}).",
                query=query
            )
        else:
            raise LibgenSearchError(
                f"Old API (sync) found no results. New API search (sync) failed unexpectedly ({type(e2).__name__}: {e2}).",
                query=query
            )


async def search_filtered_async(
    query: str,
    filters: Dict[str, str],
    search_type: SearchType = SearchType.DEFAULT,
    exact_match: bool = False, # Defaulted to False
) -> List[BookData]:
    """
    Asynchronously searches for books using the old Libgen API with filters.
    The new API does not implement this filtering, so no fallback is provided.

    Args:
        query: The search query.
        filters: A dictionary of filters to apply.
        search_type: The type of search.
        exact_match: Whether to perform an exact match on filters.

    Returns:
        A list of BookData objects.

    Raises:
        LibgenSearchError: If the old API search fails or the query is invalid.
    """
    try:
        logger.info("Attempting filtered search (async) with old Libgen client for query: '%s', filters: %s", query, filters)
        results = await OldLibgenSearch.search_filtered(query, filters, search_type, exact_match)
        logger.info("Old Libgen client (filtered async) found %d results for query: '%s'", len(results), query)
        return results
    except ValueError as e: # Handles query too short from OldLibgenSearch
        logger.warning("Invalid input for filtered search (async, query: '%s'): %s", query, e)
        raise LibgenSearchError(f"Invalid input for filtered search (async): {e}", query=query)
    except Exception as e:
        logger.error("Old Libgen filtered search (async) failed for query '%s': %s", query, e, exc_info=True)
        raise LibgenSearchError(
            f"Old Libgen filtered search (async) failed: {e}. The new Libgen client does not support filtering.",
            query=query
        )

def search_filtered_sync(
    query: str,
    filters: Dict[str, str],
    search_type: SearchType = SearchType.DEFAULT,
    exact_match: bool = False,
) -> List[BookData]:
    """
    Synchronously searches for books using the old Libgen API with filters.
    The new API does not implement this filtering, so no fallback is provided.

    Args:
        query: The search query.
        filters: A dictionary of filters to apply.
        search_type: The type of search.
        exact_match: Whether to perform an exact match on filters.

    Returns:
        A list of BookData objects.

    Raises:
        LibgenSearchError: If the old API search fails or the query is invalid.
    """
    try:
        logger.info("Attempting filtered search (sync) with old Libgen client for query: '%s', filters: %s", query, filters)
        results = OldLibgenSearch.search_filtered_sync(query, filters, search_type, exact_match)
        logger.info("Old Libgen client (filtered sync) found %d results for query: '%s'", len(results), query)
        return results
    except ValueError as e: # Handles query too short from OldLibgenSearch
        logger.warning("Invalid input for filtered search (sync, query: '%s'): %s", query, e)
        raise LibgenSearchError(f"Invalid input for filtered search (sync): {e}", query=query)
    except Exception as e:
        logger.error("Old Libgen filtered search (sync) failed for query '%s': %s", query, e, exc_info=True)
        raise LibgenSearchError(
            f"Old Libgen filtered search (sync) failed: {e}. The new Libgen client does not support filtering.",
            query=query
        )
