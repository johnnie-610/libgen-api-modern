# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

from typing import Optional

class LibgenError(Exception):
    """Base exception class for all library errors."""
    def __init__(self, message: str, *args):
        self.message = message
        super().__init__(message, *args)

class LibgenNetworkError(LibgenError):
    """Exception for network-related errors."""
    def __init__(self, message: str, status_code: Optional[int] = None, url: Optional[str] = None):
        self.status_code = status_code
        self.url = url
        full_message = f"{message}"
        if status_code:
            full_message += f" (Status code: {status_code})"
        if url:
            full_message += f", URL: {url}"
        super().__init__(full_message)

class LibgenSearchError(LibgenError):
    """Exception for failed search operations."""
    def __init__(self, message: str, query: Optional[str] = None):
        self.query = query
        full_message = f"{message}"
        if query:
            full_message += f" (Query: '{query}')"
        super().__init__(full_message)

class LibgenParseError(LibgenError):
    """Exception for failures in parsing HTML content."""
    pass