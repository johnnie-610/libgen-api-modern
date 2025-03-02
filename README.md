# Libgen

Libgen is a lightweight, asynchronous Python library and command‑line tool designed to search for, parse, and download books from Library Genesis (Libgen) and its alternative domains. It is built for maximum efficiency and minimal dependencies while providing a modern, user‑friendly interface using the [Rich](https://github.com/Textualize/rich) library for enhanced terminal output.

---

## Features

- **Asynchronous Operations:**
  Uses [aiohttp](https://github.com/aio-libs/aiohttp) for non‑blocking HTTP requests to search Libgen websites and download files.
- **Multiple Domain & Proxy Support:**
  Automatically rotates through multiple Libgen domains and supports proxy integration.
- **Advanced HTML Parsing & Link Resolution:**

  - Custom HTML parser extracts book details, cover images, and mirror links.
- **Rich Terminal Output:**
  Displays search results in a well‑formatted, colored table using [Rich](https://github.com/Textualize/rich).
- **Versatile CLI with Built‑in Help & Manual:**

  - **Search Mode:** Search for books by query.
  - **Download Mode:** Download a file from a given mirror URL.
  - **Interactive Mode:** A REPL loop to repeatedly search and download books.
  - Custom help commands (`libgen help [command]`) and a full manual (`libgen manual` or `man libgen`) are available.
  - Running `libgen` with no arguments defaults to interactive mode.
- **Memory Safety:**
  Safely creates directories, checks for existing files, and prompts before overwriting files during downloads.

---

## Installation

```bash

pip install libgen-api-modern

```

---

## Usage

- The project can be used both as a library (for programmatic usage) and as a command‑line tool.

### As a Library:

- You can import the library into your Python programs. The main function is search from libgen.client, which returns a list of dictionaries. Each result dictionary has the following keys:

  - **title**: The title of the book.
  - **authors**: The authors of the book.
  - **publisher**: The publisher of the book.
  - **year**: The publication year of the book.
  - **language**: The language of the book.
  - **pages**: The number of pages in the book.
  - **size**: The size of the book in bytes.
  - **extension**: The file extension of the book.
  - **cover**: The URL of the book's cover image.
  - **mirror**: The URL of the book's mirror link.

#### Example:

```python

import asyncio
from libgen.client import search, LibgenError

async def main():
    try:
        # Perform a search query for "the art of war"
        results = await search("the art of war")
        for result in results:
            print(f"Title: {result['title']}")
            print(f"Authors: {result['authors']}")
            print(f"Cover: {result['cover']}")
            print(f"Download: {result['mirror']}")
            print("-" * 40)
    except LibgenError as e:
        print(f"Libgen search error: {e}")

asyncio.run(main())

```

#### Example Output:

```python

{
  "cover": "https://libgen.li/comicscovers/1173000/07fa8b415fc7e4b2aa4c9ef66f0b3488_small.jpg",
  "title": "The Art of War",
  "authors": "Sun Tzu",
  "publisher": "Unknown",
  "year": "5th century BC",
  "language": "English",
  "pages": "200",
  "size": "58 MB",
  "extension": "pdf",
  "mirror": "https://libgen.li/get.php?md5=07fa8b415fc7e4b2aa4c9ef66f0b3488"
}

```

### As a Command-Line Tool:

The CLI provides multiple usage modes:

#### Interactive Mode:

- Running libgen without any arguments starts interactive mode.

```bash

libgen

```

In interactive mode:

- You can enter search queries repeatedly.
- Results are displayed in a rich‑formatted table.
- You can choose a mirror URL to download the file.
- Type exit or quit to leave the mode.

#### Search Mode:

Perform a one‑off search from the CLI:

```bash

libgen search "the art of war" --proxy http://yourproxy:port

```

This displays the search results. You can then note a mirror URL and use the download command.

#### Download Mode:

Download a file from a mirror URL:

```bash

libgen download https://libgen.li/get.php?md5=07fa8b415fc7e4b2aa4c9ef66f0b3488 --output mybook.pdf

```

This downloads the file from the provided mirror URL. If the output file exists, you will be prompted before overwriting.

#### Help and Manual:

##### Short Help:

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

##### Full Manual:

To view the complete manual with detailed instructions and examples:

```bash

libgen manual
# or
man libgen

```

## Contributing

Contributions, bug reports, and feature requests are welcome! Feel free to open an issue or submit a pull request on [GitHub](https://github.com/johnnie-610/libgen-api-modern). We'll be happy to review and merge your contributions.

## License

This project is licensed under the [MIT License](https://opensource.org/licenses/MIT).

*Enjoy using the Libgen to explore, search, and download your favourite books!*
