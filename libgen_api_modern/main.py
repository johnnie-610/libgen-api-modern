import asyncio
import sys
from libgen_api_modern.libgen_cli import LibGenCLI, console, executor


def main():
    """Entry point for the CLI tool."""
    cli = LibGenCLI()
    parser = cli.create_parser()
    args = parser.parse_args()

    try:
        if sys.platform != "win32":
            # Use uvloop on non-Windows platforms
            import uvloop

            uvloop.install()

        asyncio.run(cli.run(args))
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user[/yellow]")
        sys.exit(0)
    except Exception as e:
        console.print(f"\n[red]An error occurred: {str(e)}[/red]")
        sys.exit(1)
    finally:
        executor.shutdown(wait=False)


if __name__ == "__main__":
    main()
