import argparse
import asyncio
import aiohttp
import os
import sys

from libgen.client import search, LibgenError
from libgen.utils import pretty_print
from rich.table import Table
from rich.console import Console

console = Console()

# ------------------ DOWNLOAD FUNCTION WITH MEMORY SAFETY ------------------


async def download_file(url: str, output: str):
    """Download a file from the given URL and save it to disk safely inside the 'libgen' folder."""
    # Ensure the output directory "libgen" exists in the current working directory.
    download_dir = os.path.join(os.getcwd(), "libgen")
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
        except Exception as e:
            raise Exception(f"Could not create directory {download_dir}: {e}")

    # Ensure output file is inside the download_dir.
    if not os.path.isabs(output):
        output = os.path.join(download_dir, output)

    # If file exists, ask for confirmation.
    if os.path.exists(output):
        ans = (
            input(f"File '{output}' already exists. Overwrite? [y/N]: ").strip().lower()
        )
        if ans != "y":
            print("Download canceled.")
            return

    async with aiohttp.ClientSession() as session:
        async with session.get(url) as resp:
            if resp.status != 200:
                raise Exception(f"Download failed: HTTP {resp.status}")
            total = 0
            with open(output, "wb") as f:
                while True:
                    chunk = await resp.content.read(1024)
                    if not chunk:
                        break
                    f.write(chunk)
                    total += len(chunk)
            print(f"Downloaded {total} bytes; saved as '{output}'.")


# ------------------ PRINT SERIALIZED RESULTS FUNCTION ------------------


def print_serialized_results(results: list):
    """Prints search results in a numbered list using Rich."""
    if not results:
        console.print("No results found.", style="bold red")
        return

    table = Table(title="Libgen Search Results")
    table.add_column("No.", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta")
    table.add_column("Authors", style="green")
    table.add_column("Year", style="yellow")
    table.add_column("Size", style="blue")
    table.add_column("Extension", style="blue")
    table.add_column("Mirror", overflow="fold", style="red")

    for idx, res in enumerate(results, start=1):
        table.add_row(
            str(idx),
            res.get("title", ""),
            res.get("authors", ""),
            res.get("year", ""),
            res.get("size", ""),
            res.get("extension", ""),
            res.get("mirror", ""),
        )
    console.print(table)


# ------------------ INTERACTIVE MODE ------------------


def interactive_mode(proxies):
    print("Entering interactive mode. Type 'exit' or 'quit' to leave.")
    loop = asyncio.get_event_loop()
    while True:
        query = input("Search query> ").strip()
        if query.lower() in ("exit", "quit"):
            break
        try:
            results = loop.run_until_complete(search(query, proxies=proxies))
            print_serialized_results(results)
            choice = input(
                "Enter the serial number of the book to download (or press Enter to skip): "
            ).strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if index < 0 or index >= len(results):
                        print("Invalid serial number.")
                        continue
                    mirror_url = results[index].get("mirror")
                    if not mirror_url:
                        print("No mirror URL available for that selection.")
                        continue
                    output = (
                        input(
                            "Enter output filename (default 'download.bin'): "
                        ).strip()
                        or "download.bin"
                    )
                    loop.run_until_complete(download_file(mirror_url, output))
                except ValueError:
                    print("Please enter a valid number.")
        except LibgenError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")


# ------------------ HELP / MANUAL FUNCTIONS ------------------


def print_manual():
    manual = """
Full Libgen Async CLI Manual
============================

This tool lets you search for and download books from Libgen (and its alternatives)
using asynchronous network calls.

Usage Modes:
------------
1. Search Mode:
   Command: libgen search "search query" [--proxy PROXY_URL ...]
   - Searches Libgen for books matching the query.
   - Results are displayed as a numbered list.
   - After the search, you will be prompted to enter the serial number of the desired book to download.
   - The file will be saved inside the "libgen" directory.

2. Download Mode:
   Command: libgen download MIRROR_URL [--output filename]
   - Downloads a file from the specified mirror URL.
   - Files are saved in the "libgen" folder.
   - If the file exists, you will be prompted before overwriting.

3. Interactive Mode:
   Command: libgen interactive [--proxy PROXY_URL ...]
   - A REPL loop where you can enter search queries repeatedly.
   - Results are shown as a numbered list.
   - You can select a book by its serial number to download it.
   - Type "exit" or "quit" to leave interactive mode.
   - Running "libgen" with no arguments defaults to interactive mode.

Additional Help:
----------------
- "libgen help" displays short usage info.
- "libgen help [command]" provides details for that command.
- "libgen manual" or "man libgen" prints this full manual.

Enjoy using Libgen Async CLI!
"""
    print(manual)


def print_short_help(topic=None):
    help_text = {
        None: """
Libgen Async CLI - Available commands:

  search      : Search for books (e.g., libgen search "python")
  download    : Download a file from a mirror URL (e.g., libgen download MIRROR_URL)
  interactive : Enter interactive mode for searching & downloading
  help        : Show short help (e.g., libgen help search)
  manual/man  : Show the full manual

Running "libgen" without any arguments enters interactive mode.
""",
        "search": """
Search Mode:
  Usage: libgen search "search query" [--proxy PROXY_URL ...]
  - Performs a search on Libgen.
  - Results are displayed as a numbered list.
  - After the search, you'll be prompted to select a serial number to download.
""",
        "download": """
Download Mode:
  Usage: libgen download MIRROR_URL [--output filename]
  - Downloads a file from the specified mirror URL.
  - Files are saved in the "libgen" folder.
  - You will be prompted if the file exists.
""",
        "interactive": """
Interactive Mode:
  Usage: libgen interactive [--proxy PROXY_URL ...]
  - Enters a REPL loop to perform searches repeatedly.
  - Results are shown as a numbered list.
  - Select a book by its serial number to download.
  - Type 'exit' or 'quit' to exit interactive mode.
""",
        "help": """
Help Command:
  Usage: libgen help [command]
  - Without a command, shows an overview of available commands.
  - With a command (search, download, interactive), displays detailed help.
""",
        "manual": """
Full Manual:
  Usage: libgen manual
  - Displays the complete manual with detailed instructions and examples.
  Alternatively, use "man libgen".
""",
    }
    print(help_text.get(topic, "No extended help available for that command."))


# ------------------ MAIN CLI ------------------


def main():
    parser = argparse.ArgumentParser(
        description="Libgen Async CLI with search, download, interactive modes, and built-in help/manual",
        add_help=False,
    )
    subparsers = parser.add_subparsers(dest="command", help="Available commands")

    # search command
    search_parser = subparsers.add_parser("search", help="Search for books on Libgen")
    search_parser.add_argument("query", help="Search query")
    search_parser.add_argument(
        "--proxy", action="append", help="Proxy URL (multiple allowed)"
    )

    # download command
    download_parser = subparsers.add_parser(
        "download", help="Download file from mirror URL"
    )
    download_parser.add_argument("url", help="Mirror URL to download the file from")
    download_parser.add_argument(
        "--output",
        default="download.bin",
        help="Output filename (default: download.bin)",
    )

    # interactive command
    interactive_parser = subparsers.add_parser(
        "interactive", help="Enter interactive mode"
    )
    interactive_parser.add_argument(
        "--proxy", action="append", help="Proxy URL (multiple allowed)"
    )

    # help command (custom help)
    help_parser = subparsers.add_parser("help", help="Show short help information")
    help_parser.add_argument(
        "topic",
        nargs="?",
        default=None,
        help="Optional: command to show detailed help for (e.g., search)",
    )

    # manual command (full manual)
    manual_parser = subparsers.add_parser("manual", help="Show full manual")
    # Allow alias "man" by checking sys.argv.
    if len(sys.argv) > 1 and sys.argv[1] in ("man",):
        print_manual()
        sys.exit(0)

    # If no arguments are provided, default to interactive mode.
    if len(sys.argv) == 1:
        interactive_mode(proxies=None)
        sys.exit(0)

    args = parser.parse_args()

    if args.command == "search":
        try:
            results = asyncio.run(search(args.query, proxies=args.proxy))
            print_serialized_results(results)
            choice = input(
                "Enter the serial number of the book to download (or press Enter to skip): "
            ).strip()
            if choice:
                try:
                    index = int(choice) - 1
                    if index < 0 or index >= len(results):
                        print("Invalid serial number.")
                    else:
                        mirror_url = results[index].get("mirror")
                        if not mirror_url:
                            print("No mirror URL available for that selection.")
                        else:
                            output = (
                                input(
                                    "Enter output filename (default 'download.bin'): "
                                ).strip()
                                or "download.bin"
                            )
                            asyncio.run(download_file(mirror_url, output))
                except ValueError:
                    print("Please enter a valid number.")
        except LibgenError as e:
            print(f"Error: {e}")
        except Exception as e:
            print(f"Unexpected error: {e}")

    elif args.command == "download":
        try:
            asyncio.run(download_file(args.url, args.output))
        except Exception as e:
            print(f"Download failed: {e}")

    elif args.command == "interactive":
        interactive_mode(args.proxy)

    elif args.command == "help":
        print_short_help(args.topic)

    elif args.command == "manual":
        print_manual()


if __name__ == "__main__":
    main()

# ------------------ END OF LIBGEN CLI ------------------