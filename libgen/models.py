# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/models.py
#
# This file is part of the libgen-api-modern library

from dataclasses import dataclass

@dataclass(frozen=True)
class DownloadLinks:
    get_link: str | None
    cloudflare_link: str | None
    ipfs_link: str | None
    pinata_link: str | None
    cover_link: str | None


@dataclass(frozen=True)
class BookData:
    id: str
    authors: tuple[str, ...]
    title: str
    publisher: str | None
    year: str | None
    pages: str | None
    language: str | None
    size: str | None
    extension: str | None
    isbn: str | None
    cover_url: str | None
    download_links: DownloadLinks | None
