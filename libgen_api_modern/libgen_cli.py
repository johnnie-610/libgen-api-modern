# src/libgen_cli/main.py
#!/usr/bin/env python3

import asyncio
import argparse
import sys
import signal
from pathlib import Path
from typing import Optional, List
from functools import partial
from rich.console import Console
from rich.table import Table
from rich.progress import (
    Progress,
    SpinnerColumn,
    TextColumn,
    BarColumn,
    DownloadColumn,
    TransferSpeedColumn,
)
import httpx
from concurrent.futures import ThreadPoolExecutor

try:
    import uvloop

    asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
except ImportError:
    pass  # Windows doesn't support uvloop

from .search_request import SearchRequest, BookData, SearchType

console = Console()
executor = ThreadPoolExecutor(max_workers=5)  # For file I/O operations


class LibGenCLI:
    def __init__(self):
        self.download_dir = Path.home() / "Downloads" / "libgen"
        self.download_dir.mkdir(parents=True, exist_ok=True)
        self.client: Optional[httpx.AsyncClient] = None
        self._setup_signal_handlers()

    def _setup_signal_handlers(self):
        """Setup graceful shutdown handlers."""
        for sig in (signal.SIGTERM, signal.SIGINT):
            signal.signal(sig, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully."""
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
        if self.client:
            asyncio.create_task(self.client.aclose())
        sys.exit(0)

    def create_parser(self) -> argparse.ArgumentParser:
        parser = argparse.ArgumentParser(
            description="Fast Library Genesis CLI Search and Download Tool",
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

        parser.add_argument(
            "--parallel",
            type=int,
            default=3,
            help="Number of parallel downloads (default: 3)",
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

        # Pre-process all data before adding to table
        processed_books = []
        for idx, book in enumerate(books[:limit], 1):
            authors = ", ".join(book.authors)
            processed_books.append(
                {
                    "idx": str(idx),
                    "title": (
                        book.title[:37] + "..." if len(book.title) > 40 else book.title
                    ),
                    "authors": authors[:27] + "..." if len(authors) > 30 else authors,
                    "year": book.year,
                    "size": book.size,
                    "extension": book.extension.upper(),
                    "language": book.language,
                }
            )

        # Bulk add rows
        for book in processed_books:
            table.add_row(
                book["idx"],
                book["title"],
                book["authors"],
                book["year"],
                book["size"],
                book["extension"],
                book["language"],
            )

        console.print(table)

        while True:
            choice = console.input(
                "\nSelect a book to download (1-{}) or 'q' to quit: ".format(
                    min(len(books), limit)
                )
            )

            if choice.lower() == "q":
                return None

            try:
                idx = int(choice) - 1
                if 0 <= idx < len(books):
                    return books[idx]
                console.print("[red]Invalid selection. Please try again.[/red]")
            except ValueError:
                console.print("[red]Invalid input. Please enter a number or 'q'.[/red]")

    async def _write_file(self, filepath: Path, content: bytes) -> None:
        """Write file content asynchronously using thread executor."""
        await asyncio.get_event_loop().run_in_executor(
            executor, partial(filepath.write_bytes, content)
        )

    async def download_book(self, book: BookData) -> bool:
        """Download the selected book with progress bar."""
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
                BarColumn(),
                DownloadColumn(),
                TransferSpeedColumn(),
            ) as progress:
                task = progress.add_task(f"Downloading {filename}", total=None)

                async with self.client.stream("GET", book.download_url) as response:
                    response.raise_for_status()
                    total = int(response.headers.get("content-length", 0))
                    progress.update(task, total=total)

                    chunks = []
                    async for chunk in response.aiter_bytes(chunk_size=8192):
                        chunks.append(chunk)
                        progress.update(task, advance=len(chunk))

                    content = b"".join(chunks)
                    await self._write_file(filepath, content)

            console.print(f"\n[green]Successfully downloaded to:[/green] {filepath}")

            if book.cover_url:
                cover_filename = f"{filename}_cover.jpg"
                cover_path = self.download_dir / cover_filename

                async with self.client.stream("GET", book.cover_url) as response:
                    response.raise_for_status()
                    content = await response.aread()
                    await self._write_file(cover_path, content)

                console.print(f"[green]Cover image downloaded to:[/green] {cover_path}")

            return True

        except Exception as e:
            console.print(f"[red]Error downloading book: {str(e)}[/red]")
            return False

    async def interactive_search(self):
        """Interactive search mode with improved error handling."""
        while True:
            try:
                query = console.input("\nEnter search query (or 'q' to quit): ")
                if query.lower() == "q":
                    break

                search_type = (
                    console.input(
                        "Select search type [default/fiction/scientific] (default): "
                    )
                    or "default"
                )

                await self.perform_search(query, search_type)

                if (
                    not console.input(
                        "\nWould you like to perform another search? [y/N]: "
                    )
                    .lower()
                    .startswith("y")
                ):
                    break
            except Exception as e:
                console.print(f"[red]Error during search: {str(e)}[/red]")
                if (
                    not console.input("\nWould you like to try again? [y/N]: ")
                    .lower()
                    .startswith("y")
                ):
                    break

    async def perform_search(self, query: str, search_type: str):
        """Perform search and handle book selection/download."""
        search_type_map = {
            "default": SearchType.DEFAULT,
            "fiction": SearchType.FICTION,
            "scientific": SearchType.SCIMAG,
        }

        with console.status("[bold green]Searching Library Genesis...") as _:
            async with SearchRequest(query, search_type_map[search_type]) as searcher:
                books = await searcher.search()

        selected_book = self.display_results(books)
        if selected_book:
            await self.download_book(selected_book)

    async def run(self, args: argparse.Namespace):
        """Main run method with connection pooling."""
        if args.download_dir:
            self.download_dir = Path(args.download_dir)
            self.download_dir.mkdir(parents=True, exist_ok=True)

        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        timeout = httpx.Timeout(10.0, connect=5.0)

        async with httpx.AsyncClient(limits=limits, timeout=timeout) as client:
            self.client = client
            if args.query:
                await self.perform_search(args.query, args.type)
            else:
                await self.interactive_search()




# EOF