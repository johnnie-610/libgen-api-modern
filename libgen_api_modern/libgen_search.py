# Copyright (c) 2024 Johnnie
# 
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
# 
# This file is part of the libgen-api-modern library


from typing import List, Dict
from .search_request import SearchRequest


class LibgenSearch:

    def search(self, query: str, search_type: str = "def") -> List[Dict[str, str]]:
        """
        Searches for books based on the given query.

        Args:
            query (str): The search query.
            search_type (str, optional): The type of search to perform. Defaults to "def".
                -Options are: 'def', 'author(s)', 'title', 'series', 'publisher', 'year', 'language', 'isbn', 'md5.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the search results.
        """
        try:
            # Create a SearchRequest object with the given query and search type
            search_request = SearchRequest(query, search_type=search_type)
            
            # Aggregate the request data and return the result
            return search_request.aggregate_request_data()
        except ValueError as e:
            # If the query is too short, raise a ValueError
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            # If any other error occurs, raise an Exception
            raise Exception(f"Error during search: {e}")
    
    def search_filtered(
        self,
        query: str,
        filters: Dict[str, str],
        search_type: str = "def",
        exact_match: bool = True
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

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the filtered search results.
        """
        try:
            # Create a SearchRequest object with the given query and search type
            search_request = SearchRequest(query, search_type=search_type)

            # Aggregate the request data
            results: List[Dict[str, str]] = search_request.aggregate_request_data()

            # Apply filters to the results and return the filtered results
            filtered_results: List[Dict[str, str]] = filter_results(
                results=results, filters=filters, exact_match=exact_match
            )
            return filtered_results
        except ValueError as e:
            # If the query is too short, raise a ValueError
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            # If any other error occurs, raise an Exception
            raise Exception(f"Error during search or filtering: {e}")

    def search_title(self, query: str) -> List[Dict[str, str]]:
        """
        Searches for books by title.

        Args:
            query (str): The title search query.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the search results.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.
        """
        try:
            search_request = SearchRequest(query, search_type="title")
            results: List[Dict[str, str]] = search_request.aggregate_request_data()
            return results
        except ValueError as e:
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            raise Exception(f"Error during search: {e}")

    def search_author(
        self,
        query: str,
    ) -> List[Dict[str, str]]:
        """
        Searches for books by author and returns the search results.

        Args:
            query (str): The author search query.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the search results.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search.
        """
        try:
            # Create a SearchRequest object with the given query and search type
            search_request = SearchRequest(query, search_type="author")

            # Aggregate the request data and return the result
            return search_request.aggregate_request_data()
        except ValueError as e:
            # If the query is too short, raise a ValueError
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            # If any other error occurs, raise an Exception
            raise Exception(f"Error during search: {e}")

    def search_title_filtered(
        self,
        query: str,
        filters: Dict[str, str],
        exact_match: bool = True
    ) -> List[Dict[str, str]]:
        """
        Searches for books by title and filters the results based on the given filters.

        Args:
            query (str): The title to search for.
            filters (Dict[str, str]): The filters to apply to the search results.
            exact_match (bool, optional): If True, only include results that exactly match
                the filters. If False, include results that partially match the filters.
                Defaults to True.

        Raises:
            ValueError: If the query is shorter than 3 characters.
            Exception: If an error occurs during the search or filtering.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the filtered search results.
        """
        try:
            # Create a SearchRequest object with the given query and search type
            search_request = SearchRequest(query, search_type="title")

            # Aggregate the request data
            results: List[Dict[str, str]] = search_request.aggregate_request_data()

            # Apply filters to the results and return the filtered results
            filtered_results: List[Dict[str, str]] = filter_results(
                results=results, filters=filters, exact_match=exact_match
            )
            return filtered_results
        except ValueError as e:
            # If the query is too short, raise a ValueError
            raise ValueError(f"Search query is too short: {e}")
        except Exception as e:
            # If any other error occurs, raise an Exception
            raise Exception(f"Error during search or filtering: {e}")

    def search_author_filtered(
        self,
        query: str,
        filters: Dict[str, str],
        exact_match: bool = True
    ) -> List[Dict[str, str]]:
        """
        Searches for books by author and filters the results based on the given filters.

        Args:
            query (str): The author search query.
            filters (Dict[str, str]): The filters to apply to the search results.
            exact_match (bool, optional): Whether to perform exact matching. Defaults to True.

        Returns:
            List[Dict[str, str]]: A list of dictionaries representing the filtered search results.

        Raises:
            Exception: If an error occurs during the search or filtering.
        """
        try:
            # Create a SearchRequest object with the given query and search type
            search_request: SearchRequest = SearchRequest(query, search_type="author")
            
            # Aggregate the request data
            results: List[Dict[str, str]] = search_request.aggregate_request_data()
            
            # Apply filters to the results and return the filtered results
            filtered_results: List[Dict[str, str]] = filter_results(
                results=results, filters=filters, exact_match=exact_match
            )
            return filtered_results
        except Exception as e:
            # If an error occurs, log the error and return an empty list
            print(f"An error occurred while searching and filtering authors: {e}")
            return []



def filter_results(
        results: List[Dict[str, str]],
        filters: Dict[str, str],
        exact_match: bool = True
) -> List[Dict[str, str]]:
    """
    Returns a list of results that match the given filter criteria.

    Args:
        results (List[Dict[str, str]]): List of dictionaries containing search results.
        filters (Dict[str, str]): Filters to apply to the search results.
        exact_match (bool, optional): If True, only include results that exactly match
            the filters. If False, include results that partially match the filters.
            Defaults to True.

    Returns:
        List[Dict[str, str]]: List of dictionaries containing filtered search results.

    Note:
        When exact-match = False,
        we run a case-insensitive check between each filter field and each result.

        exact_match defaults to True -
        this is to maintain consistency with older versions of this library.

    Raises:
        ValueError: If the given filters are empty or if the query is too short.
        KeyError: If a filter field is not present in the results.
    """

    if not filters:
        raise ValueError("No filters provided")

    filtered_list: List[Dict[str, str]] = []

    try:
        # If exact_match = True, only include results that exactly match the filters
        if exact_match:
            for result in results:
                # Check whether a candidate result matches the given filters
                if filters.items() <= result.items():
                    filtered_list.append(result)

        # If exact_match = False, include results that partially match the filters
        else:
            for result in results:
                filter_matches_result = True  # Initialize flag to True
                for field, query in filters.items():
                    # Check whether each filter field partially matches the result
                    if query.casefold() not in result[field].casefold():
                        filter_matches_result = False
                        break
                if filter_matches_result:
                    filtered_list.append(result)

    except KeyError as e:
        # If a filter field is not present in the results, raise a KeyError
        raise KeyError(f"Filter field not present in results: {e}")

    return filtered_list

