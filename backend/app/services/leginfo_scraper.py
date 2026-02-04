"""California LegInfo scraping service.

Dual strategy:
1. Direct section lookup via httpx + BeautifulSoup (fast, when we know code+section)
2. Keyword search via Playwright (JSF form requires real browser)

Rate limited: max 2 concurrent requests, 1-2s delay between requests.
"""

import asyncio
import re
import logging
from dataclasses import dataclass
from urllib.parse import quote

import httpx
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

BASE_URL = "https://leginfo.legislature.ca.gov"
SECTION_URL = f"{BASE_URL}/faces/codes_displaySection.xhtml"
SEARCH_URL = f"{BASE_URL}/faces/codes_displayText.xhtml"

# Rate limiting
_semaphore = asyncio.Semaphore(2)
_last_request_time = 0.0


@dataclass
class LegInfoSection:
    code: str
    section: str
    title: str
    full_text: str
    url: str


@dataclass
class LegInfoSearchResult:
    code: str
    section: str
    title: str
    snippet: str
    url: str


async def _rate_limit() -> None:
    """Enforce minimum 1.5s between requests."""
    import time

    global _last_request_time
    now = time.monotonic()
    elapsed = now - _last_request_time
    if elapsed < 1.5:
        await asyncio.sleep(1.5 - elapsed)
    _last_request_time = time.monotonic()


async def lookup_section(code: str, section: str) -> LegInfoSection | None:
    """Fetch a specific statute section by code and section number.

    Args:
        code: Law code abbreviation (e.g., "PEN", "CIV", "VEH")
        section: Section number (e.g., "240", "1708.5")

    Returns:
        LegInfoSection with full text, or None if not found.
    """
    async with _semaphore:
        await _rate_limit()
        url = f"{SECTION_URL}?sectionNum={quote(section)}&lawCode={quote(code)}"

        try:
            async with httpx.AsyncClient(
                timeout=30.0,
                follow_redirects=True,
                headers={"User-Agent": "LawSummary/1.0 (legal research tool)"},
            ) as client:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"LegInfo lookup failed: {resp.status_code} for {code} {section}")
                    return None

                return _parse_section_page(resp.text, code, section, url)
        except httpx.HTTPError as e:
            logger.error(f"LegInfo HTTP error: {e}")
            return None


def _parse_section_page(html: str, code: str, section: str, url: str) -> LegInfoSection | None:
    """Parse a leginfo section display page."""
    soup = BeautifulSoup(html, "html.parser")

    # The statute text is typically in a div with id containing 'codeLaw'
    # or in the main content area
    content_div = soup.find("div", id=lambda x: x and "codeLaw" in x if x else False)
    if not content_div:
        content_div = soup.find("div", {"id": "manylawsections"})
    if not content_div:
        # Try finding the main content area
        content_div = soup.find("div", class_="law-section-body")

    if not content_div:
        # Fallback: look for any content that contains section text
        for div in soup.find_all("div"):
            text = div.get_text(strip=True)
            if section in text and len(text) > 100:
                content_div = div
                break

    if not content_div:
        logger.warning(f"Could not find statute text for {code} {section}")
        return None

    full_text = content_div.get_text(separator="\n", strip=True)

    # Extract title from heading or first line
    title_elem = soup.find("span", class_="law-section-heading")
    if not title_elem:
        title_elem = soup.find("h3")
    title = title_elem.get_text(strip=True) if title_elem else f"{code} Section {section}"

    return LegInfoSection(
        code=code,
        section=section,
        title=title,
        full_text=full_text,
        url=url,
    )


async def keyword_search(keywords: str, max_results: int = 10) -> list[LegInfoSearchResult]:
    """Search leginfo by keywords using Playwright (headless browser).

    The leginfo site uses JSF (JavaServer Faces) which requires a real browser
    to submit forms and navigate results.

    Args:
        keywords: Search query string
        max_results: Maximum number of results to return

    Returns:
        List of LegInfoSearchResult with code, section, snippet.
    """
    async with _semaphore:
        await _rate_limit()

        try:
            return await _playwright_keyword_search(keywords, max_results)
        except Exception as e:
            logger.error(f"Playwright search failed for '{keywords}': {e}")
            # Fallback to httpx-based search attempt
            return await _httpx_keyword_search(keywords, max_results)


async def _playwright_keyword_search(
    keywords: str, max_results: int
) -> list[LegInfoSearchResult]:
    """Use Playwright to search leginfo's keyword search form."""
    from playwright.async_api import async_playwright

    results: list[LegInfoSearchResult] = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        try:
            page = await browser.new_page()
            await page.goto(
                f"{BASE_URL}/faces/codes_displayText.xhtml",
                timeout=30000,
            )

            # Fill the keyword search input
            search_input = page.locator("input[id*='keyword']").first
            if await search_input.count() == 0:
                # Try alternative selectors
                search_input = page.locator("input[type='text']").first

            await search_input.fill(keywords)

            # Click search button
            search_btn = page.locator("input[type='submit'][value*='Search'], button[id*='search']").first
            if await search_btn.count() == 0:
                search_btn = page.locator("input[type='submit']").first

            await search_btn.click()
            await page.wait_for_load_state("networkidle", timeout=15000)

            # Parse results
            result_links = page.locator("a[href*='codes_displaySection']")
            count = min(await result_links.count(), max_results)

            for i in range(count):
                link = result_links.nth(i)
                href = await link.get_attribute("href") or ""
                text = await link.text_content() or ""

                # Extract code and section from URL or text
                code_match = re.search(r"lawCode=(\w+)", href)
                section_match = re.search(r"sectionNum=([\d.]+)", href)

                if code_match and section_match:
                    # Get snippet from surrounding text
                    parent = link.locator("..")
                    snippet = await parent.text_content() or text

                    results.append(
                        LegInfoSearchResult(
                            code=code_match.group(1),
                            section=section_match.group(1),
                            title=text.strip(),
                            snippet=snippet.strip()[:500],
                            url=f"{BASE_URL}/{href}" if not href.startswith("http") else href,
                        )
                    )
        finally:
            await browser.close()

    return results


async def _httpx_keyword_search(
    keywords: str, max_results: int
) -> list[LegInfoSearchResult]:
    """Fallback keyword search using httpx (may not work well with JSF)."""
    results: list[LegInfoSearchResult] = []

    try:
        async with httpx.AsyncClient(
            timeout=30.0,
            follow_redirects=True,
            headers={"User-Agent": "LawSummary/1.0 (legal research tool)"},
        ) as client:
            # Try the search URL with query parameters
            resp = await client.get(
                f"{BASE_URL}/faces/codes_displayText.xhtml",
                params={"lawCode": "ALL", "keyword": keywords},
            )
            if resp.status_code != 200:
                return results

            soup = BeautifulSoup(resp.text, "html.parser")

            # Look for result links
            for link in soup.find_all("a", href=re.compile(r"codes_displaySection")):
                href = link.get("href", "")
                text = link.get_text(strip=True)

                code_match = re.search(r"lawCode=(\w+)", href)
                section_match = re.search(r"sectionNum=([\d.]+)", href)

                if code_match and section_match:
                    parent_text = link.parent.get_text(strip=True) if link.parent else text
                    results.append(
                        LegInfoSearchResult(
                            code=code_match.group(1),
                            section=section_match.group(1),
                            title=text,
                            snippet=parent_text[:500],
                            url=f"{BASE_URL}/{href}" if not href.startswith("http") else href,
                        )
                    )

                if len(results) >= max_results:
                    break

    except httpx.HTTPError as e:
        logger.error(f"httpx search fallback failed: {e}")

    return results


# In-memory cache for sections fetched during a run
_section_cache: dict[str, LegInfoSection | None] = {}


async def lookup_section_cached(code: str, section: str) -> LegInfoSection | None:
    """Lookup with per-process caching."""
    key = f"{code}:{section}"
    if key not in _section_cache:
        _section_cache[key] = await lookup_section(code, section)
    return _section_cache[key]


def clear_cache() -> None:
    """Clear the section cache."""
    _section_cache.clear()
