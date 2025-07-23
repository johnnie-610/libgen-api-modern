# Libgen API Modern

Libgen-API-Modern is a lightweight, simple, and blazingly fast Python library for interacting with Library Genesis. It provides both synchronous and asynchronous methods to search for and resolve download links for books, all with a modern and elegant interface.

This library focuses exclusively on the modern Libgen web interface, ensuring high performance and reliability without the need for fallbacks to older, less structured APIs.

## Features

- **Blazingly Fast:** Optimized for speed with efficient HTML parsing and direct API interaction.
- **Async & Sync:** Provides both `async` and `sync` functions to fit any project architecture.
- **Simple & Elegant API:** A clean and minimal set of functions (`search_async`, `search_sync`).
- **Direct Download Link Resolution:** Intelligently parses mirror pages to find the most direct and reliable download links.
- **Robust Data Models:** Search results are returned as `BookData` objects for consistent and predictable data handling.
- **Minimal Dependencies:** Built with `aiohttp`, `requests`, and `rich` to keep the library lightweight.
- **Versatile CLI:** A powerful command-line tool for searching, downloading, and interactive sessions.

## Installation

```bash
pip install libgen-api-modern
```

## Usage as a Library

The core functions are `search_async` and `search_sync`. Both return a list of `BookData` objects.

### Asynchronous Example

```python
import asyncio
from libgen import search_async, LibgenError

async def main():
    try:
        results = await search_async("the art of war")
        if not results:
            print("No results found.")
            return

        for book in results:
            print(f"Title: {book.title}")
            print(f"Authors: {', '.join(book.authors) if book.authors else 'N/A'}")
            if book.download_links and book.download_links.get_link:
                print(f"Direct Download: {book.download_links.get_link}")
            print("-" * 40)

    except LibgenError as e:
        print(f"An error occurred: {e}")

if __name__ == "__main__":
    asyncio.run(main())
```

### Synchronous Example

```python
from libgen import search_sync, LibgenError

try:
    results = search_sync("the art of war")
    if not results:
        print("No results found.")
    else:
        for book in results:
            print(f"Title: {book.title}")
            print(f"Authors: {', '.join(book.authors) if book.authors else 'N/A'}")
            if book.download_links and book.download_links.get_link:
                print(f"Direct Download: {book.download_links.get_link}")
            print("-" * 40)
except LibgenError as e:
    print(f"An error occurred: {e}")
```

## Usage as a Command-Line Tool

The CLI offers three main commands.

### Search

```bash
libgen search "the art of war"
```

### Download

Download a file directly from a known Libgen mirror URL.

```bash
libgen download "MIRROR_URL" --output "mybook.pdf"
```

### Interactive Mode

For repeated searches and downloads in a single session.

```bash
libgen interactive
```

## License

This project is licensed under the **MIT License**.