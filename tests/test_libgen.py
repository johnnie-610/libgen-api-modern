import asyncio
import unittest

from libgen.client import search, LibgenError
from libgen.utils import pretty_print


class TestLibgenAsyncLiveSearch(unittest.TestCase):

    def test_live_search(self):
        async def run_search():
            try:
                results = await search("the art of war")
                print("\nLive search results:")
                pretty_print(results)
                self.assertIsInstance(results, list)
                self.assertGreater(
                    len(results),
                    0,
                    "Expected at least one search result from live Libgen website.",
                )
            except LibgenError as e:
                self.fail(f"LibgenError occurred during live search: {e}")
            except Exception as e:
                self.fail(f"An unexpected error occurred during live search: {e}")

        asyncio.run(run_search())


if __name__ == "__main__":
    unittest.main()
