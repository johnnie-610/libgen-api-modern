# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

# import asyncio
from typing import List, Dict
from libgen_api_modern.search_request import SearchRequest, SearchType


class LibgenSearch:
    @staticmethod
    async def search(query: str, search_type: str = SearchType.DEFAULT) -> List[Dict[str, str]]:
        """
        Searches for books based on the given query.

        Args:
            query (str): The search query.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.
                -Use http proxy only with no authentication.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the search results.

        Examples:

            ```python
            await LibgenSearch.search("python")
            ```

        """
        try:
            search_request = SearchRequest(query, search_type=search_type)

            return await search_request.search()
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search: {e}")

    @staticmethod
    async def search_filtered(
        query: str,
        filters: Dict[str, str],
        search_type: str = SearchType.DEFAULT,
        exact_match: bool = False,
    ) -> List[Dict[str, str]]:
        """
        Searches for books based on the given query and applies filters.

        Args:
            query (str): The search query.
            filters (Dict[str, str]): Filters to apply to the search results.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.
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
            filters = {"year": "2020"}
            await LibgenSearch.search_filtered("python", filters, exact_match=True)
            ```
        """
        try:
            search_request = SearchRequest(query, search_type=search_type)

            results: List[Dict[str, str]] = await search_request.search()

            filtered_results: List[Dict[str, str]] = await LibgenSearch.__filter_results(
                results=results, filters=filters, exact_match=exact_match
            )
            return filtered_results
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search or filtering: {e}")


    #FIXME: FILTER USING THE BOOKDATA MODEL
    @classmethod
    async def __filter_results(
        cls,
        results: List[Dict[str, str]],
        filters: Dict[str, str],
        exact_match: bool = False
    ) -> List[Dict[str, str]]:
        def match(item: str, filter_value: str) -> bool:
            if exact_match:
                return item == filter_value
            else:
                return filter_value.lower() in item.lower()

        filtered_results = []
        for result in results:
            match_all_filters = True
            for key, value in filters.items():
                if key in result:
                    if not match(result[key], value):
                        match_all_filters = False
                        break
                else:
                    match_all_filters = False
                    break

            if match_all_filters:
                filtered_results.append(result)

        return filtered_results