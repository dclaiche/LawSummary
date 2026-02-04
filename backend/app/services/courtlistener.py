"""CourtListener REST API v4 client.

Free tier: 5,000 requests/day, token auth.
Filters to California courts: cal (Supreme Court), calctapp (Court of Appeal).
Rate limited to ~1 req/sec with token bucket.
"""

import asyncio
import time
import logging
from dataclasses import dataclass

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

BASE_URL = "https://www.courtlistener.com/api/rest/v4"
CA_COURTS = "cal calctapp"


@dataclass
class CourtListenerSearchHit:
    cluster_id: int
    opinion_id: int
    case_name: str
    court: str
    date_filed: str
    citation: str
    snippet: str
    absolute_url: str


@dataclass
class OpinionDetail:
    cluster_id: int
    case_name: str
    court: str
    date_filed: str
    citations: list[str]
    opinion_text: str
    absolute_url: str


class TokenBucket:
    """Simple token bucket rate limiter."""

    def __init__(self, rate: float = 1.0, capacity: int = 3) -> None:
        self.rate = rate
        self.capacity = capacity
        self.tokens = float(capacity)
        self.last_refill = time.monotonic()
        self._lock = asyncio.Lock()

    async def acquire(self) -> None:
        async with self._lock:
            now = time.monotonic()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            if self.tokens < 1:
                wait_time = (1 - self.tokens) / self.rate
                await asyncio.sleep(wait_time)
                self.tokens = 0
            else:
                self.tokens -= 1


class CourtListenerClient:
    def __init__(self, token: str | None = None) -> None:
        self.token = token or settings.courtlistener_token
        self._rate_limiter = TokenBucket(rate=1.0, capacity=3)
        self._client: httpx.AsyncClient | None = None

    async def _get_client(self) -> httpx.AsyncClient:
        if self._client is None or self._client.is_closed:
            headers = {"User-Agent": "LawSummary/1.0 (legal research tool)"}
            if self.token:
                headers["Authorization"] = f"Token {self.token}"
            self._client = httpx.AsyncClient(
                base_url=BASE_URL,
                headers=headers,
                timeout=30.0,
                follow_redirects=True,
            )
        return self._client

    async def close(self) -> None:
        if self._client and not self._client.is_closed:
            await self._client.aclose()
            self._client = None

    async def search(
        self,
        query: str,
        max_results: int = 10,
    ) -> list[CourtListenerSearchHit]:
        """Search for opinions in California courts.

        Args:
            query: Search query string
            max_results: Maximum results to return

        Returns:
            List of search hits with case info and snippets.
        """
        await self._rate_limiter.acquire()
        client = await self._get_client()

        try:
            resp = await client.get(
                "/search/",
                params={
                    "q": query,
                    "court": CA_COURTS,
                    "type": "o",
                    "highlight": "on",
                    "page_size": min(max_results, 20),
                },
            )
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "CourtListener API token is missing or invalid. "
                    "Set COURTLISTENER_TOKEN in backend/.env"
                )
            logger.error(f"CourtListener search error: {e}")
            return []
        except httpx.HTTPError as e:
            logger.error(f"CourtListener search error: {e}")
            return []

        results: list[CourtListenerSearchHit] = []
        for item in data.get("results", [])[:max_results]:
            # Extract citation string
            citations = []
            if item.get("citation"):
                citations = item["citation"] if isinstance(item["citation"], list) else [item["citation"]]
            citation_str = citations[0] if citations else ""

            # Extract snippet and opinion_id from opinions array (v4 API nests them there)
            snippet = ""
            opinion_id = 0
            opinions = item.get("opinions", [])
            if opinions and isinstance(opinions, list):
                snippet = opinions[0].get("snippet", "")
                opinion_id = opinions[0].get("id", 0)
            # Fallback to top-level fields if present
            if not snippet and item.get("snippet"):
                snippet = item["snippet"]

            results.append(
                CourtListenerSearchHit(
                    cluster_id=item.get("cluster_id", 0),
                    opinion_id=opinion_id,
                    case_name=item.get("caseName", item.get("case_name", "")),
                    court=item.get("court", ""),
                    date_filed=item.get("dateFiled", item.get("date_filed", "")),
                    citation=citation_str,
                    snippet=snippet[:1000],
                    absolute_url=item.get("absolute_url", ""),
                )
            )

        return results

    async def get_opinion(self, opinion_id: int) -> OpinionDetail | None:
        """Fetch full opinion detail by ID.

        Args:
            opinion_id: The opinion ID

        Returns:
            OpinionDetail with full text, or None if not found.
        """
        await self._rate_limiter.acquire()
        client = await self._get_client()

        try:
            resp = await client.get(f"/opinions/{opinion_id}/")
            resp.raise_for_status()
            data = resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "CourtListener API token is missing or invalid. "
                    "Set COURTLISTENER_TOKEN in backend/.env"
                )
            logger.error(f"CourtListener opinion fetch error: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"CourtListener opinion fetch error: {e}")
            return None

        # Get the opinion text from various possible fields
        opinion_text = (
            data.get("plain_text")
            or data.get("html_with_citations")
            or data.get("html")
            or data.get("xml_harvard")
            or ""
        )

        # If HTML, extract text
        if "<" in opinion_text:
            from bs4 import BeautifulSoup

            opinion_text = BeautifulSoup(opinion_text, "html.parser").get_text(
                separator="\n", strip=True
            )

        return OpinionDetail(
            cluster_id=data.get("cluster_id", 0),
            case_name=data.get("case_name", ""),
            court=data.get("court", ""),
            date_filed=data.get("date_filed", ""),
            citations=[],
            opinion_text=opinion_text[:10000],  # Cap at 10k chars
            absolute_url=data.get("absolute_url", ""),
        )

    async def get_cluster(self, cluster_id: int) -> dict | None:
        """Fetch cluster detail for case metadata.

        Args:
            cluster_id: The cluster ID

        Returns:
            Cluster data dict, or None if not found.
        """
        await self._rate_limiter.acquire()
        client = await self._get_client()

        try:
            resp = await client.get(f"/clusters/{cluster_id}/")
            resp.raise_for_status()
            return resp.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise ValueError(
                    "CourtListener API token is missing or invalid. "
                    "Set COURTLISTENER_TOKEN in backend/.env"
                )
            logger.error(f"CourtListener cluster fetch error: {e}")
            return None
        except httpx.HTTPError as e:
            logger.error(f"CourtListener cluster fetch error: {e}")
            return None
