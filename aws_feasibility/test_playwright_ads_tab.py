#!/usr/bin/env python3
"""
T-6 — Playwright Ads Tab Scrape

Tests whether Playwright can navigate to a competitor's Meta Ad Library
page and scrape ad cards from the Ads tab — specifically for brands
whose ads the Graph API cannot return (e.g. US commercial advertisers).

What it extracts per card:
  - ad_id        (library ID shown on card)
  - start_date   (raw PT string, e.g. "4 de fev de 2026")
  - is_active    (True if "Ativo" badge present)
  - body         (ad copy text)

Ground case:
  Marcella NYC — page_id 195588473845643, country US
  Expected: ~55 results, all/most active, ad copy in English

Usage:
    # Headed (default)
    python aws_feasibility/test_playwright_ads_tab.py

    # Headless
    python aws_feasibility/test_playwright_ads_tab.py --headless

    # Different page / country
    python aws_feasibility/test_playwright_ads_tab.py --page-id 711978348674579 --country BR

    # Scroll further to load more ads
    python aws_feasibility/test_playwright_ads_tab.py --max-scroll 10
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

DEFAULT_PAGE_ID = "195588473845643"   # Marcella NYC
DEFAULT_COUNTRY = "US"
RESULTS_FILE    = Path("t6_ads_results.json")

# Card selector confirmed via Chrome extension inspection 2026-03-20
CARD_SELECTOR = "div.xh8yej3"

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def _extract_cards_js() -> str:
    """
    JS snippet that runs in the page context and returns a list of ad dicts.
    Runs entirely client-side — no extra network calls.
    """
    return r"""
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
            start_date: dateMatch ? dateMatch[1].trim() : null,
            is_active:  isActive,
            body:       body,
        });
    }
    return results;
}
"""


# ---------------------------------------------------------------------------
# Core test
# ---------------------------------------------------------------------------

async def scrape_ads(
    page_id:    str,
    country:    str,
    headless:   bool,
    max_scroll: int,
) -> dict:
    from playwright.async_api import async_playwright

    url = (
        f"https://www.facebook.com/ads/library/"
        f"?active_status=all&ad_type=all&country={country}"
        f"&view_all_page_id={page_id}"
    )

    result = {
        "page_id":   page_id,
        "country":   country,
        "url":       url,
        "ads":       [],
        "pass":      [],
        "fail":      [],
        "warn":      [],
    }

    def _p(step, detail=""):
        result["pass"].append(step)
        _log(f"  PASS  [{step}] {detail}")

    def _f(step, detail=""):
        result["fail"].append(step)
        _log(f"  FAIL  [{step}] {detail}", "ERROR")

    def _w(step, detail=""):
        result["warn"].append(step)
        _log(f"  WARN  [{step}] {detail}", "WARN")

    async with async_playwright() as pw:
        browser = await pw.chromium.launch(headless=headless)
        context = await browser.new_context(
            locale="pt-BR",
            viewport={"width": 1440, "height": 900},
            user_agent=(
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/122.0.0.0 Safari/537.36"
            ),
        )
        page = await context.new_page()

        try:
            # ---- Step A: navigate ----------------------------------------
            _log(f"Step A — navigating to {url[:80]}...")
            try:
                await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
                _p("A_navigate", f"loaded: {page.url[:80]}")
            except Exception as exc:
                _f("A_navigate", str(exc))
                return result

            await asyncio.sleep(2)

            # ---- Step B: login wall check --------------------------------
            page_text = await page.evaluate("() => document.body?.innerText ?? ''")
            if any(s in page_text.lower() for s in ["faça login", "log in to facebook"]):
                _f("B_no_login_wall", "LOGIN WALL detected")
                return result
            _p("B_no_login_wall", "no login wall")

            # ---- Step C: wait for first card -----------------------------
            _log("Step C — waiting for ad cards...")
            try:
                await page.wait_for_selector(CARD_SELECTOR, timeout=20_000)
                _p("C_cards_loaded", f"selector '{CARD_SELECTOR}' found")
            except Exception:
                _w("C_cards_loaded", "card selector not found after 20s")

            await page.wait_for_load_state("networkidle", timeout=15_000)

            # ---- Step D: result count banner -----------------------------
            count_text = await page.evaluate(
                "() => document.body.innerText.match(/~?(\\d+)\\s*resultados/)?.[0] || ''"
            )
            if count_text:
                _p("D_result_count", f"banner: '{count_text}'")
            else:
                _w("D_result_count", "result count banner not found")

            # ---- Step E: scroll to load more ads -------------------------
            _log(f"Step E — scrolling up to {max_scroll} times to load more ads...")
            prev_count = 0
            for i in range(max_scroll):
                await page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
                await asyncio.sleep(2)
                cur_count = await page.evaluate(
                    f"() => document.querySelectorAll('{CARD_SELECTOR}').length"
                )
                _log(f"  scroll {i+1}/{max_scroll}: {cur_count} cards in DOM")
                if cur_count == prev_count:
                    _log("  no new cards loaded — stopping scroll")
                    break
                prev_count = cur_count

            # ---- Step F: extract cards -----------------------------------
            _log("Step F — extracting ad cards...")
            ads = await page.evaluate(_extract_cards_js())
            result["ads"] = ads

            if ads:
                active  = sum(1 for a in ads if a["is_active"])
                inactive = len(ads) - active
                _p("F_extraction", f"{len(ads)} unique ads ({active} active, {inactive} inactive)")
                _log(f"  Sample ads:")
                for ad in ads[:3]:
                    _log(f"    [{ad['ad_id']}] {ad['start_date']} | {ad['body'][:60] if ad['body'] else '(no body)'}...")
            else:
                _f("F_extraction", "0 ads extracted")

            # ---- Step G: validate ----------------------------------------
            _log("Step G — validating...")
            if len(ads) >= 10:
                _p("G_min_ads", f"{len(ads)} ads ≥ threshold of 10")
            elif len(ads) > 0:
                _w("G_min_ads", f"only {len(ads)} ads found (expected ≥ 10 for Marcella NYC)")
            else:
                _f("G_min_ads", "0 ads — nothing scraped")

            active_ratio = sum(1 for a in ads if a["is_active"]) / max(len(ads), 1)
            if active_ratio > 0.5:
                _p("G_mostly_active", f"{active_ratio*100:.0f}% active")
            else:
                _w("G_mostly_active", f"only {active_ratio*100:.0f}% active")

            ads_with_body = sum(1 for a in ads if a["body"])
            if ads_with_body > 0:
                _p("G_has_body_text", f"{ads_with_body}/{len(ads)} ads have body text")
            else:
                _w("G_has_body_text", "no body text extracted from any ad")

        finally:
            await context.close()
            await browser.close()

    return result


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="T-6 Playwright Ads Tab Scrape")
    parser.add_argument("--page-id",   default=DEFAULT_PAGE_ID)
    parser.add_argument("--country",   default=DEFAULT_COUNTRY)
    parser.add_argument("--headless",  action="store_true")
    parser.add_argument("--max-scroll", type=int, default=5,
                        help="Number of scroll attempts to load more ads (default: 5)")
    args = parser.parse_args()

    _log("=" * 60)
    _log("T-6 — Playwright Ads Tab Scrape")
    _log(f"  page_id  : {args.page_id}")
    _log(f"  country  : {args.country}")
    _log(f"  headless : {args.headless}")
    _log(f"  max_scroll: {args.max_scroll}")
    _log("=" * 60)

    result = await scrape_ads(
        page_id    = args.page_id,
        country    = args.country,
        headless   = args.headless,
        max_scroll = args.max_scroll,
    )

    _log("")
    _log("=" * 60)
    _log("SUMMARY")
    _log("=" * 60)
    status = "OK " if not result["fail"] else "ERR"
    _log(f"  [{status}] {len(result['pass'])} pass / {len(result['fail'])} fail / {len(result['warn'])} warn")
    _log(f"  Total ads scraped: {len(result['ads'])}")

    RESULTS_FILE.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    _log(f"  Results → {RESULTS_FILE}")

    sys.exit(1 if result["fail"] else 0)


if __name__ == "__main__":
    asyncio.run(main())
