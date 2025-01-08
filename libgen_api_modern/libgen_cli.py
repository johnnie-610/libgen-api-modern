#!/usr/bin/env python3

# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

import asyncio
import argparse
import os
import sys
from typing import Optional, List
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.prompt import Prompt, Confirm
import httpx
from pathlib import Path

# Import from our library file
from .search_request import SearchRequest, BookData, SearchType

console = Console()


class LibGenCLI:
    def __init__(self):
        self.download_dir = Path.home() / "Downloads" / "libgen"
        self.download_dir.mkdir(parents=True, exist_ok=True)

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Library Genesis CLI Search and Download Tool",
            formatter_class=argparse.RawDescriptionHelpFormatter,
        )

        parser.add_argument(
            "query",
            nargs="?",
            help="Search query. If not provided, enters interactive mode",
        )

        parser.add_argument(
            "-t",
            "--type",
            choices=["default", "fiction", "scientific"],
            default="default",
            help="Type of search to perform (default: default)",
        )

        parser.add_argument(
            "-d",
            "--download-dir",
            type=str,
            help="Download directory (default: ~/Downloads/libgen)",
        )

        parser.add_argument(
            "-l",
            "--limit",
            type=int,
            default=10,
            help="Maximum number of results to display (default: 10)",
        )

        return parser

    def display_results(
        self, books: List[BookData], limit: int = 10
    ) -> Optional[BookData]:
        """Display search results in a rich table and return selected book."""
        if not books:
            console.print("[yellow]No books found![/yellow]")
            return None

        table = Table(show_header=True, header_style="bold magenta")
        table.add_column("#", style="dim", width=4)
        table.add_column("Title", width=40)
        table.add_column("Author(s)", width=30)
        table.add_column("Year", width=6)
        table.add_column("Size", width=8)
        table.add_column("Format", width=6)
        table.add_column("Language", width=10)

        for idx, book in enumerate(books[:limit], 1):
            authors = ", ".join(book.authors)
            table.add_row(
                str(idx),
                book.title[:37] + "..." if len(book.title) > 40 else book.title,
                authors[:27] + "..." if len(authors) > 30 else authors,
                book.year,
                book.size,
                book.extension.upper(),
                book.language,
            )

        console.print(table)

        while True:
            choice = Prompt.ask(
                "\nSelect a book to download (1-{}) or 'q' to quit".format(
                    min(len(books), limit)
                ),
                default="q",
            )

            if choice.lower() == "q":
                return None

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(books):
                    return books[idx]
                else:
                    console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number or 'q'.[/red]")

    async def download_book(self, book: BookData, session: httpx.AsyncClient) -> bool:
        """Download the selected book."""
        if not book.download_url:
            console.print("[red]No download URL available for this book.[/red]")
            return False

        filename = f"{book.title[:50]}_{book.authors[0].split()[0]}_{book.year}.{book.extension}"
        filename = "".join(c if c.isalnum() or c in "._- " else "_" for c in filename)
        filepath = self.download_dir / filename

        try:
            with Progress(
                SpinnerColumn(),
                TextColumn("[progress.description]{task.description}"),
                transient=True,
            ) as progress:
                progress.add_task(description=f"Downloading {filename}...", total=None)

                response = await session.get(book.download_url)
                response.raise_for_status()

                with open(filepath, "wb") as f:
                    f.write(response.content)

            console.print(f"\n[green]Successfully downloaded to:[/green] {filepath}")

            if book.cover_url:
                cover_filename = f"{filename}_cover.jpg"
                cover_path = self.download_dir / cover_filename

                response = await session.get(book.cover_url)
                response.raise_for_status()

                with open(cover_path, "wb") as f:
                    f.write(response.content)
                console.print(f"[green]Cover image downloaded to:[/green] {cover_path}")

            return True

        except Exception as e:
            console.print(f"[red]Error downloading book: {str(e)}[/red]")
            return False

    async def interactive_search(self):
        """Interactive search mode."""
        while True:
            query = Prompt.ask("\nEnter search query (or 'q' to quit)")
            if query.lower() == "q":
                break

            search_type = Prompt.ask(
                "Select search type",
                choices=["default", "fiction", "scientific"],
                default="default",
            )

            await self.perform_search(query, search_type)

            if not Confirm.ask("\nWould you like to perform another search?"):
                break

    async def perform_search(self, query: str, search_type: str):
        """Perform search and handle book selection/download."""
        search_type_map = {
            "default": SearchType.DEFAULT,
            "fiction": SearchType.FICTION,
            "scientific": SearchType.SCIMAG,
        }

        with console.status("[bold green]Searching Library Genesis...") as status:
            async with SearchRequest(query, search_type_map[search_type]) as searcher:
                books = await searcher.search()

        selected_book = self.display_results(books)
        if selected_book:
            async with httpx.AsyncClient() as client:
                await self.download_book(selected_book, client)

    async def run(self, args: argparse.Namespace):
        """Main run method."""
        if args.download_dir:
            self.download_dir = Path(args.download_dir)
            self.download_dir.mkdir(parents=True, exist_ok=True)

        if args.query:
            await self.perform_search(args.query, args.type)
        else:
            await self.interactive_search()


def main():
    cli = LibGenCLI()
    parser = cli.create_parser()
    args = parser.parse_args()

    try:
        asyncio.run(cli.run(args))
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]An error occurred: {str(e)}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    main()

# EOF
