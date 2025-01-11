# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

<<<<<<< HEAD
# import asyncio
from typing import List, Dict
from libgen_api_modern.search_request import SearchRequest
=======
from libgen_api_modern.search_request import SearchRequest, SearchType
from libgen_api_modern.models import BookData
>>>>>>> origin/main


class LibgenSearch:
    @staticmethod
<<<<<<< HEAD
    async def search_scientific_articles(
        query: str,
        proxy: str | None = None
    ) -> List[Dict[str, str]]:
        """
        Searches for scientific articles based on the given query.

        Args:
            query (str): The search query.
            proxy (str, optional): The proxy to use for the search. Defaults to None.
                -Use http proxy only with no authentication.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the search results.

        Examples:
            
            ```python
            from libgen_api_modern import LibgenSearch
            await LibgenSearch.search_scientific_articles("python")
            ```

        """
        try:
            search_request = SearchRequest(query)
            
            return await search_request.aggregate_scimag_data(proxy=proxy)
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"An error occurred during the search: {e}")
    
    async def search_scientific_articles_filtered(
        self,
        query: str,
        filters: Dict[str, str],
        exact_match: bool = False,
        proxy: str | None = None
    ) -> List[Dict[str, str]]:
        """
        Searches for scientific articles based on the given query and applies filters.

        Args:
            query (str): The search query.
            filters (Dict[str, str]): Filters to apply to the search results.
            exact_match (bool, optional): If True, only include results that exactly match
                the filters. If False, include results that partially match the filters. Defaults to False.
            proxy (str, optional): The proxy to use for the search. Defaults to None.
                -Use http proxy only with no authentication.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the filtered search results.

        Examples:
            
            ```python
            from libgen_api_modern import LibgenSearch
            filters = {"year": "2020"}
            await LibgenSearch.search_scientific_articles_filtered("python", filters, exact_match=True)
            ```

        """
        try:
            search_request = SearchRequest(query)
            
            results = await search_request.aggregate_scimag_data(proxy=proxy)
            return await LibgenSearch.__filter_results(results, filters, exact_match)
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"An error occurred during the search: {e}")

    @staticmethod
    async def search_fiction(query: str, proxy: str | None = None) -> List[Dict[str, str]]:
        """
        Searches for fiction books based on the given query.

        Args:
            query (str): The search query.
            proxy (str, optional): The proxy to use for the search. Defaults to None.
                -Use http proxy only with no authentication.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the search results.

        Examples:

            ```python
            from libgen_api_modern import LibgenSearch
            await LibgenSearch.search_fiction("python")
            ```

        """
        try:
            search_request = SearchRequest(query)
            
            return await search_request.aggregate_fiction_data(proxy=proxy)
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"An error occurred during the search: {e}")
    
    async def search_fiction_filtered(
        self,
        query: str,
        filters: Dict[str, str],
        exact_match: bool = False,
        proxy: str | None = None
    ) -> List[Dict[str, str]]:
        """
        Searches for fiction books based on the given query and applies filters.

        Args:
            query (str): The search query.
            filters (Dict[str, str]): Filters to apply to the search results.
            exact_match (bool, optional): If True, only include results that exactly match
                the filters. If False, include results that partially match the filters.
                Defaults to True.
            proxy (str, optional): The proxy to use for the search. Defaults to None.
                -Use http proxy only with no authentication.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the filtered search results.

        Examples:

            ```python
            from libgen_api_modern import LibgenSearch
            filters = {"year": "2020"}
            await LibgenSearch.search_fiction_filtered("python", filters, exact_match=True)
            ```
        """
        try:
            search_request = SearchRequest(query)

            results = await search_request.aggregate_fiction_data(proxy=proxy)

            return await LibgenSearch.__filter_results(results, filters, exact_match)
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"An error occurred during the search: {e}")

    @staticmethod
    async def search(query: str, search_type: str = "def", proxy: str | None = None) -> List[Dict[str, str]]:
=======
    async def search(query: str, search_type: str = SearchType.DEFAULT) -> list[BookData]:
>>>>>>> origin/main
        """
        Searches for books based on the given query.

        Args:
            query (str): The search query.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.
            proxy (str, optional): The proxy to use for the search. Defaults to None.
                -Use http proxy only with no authentication.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
<<<<<<< HEAD
            List[Dict[str, str]]: A list of dictionaries representing the search results.
=======
            list[BookData]: A list of dictionaries representing the search results.
>>>>>>> origin/main

        Examples:

            ```python
<<<<<<< HEAD
            from libgen_api_modern import LibgenSearch
=======
>>>>>>> origin/main
            await LibgenSearch.search("python")
            ```

        """
        try:
            search_request = SearchRequest(query, search_type=search_type)
<<<<<<< HEAD
            
            return await search_request.aggregate_request_data(proxy=proxy)
=======

            return await search_request.search()
>>>>>>> origin/main
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search: {e}")

    @staticmethod
    async def search_filtered(
        query: str,
<<<<<<< HEAD
        filters: Dict[str, str],
        search_type: str = "def",
        exact_match: bool = False,
        proxy: str | None = None
    ) -> List[Dict[str, str]]:
=======
        filters: dict[str, str],
        search_type: str = SearchType.DEFAULT,
        exact_match: bool = False,
    ) -> list[BookData]:
>>>>>>> origin/main
        """
        Searches for books based on the given query and applies filters.

        Args:
            query (str): The search query.
            filters (Dict[str, str]): Filters to apply to the search results.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.
            exact_match (bool, optional): If True, only include results that exactly match
                the filters. If False, include results that partially match the filters.
<<<<<<< HEAD
                Defaults to True.
            proxy (str, optional): The proxy to use for the search. Defaults to None.
                -Use http proxy only with no authentication.
=======
                Defaults to False.
>>>>>>> origin/main


        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
<<<<<<< HEAD
            List[Dict[str, str]]: A list of dictionaries representing the filtered search results.
=======
            list[BookData]: A list of dictionaries representing the filtered search results.
>>>>>>> origin/main

        Examples:

            ```python
            filters = {"year": "2020"}
            await LibgenSearch.search_filtered("python", filters, exact_match=True)
            ```
        """
        try:
            search_request = SearchRequest(query, search_type=search_type)

<<<<<<< HEAD
            results: List[Dict[str, str]] = await search_request.aggregate_request_data(proxy=proxy)

            filtered_results: List[Dict[str, str]] = await LibgenSearch.__filter_results(
=======
            results: list[dict[str, str]] = await search_request.search()

            filtered_results: list[dict[str, str]] = await LibgenSearch.__filter_results(
>>>>>>> origin/main
                results=results, filters=filters, exact_match=exact_match
            )
            return filtered_results
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search or filtering: {e}")

<<<<<<< HEAD
    
=======

>>>>>>> origin/main
    @classmethod
    async def __filter_results(
        cls,
        results: list[BookData],
        filters: dict[str, str],
        exact_match: bool = False
    ) -> list[BookData]:
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
                if key == 'authors' and isinstance(item_value, tuple):
                    # Check if any author matches the filter
                    author_match = any(match(author, value) for author in item_value)
                    if not author_match:
                        match_all_filters = False
                        break
                    continue

                # For all other attributes
                if not match(str(item_value) if item_value is not None else None, value):
                    match_all_filters = False
                    break

            if match_all_filters:
                filtered_results.append(result)
<<<<<<< HEAD
        
=======

>>>>>>> origin/main
        return filtered_results