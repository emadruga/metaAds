"""
competitors_scraper — Playwright-based Lambda for Meta Ad Library scraping.

Deployed as a container image (Chromium cannot fit in a ZIP-deployed Lambda).

Invocation payload (async, fire-and-forget from competitors Lambda):
    {
        "page_id":  "195588473845643",
        "country":  "US",             # optional, defaults to "US"
        "max_scroll": 6               # optional, defaults to 6
    }

What it does:
    1. Navigates to facebook.com/ads/library?view_all_page_id=<page_id>
    2. Scrolls to load all ad cards (T-6 algorithm)
    3. Extracts ad_id, start_date, is_active, body per card
    4. Converts PT-locale dates ("4 de fev de 2026") → ISO-8601 ("2026-02-04")
    5. Writes a CompetitorScrapeCache item to DynamoDB (TTL = 4 h)

On success the Lambda returns the scraped ads; since invocation is async the
caller (competitors Lambda) never sees the return value — DynamoDB is the
only communication channel.

Environment variables:
    DYNAMODB_TABLE — DynamoDB table name
    AWS_REGION     — injected by Lambda runtime
"""

from __future__ import annotations

import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timezone

import boto3

logger = logging.getLogger()
logger.setLevel(os.environ.get("LOG_LEVEL", "INFO"))

# ---------------------------------------------------------------------------
# DynamoDB helper (lightweight — no shared layer in container image)
# ---------------------------------------------------------------------------

_TABLE_NAME = os.environ.get("DYNAMODB_TABLE", "metaads-dev-table")
_REGION = os.environ.get("AWS_REGION", "us-east-1")
_SCRAPE_CACHE_TTL_SECONDS = 4 * 60 * 60  # 4 hours


def _get_table():
    dynamodb = boto3.resource("dynamodb", region_name=_REGION)
    return dynamodb.Table(_TABLE_NAME)


def _write_cache(page_id: str, ads: list) -> None:
    now_iso = datetime.now(tz=timezone.utc).isoformat().replace("+00:00", "Z")
    ttl = int(time.time()) + _SCRAPE_CACHE_TTL_SECONDS
    item = {
        "PK": f"SCRAPE_CACHE#{page_id}",
        "SK": "DATA",
        "entity_type": "SCRAPE_CACHE",
        "page_id": page_id,
        "ads": json.dumps(ads, ensure_ascii=False),
        "ad_count": len(ads),
        "scraped_at": now_iso,
        "ttl": ttl,
    }
    table = _get_table()
    table.put_item(Item=item)
    logger.info(f"Cache written: page_id={page_id}, ad_count={len(ads)}, ttl={ttl}")


# ---------------------------------------------------------------------------
# PT-locale date parser
# ---------------------------------------------------------------------------

_PT_MONTHS = {
    "jan": "01", "fev": "02", "mar": "03", "abr": "04",
    "mai": "05", "jun": "06", "jul": "07", "ago": "08",
    "set": "09", "out": "10", "nov": "11", "dez": "12",
}


def _parse_pt_date(raw: str | None) -> str | None:
    """
    Convert "4 de fev de 2026" → "2026-02-04".
    Returns None if the string cannot be parsed.
    """
    if not raw:
        return None
    raw = raw.strip().lower()
    # Pattern: "<day> de <month-abbr> de <year>"
    m = re.match(r"(\d{1,2})\s+de\s+(\w+)\s+de\s+(\d{4})", raw)
    if not m:
        return None
    day, month_abbr, year = m.group(1), m.group(2), m.group(3)
    month = _PT_MONTHS.get(month_abbr[:3])
    if not month:
        return None
    return f"{year}-{month}-{int(day):02d}"


# ---------------------------------------------------------------------------
# Playwright card-extraction JS (same logic as T-6 feasibility test)
# ---------------------------------------------------------------------------

_CARD_SELECTOR = "div.xh8yej3"

_EXTRACT_JS = r"""
() => {
    const cards = [...document.querySelectorAll('div.xh8yej3')].filter(el =>
        el.innerText && el.innerText.includes('Identificação da biblioteca')
    );

    const seen = new Set();
    const results = [];

    for (const card of cards) {
        const text = card.innerText;

        const idMatch   = text.match(/Identificação da biblioteca:\s*(\d+)/);
        const dateMatch = text.match(/Veiculação iniciada em\s+(.+?)[\n]/);
        const isActive  = text.includes('Ativo');

        // Body: first non-empty line after "Patrocinado"
        const lines  = text.split('\n').map(l => l.trim()).filter(Boolean);
        const patIdx = lines.findIndex(l => l === 'Patrocinado');
        const body   = (patIdx >= 0 && patIdx + 1 < lines.length)
                       ? lines[patIdx + 1] : null;

        const ad_id = idMatch ? idMatch[1] : null;
        if (!ad_id || seen.has(ad_id)) continue;
        seen.add(ad_id);

        results.push({
            ad_id,
            start_date_raw: dateMatch ? dateMatch[1].trim() : null,
            is_active:      isActive,
            body:           body,
        });
    }
    return results;
}
"""


# ---------------------------------------------------------------------------
# Core scrape function
# ---------------------------------------------------------------------------

async def _scrape(page_id: str, country: str, max_scroll: int) -> list:
    """
    Run the Playwright T-6 scrape and return a list of frontend-compatible
    ad dicts.
    """
    from playwright.async_api import async_playwright

    url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=all&ad_type=all&country={country}"
        f"&view_all_page_id={page_id}"
    )

    logger.info(f"Scraping page_id={page_id} country={country} url={url[:80]}...")

    ads: list = []

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(
            headless=True,
            args=[
                "--no-sandbox",
                "--disable-dev-shm-usage",
                "--disable-gpu",
                "--single-process",
                "--disable-blink-features=AutomationControlled",
            ],
        )
        context = await browser.new_context(
            locale="pt-BR",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )

        # Disable webdriver flag to avoid detection
        await context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )

        page = await context.new_page()

        try:
            await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            await asyncio.sleep(3)

            # Login wall check
            body_text = await page.evaluate("() => document.body?.innerText ?? ''")
            if any(s in body_text.lower() for s in ["faça login", "log in to facebook"]):
                logger.error("LOGIN WALL detected — scrape aborted")
                return []

            # Wait for first card
            try:
                await page.wait_for_selector(_CARD_SELECTOR, timeout=20_000)
            except Exception:
                logger.warning("Card selector not found after 20s")
                return []

            try:
                await page.wait_for_load_state("networkidle", timeout=15_000)
            except Exception:
                pass  # Proceed anyway; network may stay active due to lazy loading

            # Scroll to load all ads
            prev_count = 0
            for i in range(max_scroll):
                await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                cur_count = await page.evaluate(
                    f"() => document.querySelectorAll('{_CARD_SELECTOR}').length"
                )
                logger.info(f"Scroll {i+1}/{max_scroll}: {cur_count} cards in DOM")
                if cur_count == prev_count:
                    logger.info("No new cards — stopping scroll")
                    break
                prev_count = cur_count

            # Extract raw card data via JS
            raw_cards = await page.evaluate(_EXTRACT_JS)
            logger.info(f"Extracted {len(raw_cards)} unique raw cards")

            # Convert to frontend-compatible format
            now_utc = datetime.now(tz=timezone.utc)
            for card in raw_cards:
                start_iso = _parse_pt_date(card.get("start_date_raw"))
                days_active: int | None = None
                if start_iso:
                    try:
                        start_dt = datetime.fromisoformat(start_iso).replace(tzinfo=timezone.utc)
                        if card.get("is_active"):
                            days_active = max(0, (now_utc - start_dt).days)
                        # For inactive, we don't know the end date from the scrape
                    except Exception:
                        pass

                ads.append({
                    "meta_ad_id":   card["ad_id"],
                    "page_id":      page_id,
                    "page_name":    "",        # populated by caller from competitor record
                    "body":         card.get("body") or "",
                    "headline":     "",
                    "description":  "",
                    "link_caption": "",
                    "start_date":   start_iso,
                    "end_date":     None,
                    "is_active":    card.get("is_active", False),
                    "days_active":  days_active,
                    "snapshot_url": None,
                    "platforms":    [],
                    "media_type":   "OTHER",
                    "spend":        None,
                    "impressions":  None,
                    "data_source":  "playwright",
                })

        finally:
            await context.close()
            await browser.close()

    return ads


# ---------------------------------------------------------------------------
# Lambda entry point
# ---------------------------------------------------------------------------

def handler(event: dict, context) -> dict:
    """
    Invoked asynchronously by the competitors Lambda when Graph API results
    are insufficient (< 5 results or all inactive).

    Event schema:
        {
            "page_id":    "195588473845643",
            "country":    "US",           # optional
            "max_scroll": 6               # optional
        }
    """
    page_id = str(event.get("page_id", "")).strip()
    country = str(event.get("country", "US")).strip().upper() or "US"
    max_scroll = int(event.get("max_scroll", 6))

    if not page_id:
        logger.error("handler called without page_id — aborting")
        return {"success": False, "error": "page_id required"}

    logger.info(f"=== Competitors Scraper: page_id={page_id} country={country} ===")

    try:
        ads = asyncio.run(_scrape(page_id, country, max_scroll))
    except Exception as exc:
        logger.error(f"Playwright scrape failed: {exc}", exc_info=True)
        return {"success": False, "error": str(exc), "page_id": page_id}

    if ads:
        try:
            _write_cache(page_id, ads)
        except Exception as exc:
            logger.error(f"DynamoDB write failed: {exc}", exc_info=True)
            return {"success": False, "error": f"Cache write failed: {exc}", "page_id": page_id}
    else:
        logger.warning(f"Scrape returned 0 ads for page_id={page_id}")

    active = sum(1 for a in ads if a.get("is_active"))
    logger.info(
        f"=== Done: {len(ads)} ads ({active} active) for page_id={page_id} ==="
    )
    return {
        "success": True,
        "page_id": page_id,
        "ad_count": len(ads),
        "active_count": active,
    }
