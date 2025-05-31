# Libgen-API-Modern

Libgen-API-Modern is a lightweight, asynchronous Python library and command-line tool designed to search for, parse, and
download books from Library Genesis (Libgen) and its alternative domains. It is built for efficiency and minimal
dependencies while providing a modern, user-friendly interface using the [Rich](https://github.com/Textualize/rich)
library for enhanced terminal output.

The library intelligently attempts to use an older, more structured Libgen interface first, and falls back to newer,
more common Libgen interfaces if needed, ensuring higher chances of success.

---

## Features

- **Asynchronous Operations:**
  Uses [aiohttp](https://github.com/aio-libs/aiohttp) for non-blocking HTTP requests.
- **Fallback Mechanism:** Prioritizes more structured Libgen sources, falling back to common mirrors.
- **Multiple Domain & Proxy Support:**
  Automatically rotates through multiple Libgen domains (for the "new" client part) and supports proxy integration.
- **Advanced HTML Parsing & Link Resolution:**
  Custom HTML parsers extract book details, cover images, and attempts to resolve direct download links.
- **Consistent Data Model:** Returns search results as `BookData` objects for predictable data handling.
- **Rich Terminal Output:**
  Displays search results in a well-formatted, colored table using [Rich](https://github.com/Textualize/rich) in the
  CLI.
- **Versatile CLI with Built-in Help & Manual:**
    - **Search Mode:** Search for books by query.
    - **Download Mode:** Download a file from a given mirror URL, with a progress bar.
    - **Interactive Mode:** A REPL loop to repeatedly search and download books.
    - Custom help commands (`libgen help [command]`) and a full manual (`libgen manual` or `man libgen`).
    - Running `libgen` with no arguments defaults to interactive mode.

---

## Installation

```bash
pip install libgen-api-modern
```

## Usage

The project can be used both as a library for programmatic integration and as a command-line tool.

### As a Library

Import the library into your Python programs. The primary functions are `search_async` and `search_sync` from the
top-level libgen package. These functions return a list of `BookData` objects.

#### BookData Object Attributes

- `id: str` - The Libgen ID of the book.
- `authors: tuple[str, ...]` - A tuple of author names.
- `title: str` - The title of the book.
- `publisher: str | None` - The publisher.
- `year: str | None` - Publication year.
- `pages: str | None` - Number of pages.
- `language: str | None` - Language of the book.
- `size: str | None` - File size (e.g., "10 MB").
- `extension: str | None` - File extension (e.g., "pdf").
- `isbn: str | None` - ISBN, if available.
- `cover_url: str | None` - URL of the book's cover image.
- `download_links: DownloadLinks | None` - An object containing various download links:
    - `get_link: str | None` - A direct GET download link, often the most reliable.
    - `cloudflare_link: str | None`
    - `ipfs_link: str | None`
    - `pinata_link: str | None`
    - `cover_link: str | None` (Note: `BookData.cover_url` is usually preferred for the main cover)

#### Example

```python
import asyncio
from libgen_api_modern import search_async, LibgenError, BookData


async def main():
    try:
        # Perform a search query for "the art of war"
        results: list[BookData] = await search_async("the art of war")
        if not results:
            print("No results found.")
            return

        for book in results:
            print(f"Title: {book.title}")
            print(f"Authors: {', '.join(book.authors) if book.authors else 'N/A'}")
            print(f"Year: {book.year or 'N/A'}")
            print(f"Extension: {book.extension or 'N/A'}")
            if book.cover_url:
                print(f"Cover: {book.cover_url}")

            direct_download_link = None
            if book.download_links and book.download_links.get_link:
                direct_download_link = book.download_links.get_link

            if direct_download_link:
                print(f"Direct Download: {direct_download_link}")
            else:
                print("No direct download link found through primary resolution.")
            print("-" * 40)

    except LibgenError as e:
        print(f"Libgen search error: {e}")


if __name__ == "__main__":
    asyncio.run(main())
```

#### Example Output (Conceptual for one book)

```
Title: The Art of War
Authors: Sun Tzu
Year: 5th century BC
Extension: pdf
Cover: https://..pic.jpg
Direct Download: https://...b3488&key=SOMEKEY
----------------------------------------
```

You can also use filtered search (currently relies on the "old" API):

```python
from libgen_api_modern import search_filtered_async


async def filtered_search_example():
    filters = {"year": "2020", "extension": "pdf"}
    results = await search_filtered_async("python programming", filters=filters, exact_match=False)
    # ... process results ...
```

### As a Command-Line Tool

The CLI provides multiple usage modes:

#### Interactive Mode

Running `libgen` without any arguments starts interactive mode.

```bash
libgen
```

In interactive mode:

- Enter search queries repeatedly.
- Results are displayed in a rich-formatted table.
- Choose a book by number to download.
- Type `exit` or `quit` to leave.

#### Search Mode

Perform a one-off search from the CLI. Results are displayed, and you'll be prompted if you want to download one.

```bash
libgen search "the art of war" --proxy http://yourproxy:port
```

#### Download Mode

Download a file directly from a known Libgen mirror URL:

```bash
libgen download "MIRROR_URL" --output "mybook.pdf"
```

Example:

```bash
libgen download "https://...y=SOMEKEY" --output "art_of_war.pdf"
```

This downloads the file with a progress bar. If the output file exists, you will be prompted.

#### Help and Manual

Get a brief overview of available commands:

```bash
libgen help
```

For detailed help on a specific command:

```bash
libgen help search
libgen help download
libgen help interactive
```

To view the complete manual with detailed instructions and examples:

```bash
libgen manual
# or (if symlinked appropriately)
# man libgen
```

## Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request on
[GitHub](https://github.com/Johnnie610/libgen-api-modern).

## License

This project is licensed under the [MIT License](https://mit-license.org/).

Enjoy using Libgen-API-Modern to explore, search, and download your favourite books!