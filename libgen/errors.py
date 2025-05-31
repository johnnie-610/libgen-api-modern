# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/errors.py
#
# This file is part of the libgen-api-modern library

from typing import Optional


class LibgenError(Exception):
    """Base exception class for all libgen-api-modern errors."""
    
    def __init__(self, message: str, *args):
        self.message = message
        super().__init__(message, *args)


class LibgenNetworkError(LibgenError):
    """Exception raised for network-related errors."""
    
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        self.status_code = status_code
        self.url = url
        super_message = message
        if status_code:
            super_message = f"{message} (Status code: {status_code})"
        if url:
            super_message = f"{super_message}, URL: {url}"
        super().__init__(super_message)


class LibgenSearchError(LibgenError):
    """Exception raised when a search operation fails."""
    
    def __init__(self, message: str, query: Optional[str] = None):
        self.query = query
        super_message = message
        if query:
            super_message = f"{message} (Query: {query})"
        super().__init__(super_message)


class LibgenParseError(LibgenError):
    """Exception raised when parsing HTML content fails."""
    
    def __init__(self, message: str, content_snippet: Optional[str] = None):
        self.content_snippet = content_snippet
        super_message = message
        if content_snippet and len(content_snippet) > 100:
            content_snippet = content_snippet[:97] + "..."
        if content_snippet:
            super_message = f"{message} (Content: {content_snippet})"
        super().__init__(super_message)


class LibgenResourceError(LibgenError):
    """Exception raised when a resource (book, article, etc.) cannot be accessed."""
    
    def __init__(self, message: str, resource_id: Optional[str] = None):
        self.resource_id = resource_id
        super_message = message
        if resource_id:
            super_message = f"{message} (Resource ID: {resource_id})"
        super().__init__(super_message)


class LibgenConfigError(LibgenError):
    """Exception raised for configuration errors."""
    
    def __init__(self, message: str, param_name: Optional[str] = None):
        self.param_name = param_name
        super_message = message
        if param_name:
            super_message = f"{message} (Parameter: {param_name})"
        super().__init__(super_message)