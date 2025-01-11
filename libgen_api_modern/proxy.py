# Copyright (c) 2024-2025 Johnnie
#
# This software is released under the MIT License.
# https://opensource.org/licenses/MIT
#
# This file is part of the libgen-api-modern library

from dataclasses import dataclass
from typing import List, Optional, Dict, Set
import asyncio
import time
import random
from datetime import datetime, timedelta
import aiofiles
import httpx
from pathlib import Path
import orjson
import logging
from functools import wraps


@dataclass
class ProxyStats:
    success_count: int = 0
    fail_count: int = 0
    last_used: float = 0
    average_response_time: float = 0
    last_error: Optional[str] = None


class RateLimiter:

    def __init__(
        self,
        requests_per_second: float = 2.0,
        burst_size: int = 5,
        per_host_delay: float = 1.0,
    ):
        self.rate = requests_per_second
        self.burst_size = burst_size
        self.per_host_delay = per_host_delay
        self.tokens = burst_size
        self.last_update = time.monotonic()
        self.lock = asyncio.Lock()
        self.host_timestamps: Dict[str, float] = {}

    async def acquire(self, host: Optional[str] = None) -> None:
        async with self.lock:
            # Update tokens based on time passed
            now = time.monotonic()
            time_passed = now - self.last_update
            self.tokens = min(self.burst_size, self.tokens + time_passed * self.rate)

            # Check host-specific rate limit
            if host:
                last_host_request = self.host_timestamps.get(host, 0)
                host_delay = now - last_host_request
                if host_delay < self.per_host_delay:
                    await asyncio.sleep(self.per_host_delay - host_delay)
                self.host_timestamps[host] = now

            # If we need to wait for tokens
            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 1

            self.tokens -= 1
            self.last_update = now


class ProxyManager:

    def __init__(self, cache_dir: Path = Path.home() / ".cache" / "libgen-cli"):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.proxy_file = self.cache_dir / "proxies.json"
        self.proxies: Dict[str, ProxyStats] = {}
        self.rate_limiter = RateLimiter()
        self._load_proxies()

    def _load_proxies(self) -> None:
        try:
            if self.proxy_file.exists():
                with open(self.proxy_file, "rb") as f:
                    data = orjson.loads(f.read())
                    self.proxies = {
                        url: ProxyStats(**stats) for url, stats in data.items()
                    }
        except Exception as e:
            logging.warning(f"Failed to load proxies: {e}")

    async def _save_proxies(self) -> None:
        try:
            async with aiofiles.open(self.proxy_file, "wb") as f:
                data = {url: stats.__dict__ for url, stats in self.proxies.items()}
                await f.write(orjson.dumps(data))
        except Exception as e:
            logging.warning(f"Failed to save proxies: {e}")

    async def add_proxy(self, proxy_url: str) -> None:
        if proxy_url not in self.proxies:
            self.proxies[proxy_url] = ProxyStats()
            await self._save_proxies()

    async def remove_proxy(self, proxy_url: str) -> None:
        if proxy_url in self.proxies:
            del self.proxies[proxy_url]
            await self._save_proxies()

    async def get_best_proxy(self) -> Optional[str]:
        if not self.proxies:
            return None

        # Score proxies based on success rate and response time
        proxy_scores = {}
        for url, stats in self.proxies.items():
            total_requests = stats.success_count + stats.fail_count
            if total_requests == 0:
                success_rate = 0
            else:
                success_rate = stats.success_count / total_requests

            # Factor in response time (lower is better)
            time_score = 1 / (stats.average_response_time + 1)

            # Calculate final score
            proxy_scores[url] = success_rate * 0.7 + time_score * 0.3

        # Return the proxy with the highest score
        return max(proxy_scores.items(), key=lambda x: x[1])[0]

    async def update_proxy_stats(
        self,
        proxy_url: str,
        success: bool,
        response_time: float,
        error: Optional[str] = None,
    ) -> None:
        if proxy_url in self.proxies:
            stats = self.proxies[proxy_url]
            if success:
                stats.success_count += 1
            else:
                stats.fail_count += 1
                stats.last_error = error

            # Update average response time with exponential moving average
            alpha = 0.3  # Weight for new values
            if stats.average_response_time == 0:
                stats.average_response_time = response_time
            else:
                stats.average_response_time = (
                    alpha * response_time + (1 - alpha) * stats.average_response_time
                )

            stats.last_used = time.time()
            await self._save_proxies()


class ProxySession:

    def __init__(
        self, proxy_manager: ProxyManager, max_retries: int = 3, timeout: float = 10.0
    ):
        self.proxy_manager = proxy_manager
        self.max_retries = max_retries
        self.timeout = timeout
        self.client: Optional[httpx.AsyncClient] = None

    async def __aenter__(self):
        limits = httpx.Limits(max_keepalive_connections=5, max_connections=10)
        transport = httpx.AsyncHTTPTransport(retries=1)  # Low level retries

        self.client = httpx.AsyncClient(
            timeout=self.timeout,
            limits=limits,
            transport=transport,
            follow_redirects=True,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def request(self, method: str, url: str, **kwargs) -> httpx.Response:
        retries = 0
        last_exception = None

        while retries < self.max_retries:
            proxy_url = await self.proxy_manager.get_best_proxy()
            if proxy_url:
                kwargs["proxies"] = {"all://": proxy_url}

            try:

                await self.proxy_manager.rate_limiter.acquire(
                    httpx.URL(url).host
                )  # Apply rate limiting

                start_time = time.monotonic()
                response = await self.client.request(method, url, **kwargs)
                response_time = time.monotonic() - start_time

                if proxy_url:
                    await self.proxy_manager.update_proxy_stats(
                        proxy_url, True, response_time
                    )

                return response

            except Exception as e:
                last_exception = e
                if proxy_url:
                    await self.proxy_manager.update_proxy_stats(
                        proxy_url, False, 0, str(e)
                    )
                retries += 1

                await asyncio.sleep(2**retries)  # Exponential backoff

        raise last_exception


def requires_proxy_session(f):

    @wraps(f)
    async def wrapper(self, *args, **kwargs):
        if not hasattr(self, "proxy_session"):
            self.proxy_session = await ProxySession(self.proxy_manager).__aenter__()
        try:
            return await f(self, *args, **kwargs)
        finally:
            if hasattr(self, "proxy_session"):
                await self.proxy_session.__aexit__(None, None, None)

    return wrapper
