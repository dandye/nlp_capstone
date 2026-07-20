import asyncio
import random
import httpx
from typing import Optional


BROWSER_UA = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


class CISAFetcher:
    def __init__(self, base_url: str = "https://www.cisa.gov", concurrency: int = 3):
        self.base_url = base_url
        self.concurrency = concurrency
        self.semaphore = asyncio.Semaphore(concurrency)
        self.client = None

    async def __aenter__(self):
        headers = {
            "User-Agent": BROWSER_UA,
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Accept-Encoding": "gzip, deflate, br",
            "DNT": "1",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1",
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "none",
        }
        self.client = httpx.AsyncClient(
            headers=headers,
            follow_redirects=True,
            timeout=30.0,
        )
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.client:
            await self.client.aclose()

    async def get(self, path: str, **kwargs) -> httpx.Response:
        async with self.semaphore:
            url = f"{self.base_url}{path}" if path.startswith("/") else f"{self.base_url}/{path}"

            for attempt in range(3):
                try:
                    await self._rate_limit()
                    response = await self.client.get(url, **kwargs)
                    response.raise_for_status()
                    return response
                except httpx.HTTPStatusError as e:
                    if e.response.status_code in (429, 503, 504):
                        if attempt < 2:
                            wait_time = 2 ** attempt + random.uniform(0, 1)
                            await asyncio.sleep(wait_time)
                            continue
                    raise
                except httpx.RequestError:
                    if attempt < 2:
                        wait_time = 2 ** attempt + random.uniform(0, 1)
                        await asyncio.sleep(wait_time)
                        continue
                    raise

            raise RuntimeError(f"Failed to fetch {url} after 3 retries")

    async def _rate_limit(self):
        await asyncio.sleep(random.uniform(0.8, 1.5))
