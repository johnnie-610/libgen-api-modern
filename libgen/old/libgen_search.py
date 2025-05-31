# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/old/libgen_search.py
#
# This file is part of the libgen-api-modern library

from libgen.old.search_request import SearchRequest, SearchType
from libgen.models import BookData
from typing import List, Dict, Optional, Union, Tuple, Any


class LibgenSearch:
    @staticmethod
    async def search(
        query: str, search_type: SearchType = SearchType.DEFAULT
    ) -> list[BookData]:
        """
        Asynchronously searches for books based on the given query.

        Args:
            query (str): The search query.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                - Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
            list[BookData]: A list of dictionaries representing the search results.

        Examples:

            ```python
            await LibgenSearch.search("python")
            ```

        """
        try:
            async with SearchRequest(query, search_type=search_type) as search_request:
                return await search_request.search()
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search: {e}")

    @staticmethod
    def search_sync(
        query: str, search_type: SearchType = SearchType.DEFAULT
    ) -> list[BookData]:
        """
        Synchronously searches for books based on the given query.

        Args:
            query (str): The search query.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
            list[BookData]: A list of dictionaries representing the search results.

        Examples:

            ```python
            LibgenSearch.search_sync("python")
            ```

        """
        try:
            with SearchRequest(query, search_type=search_type) as search_request:
                return search_request.search_sync()
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search: {e}")

    @staticmethod
    async def search_filtered(
        query: str,
        filters: dict[str, str],
        search_type: SearchType = SearchType.DEFAULT,
        exact_match: bool = False,
    ) -> list[BookData]:
        """
        Asynchronously searches for books based on the given query and applies filters.

        Args:
            query (str): The search query.
            filters (Dict[str, str]): Filters to apply to the search results.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.
            exact_match (bool, optional): If True, only include results that exactly match
                the filters. If False, include results that partially match the filters.
                Defaults to False.


        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
            list[BookData]: A list of dictionaries representing the filtered search results.

        Examples:

            ```python
            filters = {"year": "2020"}
            await LibgenSearch.search_filtered("python", filters, exact_match=True)
            ```
        """
        try:
            async with SearchRequest(query, search_type=search_type) as search_request:
                results: list[BookData] = await search_request.search()

                filtered_results: list[BookData] = await LibgenSearch.__filter_results(
                    results=results, filters=filters, exact_match=exact_match
                )
                return filtered_results
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search or filtering: {e}")

    @staticmethod
    def search_filtered_sync(
        query: str,
        filters: dict[str, str],
        search_type: SearchType = SearchType.DEFAULT,
        exact_match: bool = False,
    ) -> list[BookData]:
        """
        Synchronously searches for books based on the given query and applies filters.

        Args:
            query (str): The search query.
            filters (Dict[str, str]): Filters to apply to the search results.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.
            exact_match (bool, optional): If True, only include results that exactly match
                the filters. If False, include results that partially match the filters.
                Defaults to False.


        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
            list[BookData]: A list of dictionaries representing the filtered search results.

        Examples:

            ```python
            filters = {"year": "2020"}
            LibgenSearch.search_filtered_sync("python", filters, exact_match=True)
            ```
        """
        try:
            with SearchRequest(query, search_type=search_type) as search_request:
                results: list[BookData] = search_request.search_sync()

                filtered_results: list[BookData] = LibgenSearch.__filter_results_sync(
                    results=results, filters=filters, exact_match=exact_match
                )
                return filtered_results
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search or filtering: {e}")

    @classmethod
    async def __filter_results(
        cls, results: list[BookData], filters: dict[str, str], exact_match: bool = False
    ) -> list[BookData]:
        """
        Asynchronously filter search results based on the given filters.
        """

        def match(item: str | None, filter_value: str) -> bool:
            if item is None:
                return False
            if exact_match:
                return item.lower() == filter_value.lower()
            return filter_value.lower() in item.lower()

        filtered_results = []

        for result in results:
            match_all_filters = True
            for key, value in filters.items():
                # Get the attribute value using getattr
                item_value = getattr(result, key, None)

                # Handle tuple of authors specially
                if key == "authors" and isinstance(item_value, tuple):
                    # Check if any author matches the filter
                    author_match = any(match(author, value) for author in item_value)
                    if not author_match:
                        match_all_filters = False
                        break
                    continue

                # For all other attributes
                if not match(
                    str(item_value) if item_value is not None else None, value
                ):
                    match_all_filters = False
                    break

            if match_all_filters:
                filtered_results.append(result)
        return filtered_results

    @classmethod
    def __filter_results_sync(
        cls, results: list[BookData], filters: dict[str, str], exact_match: bool = False
    ) -> list[BookData]:
        """
        Synchronously filter search results based on the given filters.
        """

        def match(item: str | None, filter_value: str) -> bool:
            if item is None:
                return False
            if exact_match:
                return item.lower() == filter_value.lower()
            return filter_value.lower() in item.lower()

        filtered_results = []

        for result in results:
            match_all_filters = True
            for key, value in filters.items():
                # Get the attribute value using getattr
                item_value = getattr(result, key, None)

                # Handle tuple of authors specially
                if key == "authors" and isinstance(item_value, tuple):
                    # Check if any author matches the filter
                    author_match = any(match(author, value) for author in item_value)
                    if not author_match:
                        match_all_filters = False
                        break
                    continue

                # For all other attributes
                if not match(
                    str(item_value) if item_value is not None else None, value
                ):
                    match_all_filters = False
                    break

            if match_all_filters:
                filtered_results.append(result)
        return filtered_results
