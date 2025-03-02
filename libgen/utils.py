from rich.console import Console
from rich.table import Table


def pretty_print(results: list):
    console = Console()
    if not results:
        console.print("No results found.", style="bold red")
        return

    table = Table(title="Libgen Search Results")
    columns = [
        "cover",
        "title",
        "authors",
        "publisher",
        "year",
        "language",
        "pages",
        "size",
        "extension",
        "mirror",
    ]
    for col in columns:
        table.add_column(col.capitalize(), overflow="fold")
    for res in results:
        # For the cover and mirror, we print the URL
        row = [res.get(col, "") for col in columns]
        table.add_row(*row)
    console.print(table)
