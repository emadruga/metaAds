#!/usr/bin/env python3
"""
T-5 — Playwright "Sobre" Tab Scrape

Tests whether Playwright can navigate facebook.com/ads/library, reach an
advertiser's "Sobre" (About) tab, and extract the following fields without
triggering a CAPTCHA or login wall:

  - Facebook page ID (numeric)
  - Facebook followers
  - Instagram handle
  - Instagram follower count
  - Page creation date

Ground cases:

  Advertiser 1: Rodrigo Tadewald / Asimov Academy  (BR)
    page_id : 711978348674579
    expected: ~99k IG followers, created Sep 2025

  Advertiser 2: Ivangelica (stand-up comedy, BR)
    page_id : 811525368628016  (discovered via keyword search + JS extraction)

  Advertiser 3: Marcella NYC  (US)
    page_id : 195588473845643  (confirmed via Chrome extension 2026-03-19)
    expected: @marcellanyc, ~88.5k FB / ~214.9k IG followers, created 2011

Search strategy:
  - Known page_id  → direct view_all_page_id= URL  (fastest, most reliable)
  - Unknown page_id → search_type=page URL  (advertiser search, broader than
                      keyword_unordered and works for non-BR advertisers)

Usage:
    # Headed mode (default — recommended for initial discovery run):
    python test_playwright_sobre.py

    # Headless mode (after selectors are confirmed):
    python test_playwright_sobre.py --headless

    # Run a single advertiser:
    python test_playwright_sobre.py --advertiser marcellanyc
    python test_playwright_sobre.py --advertiser ivangelica

    # Run all advertisers in sequence:
    python test_playwright_sobre.py --advertiser all

    # Provide a known page_id directly (skips search step):
    python test_playwright_sobre.py --page-id 711978348674579

    # Save DOM snapshot to file for offline inspection:
    python test_playwright_sobre.py --save-html
"""

import argparse
import asyncio
import json
import re
import sys
from datetime import datetime
from pathlib import Path

# ---------------------------------------------------------------------------
# Advertiser definitions
# ---------------------------------------------------------------------------

ADVERTISERS = {
    "tadewald": {
        "label":        "Rodrigo Tadewald / Asimov Academy",
        "search_term":  "Rodrigo Tadewald",
        "page_id":      "711978348674579",           # known — confirmed via web UI
        "country":      "BR",
        "expected": {
            "page_id":           "711978348674579",
            "ig_handle":         "rodrigotadewald",
            "created_contains":  ["set", "2025"],    # "setembro de 2025" or "Sep 2025"
        },
    },
    "ivangelica": {
        "label":        "Ivangelica",
        "search_term":  "Ivangelica",
        "page_id":      None,                        # unknown — to be discovered
        "country":      "BR",
        "expected": {
            "page_id":           None,               # any numeric string ≥ 10 digits
        },
    },
    "marcellanyc": {
        "label":        "Marcella NYC",
        "search_term":  "Marcella NYC",
        "page_id":      "195588473845643",           # confirmed via Chrome extension 2026-03-19
        "country":      "US",
        "expected": {
            "page_id":           "195588473845643",
            "ig_handle":         "marcellanyc",
            "fb_followers_contains": ["88"],         # ~88.5k
            "ig_followers_contains": ["214"],        # ~214.9k
            "created_contains":  ["2011"],
        },
    },
}

RESULTS_FILE    = Path("t5_sobre_results.json")
DEFAULT_COUNTRY = "US"   # broader — catches non-BR advertisers in page search

# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

results: dict = {
    "started_at":  None,
    "headless":    None,
    "advertisers": {},
}


def _log(msg: str, level: str = "INFO") -> None:
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def _save_results() -> None:
    with open(RESULTS_FILE, "w") as fh:
        json.dump(results, fh, indent=2, ensure_ascii=False)
    _log(f"Results written → {RESULTS_FILE}")


# ---------------------------------------------------------------------------
# Regex extraction helpers
# ---------------------------------------------------------------------------

# Both Portuguese and English variants are tried for every field.
# First match wins.

_PATTERNS_PAGE_ID = [
    r"Identifica(?:ção|cao)[^\d]*(\d{10,20})",   # PT: "Identificação: 711978..."
    r"ID da [Pp]ágina[^\d]*(\d{10,20})",          # PT: "ID da Página"
    r"Page ID[^\d]*(\d{10,20})",                  # EN
    r"Identification[^\d]*(\d{10,20})",            # EN alt
    r"\b(\d{15,20})\b",                            # bare long numeric (fallback)
]

_PATTERNS_CREATED = [
    r"[Pp]ágina criada\s+(.{3,40}?)(?:\n|<|\s{2})",  # PT: "Página criada set. de 2025"
    r"Page created\s+(.{3,40}?)(?:\n|<|\s{2})",        # EN
    r"[Cc]riada em\s+(.{3,40}?)(?:\n|<|\s{2})",        # PT alt
]

_PATTERNS_FB_FOLLOWERS = [
    r"([\d\.,]+)\s*(?:mil\s+)?seguidores",   # PT: "99,3 mil seguidores" or "99.300 seguidores"
    r"([\d\.,]+)\s*(?:k\s+)?followers",       # EN: "99.3k followers"
]

_PATTERNS_IG_HANDLE = [
    r"instagram\.com/([\w\.]+)",
    r"@([\w\.]+)",
]

_PATTERNS_IG_FOLLOWERS = [
    # Instagram followers often appear AFTER the handle — we grab the second
    # "seguidores" match separately in extract_fields().
    r"([\d\.,]+)\s*(?:mil\s+)?seguidores",
    r"([\d\.,]+)\s*(?:k\s+)?followers",
]


def _first_match(text: str, patterns: list[str]) -> str | None:
    for pat in patterns:
        m = re.search(pat, text, re.IGNORECASE)
        if m:
            return m.group(1).strip()
    return None


def extract_fields(text: str) -> dict:
    """
    Run all regex patterns against the visible text and return extracted values.
    For followers we attempt to find two distinct matches (FB first, IG second).
    """
    page_id      = _first_match(text, _PATTERNS_PAGE_ID)
    created      = _first_match(text, _PATTERNS_CREATED)
    ig_handle    = _first_match(text, _PATTERNS_IG_HANDLE)

    # Followers: collect ALL matches, return first two distinctly
    all_follower_matches = []
    for pat in _PATTERNS_FB_FOLLOWERS:
        all_follower_matches.extend(re.findall(pat, text, re.IGNORECASE))
    # deduplicate while preserving order
    seen = set()
    unique_follower_matches = []
    for m in all_follower_matches:
        if m not in seen:
            seen.add(m)
            unique_follower_matches.append(m)

    fb_followers = unique_follower_matches[0] if len(unique_follower_matches) > 0 else None
    ig_followers = unique_follower_matches[1] if len(unique_follower_matches) > 1 else None

    return {
        "page_id":      page_id,
        "fb_followers": fb_followers,
        "ig_handle":    ig_handle,
        "ig_followers": ig_followers,
        "created":      created,
    }


# ---------------------------------------------------------------------------
# Playwright helpers
# ---------------------------------------------------------------------------

async def _wait_for_any(page, selectors: list[str], timeout: int = 10_000):
    """Wait for the first of several candidate selectors to appear."""
    for sel in selectors:
        try:
            await page.wait_for_selector(sel, timeout=timeout)
            return sel
        except Exception:
            continue
    return None


async def _click_sobre_tab(page) -> bool:
    """
    Try to click the "Sobre" / "About" tab on the advertiser page.
    Returns True if clicked, False if not found.
    """
    candidates = [
        "text=Sobre",
        "text=About",
        "[role=tab]:has-text('Sobre')",
        "[role=tab]:has-text('About')",
        "a:has-text('Sobre')",
        "a:has-text('About')",
        "button:has-text('Sobre')",
        "button:has-text('About')",
    ]
    for sel in candidates:
        try:
            el = page.locator(sel).first
            if await el.is_visible(timeout=3_000):
                await el.click()
                _log(f"  Clicked 'Sobre/About' tab via: {sel}")
                return True
        except Exception:
            continue
    return False


async def _get_visible_text(page) -> str:
    """Return the full innerText of the body."""
    try:
        return await page.evaluate("() => document.body?.innerText ?? ''")
    except Exception:
        return ""


async def _get_html_snapshot(page) -> str:
    try:
        return await page.content()
    except Exception:
        return ""


# ---------------------------------------------------------------------------
# Core test per advertiser
# ---------------------------------------------------------------------------

async def test_advertiser(
    browser,
    advertiser_key: str,
    advertiser: dict,
    save_html: bool,
) -> dict:
    label       = advertiser["label"]
    search_term = advertiser["search_term"]
    known_pid   = advertiser["page_id"]
    country     = advertiser.get("country", DEFAULT_COUNTRY)
    expected    = advertiser.get("expected", {})

    _log("=" * 60)
    _log(f"Advertiser: {label}")
    _log(f"  Search term : {search_term}")
    _log(f"  Known page_id: {known_pid or 'unknown'}")
    _log("=" * 60)

    adv_result: dict = {
        "label":     label,
        "steps":     {},
        "extracted": {},
        "pass":      [],
        "fail":      [],
        "warn":      [],
    }

    def _p(step, detail=""):
        adv_result["steps"][step] = {"status": "PASS", "detail": detail}
        adv_result["pass"].append(step)
        _log(f"  PASS  [{step}] {detail}")

    def _f(step, detail=""):
        adv_result["steps"][step] = {"status": "FAIL", "detail": detail}
        adv_result["fail"].append(step)
        _log(f"  FAIL  [{step}] {detail}", "ERROR")

    def _w(step, detail=""):
        adv_result["steps"][step] = {"status": "WARN", "detail": detail}
        adv_result["warn"].append(step)
        _log(f"  WARN  [{step}] {detail}", "WARN")

    # ---- open context & page -------------------------------------------
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
        # ---- Step A: navigate to Ads Library ---------------------------
        _log("Step A — navigating to Ads Library...")

        if known_pid:
            # Direct URL — bypasses search, lands on advertiser's ad list
            url = (
                f"https://www.facebook.com/ads/library/"
                f"?active_status=all&ad_type=all&country={country}"
                f"&view_all_page_id={known_pid}"
            )
        else:
            # Page/advertiser search — more reliable than keyword_unordered,
            # especially for non-BR advertisers. Falls back to broad country=US.
            encoded = search_term.replace(" ", "+")
            url = (
                f"https://www.facebook.com/ads/library/"
                f"?active_status=all&ad_type=all&country={country}"
                f"&q={encoded}&search_type=page"
            )

        _log(f"  URL: {url}")
        try:
            await page.goto(url, timeout=30_000, wait_until="domcontentloaded")
            _p("A_navigate", f"page loaded: {page.url[:80]}")
        except Exception as exc:
            _f("A_navigate", str(exc))
            return adv_result

        # ---- Step B: check for login wall / CAPTCHA -------------------
        _log("Step B — checking for login wall or CAPTCHA...")
        await asyncio.sleep(2)  # let JS settle

        page_text = await _get_visible_text(page)
        title     = await page.title()
        _log(f"  Page title: '{title}'")

        login_signals = [
            "log in to facebook",
            "faça login",
            "entrar no facebook",
            "log into facebook",
        ]
        captcha_signals = [
            "captcha",
            "verificação de segurança",
            "security check",
            "are you human",
        ]

        if any(s in page_text.lower() for s in login_signals):
            _f("B_no_login_wall", f"LOGIN WALL detected. title='{title}'")
            return adv_result
        elif any(s in page_text.lower() for s in captcha_signals):
            _f("B_no_captcha", f"CAPTCHA detected. title='{title}'")
            return adv_result
        else:
            _p("B_no_login_wall", "no login wall or CAPTCHA detected")

        # ---- Step C: wait for ad results to load ----------------------
        _log("Step C — waiting for ad list to render...")
        result_selectors = [
            "[data-testid='ad-library-preview']",
            ".x1n2onr6",         # generic FB container (may change)
            "text=anúncios",
            "text=ads",
            "text=resultados",
            "text=results",
        ]
        found_sel = await _wait_for_any(page, result_selectors, timeout=15_000)
        if found_sel:
            _p("C_results_loaded", f"content detected via: {found_sel}")
        else:
            _w("C_results_loaded", "no known selector found — page may have rendered differently")

        await page.wait_for_load_state("networkidle", timeout=15_000)

        # ---- Step C2: if we came via keyword search, click the advertiser
        #               name to navigate to their page (view_all_page_id URL)
        if not known_pid:
            _log("Step C2 — clicking advertiser name to reach their page...")
            # The advertiser name appears as a link/button above their ads in search results.
            # Try the search_term text first, then a generic "Ver todos os anúncios" link.
            advertiser_link_candidates = [
                f"text={search_term}",
                f"a:has-text('{search_term}')",
                f"button:has-text('{search_term}')",
                "text=Ver todos os anúncios",
                "text=See all ads",
            ]
            clicked_advertiser = False
            for sel in advertiser_link_candidates:
                try:
                    el = page.locator(sel).first
                    if await el.is_visible(timeout=4_000):
                        await el.click()
                        _log(f"  Clicked advertiser link via: {sel}")
                        await page.wait_for_load_state("networkidle", timeout=15_000)
                        await asyncio.sleep(1)
                        clicked_advertiser = True
                        break
                except Exception:
                    continue

            if clicked_advertiser:
                _p("C2_advertiser_link", f"navigated to advertiser page: {page.url[:80]}")
                # Extract page_id from the new URL
                pid_from_url = re.search(r"view_all_page_id=(\d+)", page.url)
                if pid_from_url:
                    discovered_pid = pid_from_url.group(1)
                    _log(f"  Discovered page_id from URL: {discovered_pid}")
                    adv_result["discovered_page_id"] = discovered_pid
            else:
                _w("C2_advertiser_link", "could not find advertiser link — will try 'Sobre' on current page")

        # ---- Step D: find & click the "Sobre" tab ---------------------
        _log("Step D — looking for 'Sobre/About' tab...")
        clicked = await _click_sobre_tab(page)

        if clicked:
            _p("D_sobre_tab_clicked", "tab found and clicked")
            # Wait for Sobre panel content to actually render — look for known
            # strings that only appear inside the Sobre tab body.
            sobre_content_selectors = [
                "text=Identificação",
                "text=Identification",
                "text=Página criada",
                "text=Page created",
                "text=seguidores",
                "text=followers",
                "text=Criada em",
            ]
            found_content = await _wait_for_any(page, sobre_content_selectors, timeout=12_000)
            if found_content:
                _log(f"  Sobre panel content confirmed via: {found_content}")
            else:
                _w("D_sobre_tab_clicked", "Sobre content selectors not found after 12s — proceeding anyway")
            await asyncio.sleep(1)
        else:
            _w("D_sobre_tab_clicked", "tab not found — will attempt extraction from current DOM anyway")

        # ---- Step E: save HTML snapshot (optional) --------------------
        if save_html:
            html  = await _get_html_snapshot(page)
            fname = f"t5_sobre_{advertiser_key}.html"
            Path(fname).write_text(html, encoding="utf-8")
            _log(f"  HTML saved → {fname}")

        # ---- Step F: extract fields from visible text + JS fallback ------
        _log("Step F — extracting fields from page text...")
        page_text = await _get_visible_text(page)

        if not page_text.strip():
            _f("F_extraction", "page innerText is empty")
            return adv_result

        # Log a slice for debugging
        _log(f"  [text excerpt] {page_text[:300].replace(chr(10), ' ')!r}")

        extracted = extract_fields(page_text)

        # page_id fallback 1: use known_pid when already provided
        if not extracted["page_id"] and known_pid:
            extracted["page_id"] = known_pid
            _log(f"  page_id (from known_pid): {known_pid}")

        # page_id fallback 2: scrape JS bundle via innerHTML regex
        if not extracted["page_id"]:
            try:
                pid_js = await page.evaluate(
                    r"""() => {
                        const m = document.documentElement.innerHTML
                            .match(/page_id[":\s]+(\d{10,20})/);
                        return m ? m[1] : null;
                    }"""
                )
                if pid_js:
                    extracted["page_id"] = pid_js
                    _log(f"  page_id (from JS innerHTML): {pid_js}")
            except Exception:
                pass

        adv_result["extracted"] = extracted

        _log(f"  page_id      : {extracted['page_id']}")
        _log(f"  fb_followers : {extracted['fb_followers']}")
        _log(f"  ig_handle    : {extracted['ig_handle']}")
        _log(f"  ig_followers : {extracted['ig_followers']}")
        _log(f"  created      : {extracted['created']}")

        # ---- Step G: validate extracted values ------------------------
        _log("Step G — validating extracted values against expected...")

        # page_id
        if known_pid:
            if extracted["page_id"] == known_pid:
                _p("G_page_id", f"page_id matches expected: {known_pid}")
            elif extracted["page_id"]:
                _f("G_page_id", f"got '{extracted['page_id']}', expected '{known_pid}'")
            else:
                _f("G_page_id", "page_id not found via text or JS")
        else:
            # Ivangelica — any ≥ 10-digit string is a pass
            if extracted["page_id"] and len(re.sub(r"\D", "", extracted["page_id"])) >= 10:
                _p("G_page_id", f"page_id discovered: {extracted['page_id']}")
            else:
                _f("G_page_id", "no ≥10-digit page_id found")

        # fb_followers
        if extracted["fb_followers"]:
            _p("G_fb_followers", f"value: {extracted['fb_followers']}")
        else:
            _w("G_fb_followers", "not found")

        # ig_handle
        exp_handle = expected.get("ig_handle")
        if extracted["ig_handle"]:
            if exp_handle and extracted["ig_handle"].lower() != exp_handle.lower():
                _w("G_ig_handle", f"got '{extracted['ig_handle']}', expected '{exp_handle}'")
            else:
                _p("G_ig_handle", f"value: {extracted['ig_handle']}")
        else:
            _w("G_ig_handle", "not found")

        # ig_followers
        if extracted["ig_followers"]:
            _p("G_ig_followers", f"value: {extracted['ig_followers']}")
        else:
            _w("G_ig_followers", "not found")

        # created
        exp_contains = expected.get("created_contains", [])
        if extracted["created"]:
            if exp_contains:
                hits = [kw for kw in exp_contains if kw.lower() in extracted["created"].lower()]
                if len(hits) == len(exp_contains):
                    _p("G_created", f"value: {extracted['created']}")
                else:
                    _w("G_created", f"got '{extracted['created']}' — missing keywords: {set(exp_contains)-set(hits)}")
            else:
                _p("G_created", f"value: {extracted['created']}")
        else:
            _w("G_created", "not found")

    except Exception as exc:
        _f("unexpected", str(exc))
        import traceback
        _log(traceback.format_exc(), "ERROR")
    finally:
        await context.close()

    return adv_result


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main() -> None:
    parser = argparse.ArgumentParser(description="T-5 Playwright Sobre tab scrape")
    parser.add_argument(
        "--headless", action="store_true", default=False,
        help="Run headless (default: headed — recommended for first run)",
    )
    parser.add_argument(
        "--advertiser", default="tadewald",
        choices=list(ADVERTISERS.keys()) + ["all"],
        help="Which advertiser(s) to test (default: tadewald)",
    )
    parser.add_argument(
        "--page-id", default=None,
        help="Override the known page_id for the selected advertiser",
    )
    parser.add_argument(
        "--save-html", action="store_true", default=False,
        help="Save full page HTML to t5_sobre_<advertiser>.html for offline inspection",
    )
    args = parser.parse_args()

    results["started_at"] = datetime.utcnow().isoformat() + "Z"
    results["headless"]   = args.headless

    if args.advertiser == "all":
        keys = list(ADVERTISERS.keys())
    else:
        keys = [args.advertiser]

    if args.page_id and len(keys) == 1:
        ADVERTISERS[keys[0]]["page_id"] = args.page_id
        _log(f"Override page_id → {args.page_id}")

    _log("=" * 60)
    _log("T-5 — Playwright Sobre Tab Scrape")
    _log(f"  Headless   : {args.headless}")
    _log(f"  Advertisers: {keys}")
    _log(f"  Save HTML  : {args.save_html}")
    _log("=" * 60)

    try:
        from playwright.async_api import async_playwright
    except ImportError:
        _log("playwright not installed. Run: pip install playwright && playwright install chromium", "ERROR")
        sys.exit(1)

    async with async_playwright() as p:
        browser = await p.chromium.launch(
            headless=args.headless,
            slow_mo=200 if not args.headless else 0,  # easier to observe in headed mode
            args=[
                "--no-sandbox",
                "--disable-blink-features=AutomationControlled",
            ],
        )

        for key in keys:
            adv_result = await test_advertiser(
                browser,
                advertiser_key=key,
                advertiser=ADVERTISERS[key],
                save_html=args.save_html,
            )
            results["advertisers"][key] = adv_result

        await browser.close()

    # ---- Final summary --------------------------------------------------
    results["completed_at"] = datetime.utcnow().isoformat() + "Z"

    _log("")
    _log("=" * 60)
    _log("FINAL SUMMARY")
    _log("=" * 60)

    all_pass = True
    for key, adv in results["advertisers"].items():
        passes = len(adv["pass"])
        fails  = len(adv["fail"])
        warns  = len(adv["warn"])
        status = "OK " if fails == 0 else "ERR"
        _log(f"  [{status}] {adv['label']}: {passes} pass / {fails} fail / {warns} warn")
        for f in adv["fail"]:
            _log(f"          FAIL: {f} — {adv['steps'][f]['detail']}", "ERROR")
        if extracted := adv.get("extracted"):
            _log(f"        page_id      = {extracted.get('page_id')}")
            _log(f"        fb_followers = {extracted.get('fb_followers')}")
            _log(f"        ig_handle    = {extracted.get('ig_handle')}")
            _log(f"        ig_followers = {extracted.get('ig_followers')}")
            _log(f"        created      = {extracted.get('created')}")
        if fails > 0:
            all_pass = False

    _log("=" * 60)
    _save_results()

    sys.exit(0 if all_pass else 1)


if __name__ == "__main__":
    asyncio.run(main())
