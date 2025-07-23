# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT

import argparse
import asyncio
import aiohttp
import os
import sys
from typing import List

from rich.console import Console
from rich.progress import (
    BarColumn,
    DownloadColumn,
    Progress,
    TextColumn,
    TimeRemainingColumn,
    TransferSpeedColumn,
)
from rich.table import Table

from errors import LibgenError, LibgenSearchError, LibgenNetworkError
from models import BookData
from client import search_async

console = Console()


async def download_file(url: str, output_path: str):
    """Asynchronously downloads a file with a progress bar."""
    if os.path.exists(output_path):
        if console.input(f"[yellow]File '{output_path}' already exists. Overwrite? (y/N): [/yellow]").lower() != 'y':
            console.print("[red]Download canceled.[/red]")
            return

    console.print(f"Starting download from [green]{url}[/green] to [cyan]{output_path}[/cyan]")

    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as resp:
                resp.raise_for_status()
                total_size = int(resp.headers.get("content-length", 0))

                with Progress(
                    TextColumn("[bold blue]{task.fields[filename]}", justify="right"),
                    BarColumn(bar_width=None),
                    "[progress.percentage]{task.percentage:>3.1f}%", "•",
                    DownloadColumn(), "•",
                    TransferSpeedColumn(), "•",
                    TimeRemainingColumn(),
                    transient=True,
                ) as progress:
                    task = progress.add_task("Downloading", total=total_size, filename=os.path.basename(output_path))
                    with open(output_path, "wb") as f:
                        async for chunk in resp.content.iter_chunked(8192):
                            f.write(chunk)
                            progress.update(task, advance=len(chunk))

        console.print(f"[bold green]Download complete: '{output_path}'[/bold green]")

    except aiohttp.ClientError as e:
        raise LibgenNetworkError(f"Network error during download: {e}", url=url)
    except OSError as e:
        raise LibgenError(f"File system error: {e}")


def print_search_results(results: List[BookData]):
    """Prints search results in a Rich table."""
    if not results:
        console.print("[bold red]No results found.[/bold red]")
        return

    table = Table(title="Library Genesis Search Results", show_lines=True)
    table.add_column("ID", style="cyan", no_wrap=True)
    table.add_column("Title", style="magenta", overflow="fold")
    table.add_column("Author(s)", style="green", overflow="fold")
    table.add_column("Year", style="yellow")
    table.add_column("Size", style="blue")
    table.add_column("Ext", style="blue")

    for book in results:
        table.add_row(
            book.id,
            book.title or "N/A",
            ", ".join(book.authors) if book.authors else "N/A",
            book.year or "N/A",
            book.size or "N/A",
            book.extension or "N/A",
        )
    console.print(table)


async def interactive_mode():
    """Runs the interactive search and download loop."""
    console.print("[bold blue]Welcome to Libgen Interactive Mode. Type 'exit' or 'quit' to leave.[/bold blue]")
    while True:
        try:
            query = console.input("[green]Search query> [/green]").strip()
            if query.lower() in ("exit", "quit"):
                break
            if not query:
                continue

            with console.status("[yellow]Searching...[/yellow]", spinner="dots"):
                results = await search_async(query)

            if not results:
                console.print("[red]No results found for your query.[/red]")
                continue

            print_search_results(results)

            choice = console.input("Enter the ID of the book to download (or press Enter to search again): ").strip()
            if not choice:
                continue

            selected_book = next((book for book in results if book.id == choice), None)

            if not selected_book:
                console.print("[red]Invalid ID.[/red]")
                continue

            if not (selected_book.download_links and selected_book.download_links.get_link):
                console.print("[red]No direct download link found for this book.[/red]")
                continue

            sane_title = "".join(c for c in selected_book.title if c.isalnum() or c in " ._-")
            default_filename = f"{sane_title[:60]}.{selected_book.extension}"
            output = console.input(f"Enter output filename (default: [cyan]{default_filename}[/cyan]): ").strip() or default_filename

            await download_file(selected_book.download_links.get_link, output)

        except (LibgenSearchError, LibgenNetworkError) as e:
            console.print(f"[bold red]Error: {e}[/bold red]")
        except Exception as e:
            console.print(f"[bold red]An unexpected error occurred: {e}[/bold red]")


def main():
    parser = argparse.ArgumentParser(description="A modern CLI for Library Genesis.")
    subparsers = parser.add_subparsers(dest="command", required=True, help="Available commands")

    # Search command
    search_parser = subparsers.add_parser("search", help="Search for books.")
    search_parser.add_argument("query", type=str, help="The search query.")

    # Download command
    download_parser = subparsers.add_parser("download", help="Download a book from a direct URL.")
    download_parser.add_argument("url", type=str, help="The direct download URL.")
    download_parser.add_argument("--output", "-o", type=str, help="The output filename.")

    # Interactive command
    subparsers.add_parser("interactive", help="Enter interactive search and download mode.")

    args = parser.parse_args()

    try:
        if args.command == "search":
            results = asyncio.run(search_async(args.query))
            print_search_results(results)
        elif args.command == "download":
            filename = args.output or os.path.basename(args.url.split('?')[0])
            asyncio.run(download_file(args.url, filename))
        elif args.command == "interactive":
            asyncio.run(interactive_mode())
    except LibgenError as e:
        console.print(f"[bold red]Error: {e}[/bold red]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"[bold red]An unexpected critical error occurred: {e}[/bold red]")
        sys.exit(1)


if __name__ == "__main__":
    main()