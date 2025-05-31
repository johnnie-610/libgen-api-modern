#!/usr/bin/env python3
"""
Test script for the LibgenClient class.
This script tests both synchronous and asynchronous functionality.
"""

import asyncio
import sys
from libgen.new.client import LibgenClient, search, search_sync

async def test_async():
    """Test asynchronous search functionality"""
    print("Testing asynchronous search...")
    
    # Test using the client class
    async with LibgenClient() as client:
        results = await client.search_async("python programming")
        print(f"Found {len(results)} results using client.search_async")
        if results:
            print(f"First result: {results[0].title} by {', '.join(results[0].authors)}")
    
    # Test using the standalone function
    results = await search("python programming")
    print(f"Found {len(results)} results using search function")
    if results:
        print(f"First result: {results[0]['title']} by {results[0]['authors']}")
    
    return True

def test_sync():
    """Test synchronous search functionality"""
    print("\nTesting synchronous search...")
    
    # Test using the client class
    with LibgenClient() as client:
        results = client.search_sync("python programming")
        print(f"Found {len(results)} results using client.search_sync")
        if results:
            print(f"First result: {results[0].title} by {', '.join(results[0].authors)}")
    
    # Test using the standalone function
    results = search_sync("python programming")
    print(f"Found {len(results)} results using search_sync function")
    if results:
        print(f"First result: {results[0]['title']} by {results[0]['authors']}")
    
    return True

async def main():
    """Run all tests"""
    try:
        async_success = await test_async()
        sync_success = test_sync()
        
        if async_success and sync_success:
            print("\nAll tests passed!")
            return 0
        else:
            print("\nSome tests failed!")
            return 1
    except Exception as e:
        print(f"Error during testing: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(asyncio.run(main()))