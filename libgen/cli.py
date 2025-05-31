# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# libgen/cli.py
#
# This file is part of the libgen-api-modern library

import argparse
import asyncio
import aiohttp
import os
import sys

from rich.progress import TextColumn, DownloadColumn, BarColumn, TransferSpeedColumn, TimeRemainingColumn, Progress

# import logging

from libgen import search_async, LibgenError, BookData, LibgenSearchError, LibgenNetworkError
from rich.table import Table
from rich.console import Console

console = Console()

# logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


# ------------------ DOWNLOAD FUNCTION ------------------
async def download_file(url: str, output_filename: str):
    """Download a file from the given URL and save it to disk safely inside the 'libgen' folder with a progress bar."""
    download_dir = os.path.join(os.getcwd(), "libgen")
    if not os.path.exists(download_dir):
        try:
            os.makedirs(download_dir)
            console.print(f"Created download directory: [cyan]{download_dir}[/cyan]")
        except OSError as e:
            raise LibgenError(f"Could not create directory {download_dir}: {e}")

    output_path = os.path.join(download_dir, os.path.basename(output_filename))

    if os.path.exists(output_path):
        ans = console.input(
            f"[yellow]File '{os.path.relpath(output_path)}' already exists. Overwrite? (y/N):[/yellow] " # Use relpath for shorter display
        ).strip().lower()
        if ans != "y":
            console.print("[red]Download canceled.[/red]")
            return

    console.print(f"Starting download from [green]{url}[/green] to [cyan]{os.path.relpath(output_path)}[/cyan]")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                total_size = int(resp.headers.get('content-length', 0)) # Get total size for progress bar

                with Progress( # Rich Progress context manager
                        TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                        BarColumn(bar_width=None),
                        "[progress.percentage]{task.percentage:>3.1f}%",
                        "•",
                        DownloadColumn(),
                        "•",
                        TransferSpeedColumn(),
                        "•",
                        TimeRemainingColumn(),
                        console=console, # Use the existing console
                        transient=True # Remove progress bar when done
                ) as progress:
                    download_task = progress.add_task("Downloading", total=total_size, filename=os.path.basename(output_path))

                    with open(output_path, "wb") as f:
                        downloaded_so_far = 0
                        while True:
                            chunk = await resp.content.read(8192) # 8KB chunks
                            if not chunk:
                                break
                            f.write(chunk)
                            downloaded_so_far += len(chunk)
                            progress.update(download_task, advance=len(chunk))
                            # If total_size was 0 initially (not provided by server), update it now
                            if total_size == 0 and downloaded_so_far > 0 and not progress.tasks[download_task].completed:
                                # This is a bit of a hack if server doesn't send content-length
                                # The progress bar might jump or look indeterminate initially
                                pass # Or set total based on an assumption if desired

                console.print(
                    f"[bold green]Downloaded {downloaded_so_far} bytes; saved as '{os.path.relpath(output_path)}'.[/bold green]"
                )
    except aiohttp.ClientError as e:
        raise LibgenNetworkError(f"AIOHTTP download error: {e}", url=url)
    except OSError as e:
        raise LibgenError(f"File system error during download: {e}")
    except Exception as e:
        console.print_exception(show_locals=True) # For debugging unexpected errors
        raise LibgenError(f"An unexpected error occurred during download: {e}")


# ------------------ PRINT SERIALIZED RESULTS FUNCTION ------------------
def print_search_results(results: list[BookData]):
    """Prints search results in a table using Rich."""
    if not results:
        console.print("[bold red]No results found.[/bold red]")
        return

    table = Table(title="Libgen Search Results", show_lines=True)
    table.add_column("No.", justify="right", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta", overflow="fold")
    table.add_column("Authors", style="green", overflow="fold")
    table.add_column("Year", style="yellow")
    table.add_column("Size", style="blue")
    table.add_column("Ext", style="blue") # Shorter name for Extension
    table.add_column("Mirror",เที่ยว="fold", style="dim cyan") # Dim for less prominent URLs

    for idx, book in enumerate(results, start=1):
        authors_str = ", ".join(book.authors) if book.authors else "N/A"
        # Get the primary download link; BookData.download_links.get_link
        mirror_url = (
            book.download_links.get_link
            if book.download_links and book.download_links.get_link
            else "N/A"
        )
        table.add_row(
            str(idx),
            book.title or "N/A",
            authors_str,
            book.year or "N/A",
            book.size or "N/A",
            book.extension or "N/A",
            mirror_url,
            )
    console.print(table)


# ------------------ INTERACTIVE MODE ------------------
async def interactive_mode_async(proxies: list[str] | None):
    """Asynchronous interactive mode."""
    console.print("[bold blue]Entering interactive mode. Type 'exit' or 'quit' to leave.[/bold blue]")
    while True:
        try:
            query = console.input("[green]Search query>[/green] ").strip()
            if query.lower() in ("exit", "quit"):
                break
            if not query:
                continue

            with console.status("[yellow]Searching...[/yellow]", spinner="dots"):
                results = await search_async(query, proxies=proxies) # Uses unified search

            print_search_results(results)

            if not results:
                continue

            choice_str = console.input(
                "Enter the number of the book to download (or press Enter to skip): "
            ).strip()
            if choice_str:
                try:
                    index = int(choice_str) - 1
                    if not (0 <= index < len(results)):
                        console.print("[red]Invalid selection number.[/red]")
                        continue

                    selected_book = results[index]
                    mirror_url = (
                        selected_book.download_links.get_link
                        if selected_book.download_links and selected_book.download_links.get_link
                        else None
                    )

                    if not mirror_url:
                        console.print("[red]No direct download mirror URL available for this selection.[/red]")
                        continue

                    # Generate a default filename from title and extension
                    default_filename = "download.pdf"
                    if selected_book.title and selected_book.extension:
                        # Sanitize title for filename
                        sane_title = "".join(c if c.isalnum() or c in " .-_" else "_" for c in selected_book.title)
                        default_filename = f"{sane_title[:50]}.{selected_book.extension}"


                    output_filename = console.input(
                        f"Enter output filename (default: [cyan]{default_filename}[/cyan]): "
                    ).strip() or default_filename

                    await download_file(mirror_url, output_filename)

                except ValueError:
                    console.print("[red]Please enter a valid number.[/red]")
                except LibgenError as e: # Catch errors from download_file or selection logic
                    console.print(f"[bold red]Error: {e}[/bold red]")

        except LibgenSearchError as e:
            console.print(f"[bold red]Search Error: {e}[/bold red]")
        except LibgenNetworkError as e:
            console.print(f"[bold red]Network Error: {e}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]",)
            # For debugging, you might want to print traceback:
            # console.print_exception(show_locals=True)


# ------------------ HELP / MANUAL FUNCTIONS ------------------
def print_manual():
    manual = """... (manual text as before) ..."""
    console.print(manual)

def print_short_help(topic=None):
    help_text = {
        None: """... (help text as before) ...""",
        "search": """...""",
        "download": """...""",
        "interactive": """...""",
        "help": """...""",
        "manual": """...""",
    }
    console.print(help_text.get(topic, "[red]No extended help available for that command.[/red]"))


# ------------------ MAIN CLI FUNCTION ------------------
def main():
    parser = argparse.ArgumentParser(
        description="Libgen Async CLI: Search, download, and interact with Library Genesis.",
        add_help=False, # Using custom help
    )
    # Custom help action
    parser.add_argument(
        "-h", "--help", action="store_true", help="Show this help message and exit"
    )

    subparsers = parser.add_subparsers(dest="command", title="Commands", metavar="<command>")
    subparsers.required = False # To allow no command (defaults to interactive or help)

    # search command
    search_parser = subparsers.add_parser("search", help="Search for books on Libgen")
    search_parser.add_argument("query", help="The search query string")
    search_parser.add_argument(
        "--proxy", action="append", help="Proxy URL (e.g., http://localhost:8080). Can be used multiple times."
    )

    # download command
    download_parser = subparsers.add_parser("download", help="Download a file from a direct mirror URL")
    download_parser.add_argument("url", help="The direct mirror URL to download from")
    download_parser.add_argument(
        "--output",
        help="Output filename (e.g., book.pdf). Defaults to a sanitized name or 'download.bin'.",
    )

    # interactive command
    interactive_parser = subparsers.add_parser("interactive", help="Enter interactive mode for searching and downloading")
    interactive_parser.add_argument(
        "--proxy", action="append", help="Proxy URL for interactive mode sessions."
    )

    # help command (custom detailed help)
    help_parser_custom = subparsers.add_parser("help", help="Show detailed help for a command")
    help_parser_custom.add_argument(
        "topic",
        nargs="?", # Optional topic
        default=None,
        choices=["search", "download", "interactive", "manual", "help"],
        help="Get help on a specific command.",
    )

    # manual command
    subparsers.add_parser("manual", help="Show the full user manual")
    # 'man' alias is handled by checking sys.argv before parsing
    if len(sys.argv) > 1 and sys.argv[1] in ("man",):
        print_manual()
        sys.exit(0)

    args = parser.parse_args()

    if args.help and not args.command: # if -h is used without a subcommand
        parser.print_help()
        sys.exit(0)

    loop = asyncio.get_event_loop()

    try:
        if args.command == "search":
            console.print(f"Searching for: \"{args.query}\"...")
            with console.status("[yellow]Searching...[/yellow]", spinner="dots"):
                results = loop.run_until_complete(search_async(args.query, proxies=args.proxy))
            print_search_results(results)

            if results: # Only prompt for download if there are results
                choice_str = console.input(
                    "Enter book number to download (or Enter to skip): "
                ).strip()
                if choice_str:
                    try:
                        index = int(choice_str) - 1
                        if not (0 <= index < len(results)):
                            console.print("[red]Invalid selection number.[/red]")
                        else:
                            selected_book = results[index]
                            mirror_url = (
                                selected_book.download_links.get_link
                                if selected_book.download_links and selected_book.download_links.get_link
                                else None
                            )
                            if not mirror_url:
                                console.print("[red]No direct download mirror URL available.[/red]")
                            else:
                                default_filename = "download.bin"
                                if selected_book.title and selected_book.extension:
                                    sane_title = "".join(c if c.isalnum() or c in " .-_" else "_" for c in selected_book.title)
                                    default_filename = f"{sane_title[:50]}.{selected_book.extension}"

                                output_filename = console.input(
                                    f"Output filename (default: [cyan]{default_filename}[/cyan]): "
                                ).strip() or default_filename
                                loop.run_until_complete(download_file(mirror_url, output_filename))
                    except ValueError:
                        console.print("[red]Invalid input. Please enter a number.[/red]")

        elif args.command == "download":
            output_fn = args.output if args.output else os.path.basename(args.url.split('?')[0]) # Basic default from URL
            if not output_fn or output_fn == "/": # further sanitize default
                output_fn = "downloaded_file.bin"
            loop.run_until_complete(download_file(args.url, output_fn))

        elif args.command == "interactive":
            loop.run_until_complete(interactive_mode_async(args.proxy))

        elif args.command == "help":
            if args.topic:
                print_short_help(args.topic)
            else: # `libgen help` without topic
                parser.print_help() # Show general help
                print_short_help(None) # Show custom command overview

        elif args.command == "manual":
            print_manual()

        else: # No command given, default to interactive mode
            if args.help:
                parser.print_help()
            else:
                console.print("[bold blue]No command specified. Defaulting to interactive mode.[/bold blue]")
                loop.run_until_complete(interactive_mode_async(None))

    except LibgenError as e:
        console.print(f"[bold red]A Libgen specific error occurred: {e}[/bold red]")
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
    except Exception as e:
        console.print(f"[bold red]An unexpected critical error occurred: {e}[/bold red]")
        # For debugging:
        # console.print_exception(show_locals=True)
    finally:
        pass