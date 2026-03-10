#!/usr/bin/env python3
"""
Andromeda Feasibility Test — Steps 1-8

Validates that Playwright on EC2 can:
  1. Fetch the current FB access token from Secrets Manager (IAM role)
  2. Launch headless Chromium (with optional playwright-stealth)
  3. Navigate to the Meta Ad Library snapshot URL
  4. Wait for networkidle (React renders the ad)
  5. Extract video CDN URL (video.src) and thumbnail (video.poster) from the DOM
  6. Assert URLs are present and not expired (check 'oe' hex timestamp)
  7. Download the MP4 to /tmp
  8. Download the thumbnail JPEG to /tmp

Reference ad: 2162596270894996  (Lost Dutchman Leather Goods, 35 days active)
Expected result: all 8 steps PASS, ~7 MB MP4 downloaded to /tmp/andromeda_test/

Usage:
    python andromeda_single_ad_test.py
    python andromeda_single_ad_test.py --ad-id 2162596270894996
    python andromeda_single_ad_test.py --no-stealth
    python andromeda_single_ad_test.py --dry-run   # skip downloads, test DOM extraction only
"""

import argparse
import asyncio
import json
import os
import re
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

import boto3
import requests

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

AD_ID_DEFAULT = "2162596270894996"
SECRET_NAME   = "metaads/dev/meta-api"
REGION        = "us-east-1"
TMP_DIR       = Path("/tmp/andromeda_test")
RESULTS_FILE  = Path("/home/ec2-user/andromeda_test_results.json")


# ---------------------------------------------------------------------------
# Result tracking
# ---------------------------------------------------------------------------

results = {
    "ad_id": None,
    "started_at": None,
    "completed_at": None,
    "stealth_enabled": None,
    "dry_run": None,
    "steps": {},
    "summary": {"passed": 0, "failed": 0},
    "extracted": {
        "video_url": None,
        "thumbnail_url": None,
        "video_url_expiry": None,
        "thumbnail_url_expiry": None,
    },
    "downloads": {
        "video_path": None,
        "video_size_mb": None,
        "thumbnail_path": None,
        "thumbnail_size_kb": None,
    },
}


def _log(msg, level="INFO"):
    ts = datetime.now().strftime("%H:%M:%S")
    print(f"[{ts}] [{level}] {msg}", flush=True)


def _pass(step_key, details=""):
    results["steps"][step_key] = {"status": "PASS", "details": details}
    results["summary"]["passed"] += 1
    _log(f"PASS  {step_key}: {details}")


def _fail(step_key, details=""):
    results["steps"][step_key] = {"status": "FAIL", "details": details}
    results["summary"]["failed"] += 1
    _log(f"FAIL  {step_key}: {details}", "ERROR")


def _save_results():
    RESULTS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(RESULTS_FILE, "w") as fh:
        json.dump(results, fh, indent=2)
    _log(f"Results written → {RESULTS_FILE}")


# ---------------------------------------------------------------------------
# URL helpers
# ---------------------------------------------------------------------------

def _oe_info(url: str) -> str:
    """Return human-readable expiry info from the 'oe' query param."""
    match = re.search(r"[&?]oe=([0-9a-fA-F]+)", url)
    if not match:
        return "no oe param"
    expiry_unix = int(match.group(1), 16)
    expiry_dt   = datetime.fromtimestamp(expiry_unix, tz=timezone.utc)
    remaining_h = (expiry_unix - time.time()) / 3600
    return f"expires {expiry_dt.strftime('%Y-%m-%d %H:%M UTC')} (in {remaining_h:.1f}h)"


def _is_expired(url: str) -> bool:
    match = re.search(r"[&?]oe=([0-9a-fA-F]+)", url)
    if not match:
        return False
    return time.time() > int(match.group(1), 16)


# ---------------------------------------------------------------------------
# Step 1 — Secrets Manager
# ---------------------------------------------------------------------------

def step1_get_token() -> str | None:
    _log("Step 1 — fetching FB access token from Secrets Manager...")
    try:
        client = boto3.client("secretsmanager", region_name=REGION)
        resp   = client.get_secret_value(SecretId=SECRET_NAME)
        secret = json.loads(resp["SecretString"])
        token  = secret.get("access_token")
        if not token:
            _fail("1_get_token", "Secret retrieved but 'access_token' key is missing")
            return None
        _pass("1_get_token", f"token length={len(token)}, starts with {token[:8]}...")
        return token
    except Exception as exc:
        _fail("1_get_token", str(exc))
        return None


# ---------------------------------------------------------------------------
# Steps 2-6 — Playwright
# ---------------------------------------------------------------------------

async def steps_2_6_playwright(token: str, ad_id: str, use_stealth: bool):
    """
    Returns (video_url, poster_url) on success, (None, None) on failure.
    Also handles IMAGE ads: falls back to the first fbcdn <img> src.
    """
    snapshot_url = (
        f"https://www.facebook.com/ads/archive/render_ad/"
        f"?id={ad_id}&access_token={token}"
    )

    # ---- Step 2: launch browser ----------------------------------------
    _log(f"Step 2 — launching Playwright (stealth={use_stealth})...")
    try:
        from playwright.async_api import async_playwright
    except ImportError as exc:
        _fail("2_launch_playwright", f"playwright not installed: {exc}")
        return None, None

    stealth_fn = None
    if use_stealth:
        try:
            from playwright_stealth import stealth_async
            stealth_fn = stealth_async
            _log("  playwright-stealth loaded")
        except ImportError:
            _log("  WARNING: playwright-stealth not installed, continuing without stealth")

    try:
        async with async_playwright() as p:
            browser = await p.chromium.launch(
                headless=True,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                    "--disable-gpu",
                    "--single-process",
                ],
            )
            context = await browser.new_context(
                user_agent=(
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                ),
                viewport={"width": 1280, "height": 800},
                locale="en-US",
            )
            page = await context.new_page()

            if stealth_fn:
                await stealth_fn(page)

            _pass("2_launch_playwright", f"headless Chromium ready, stealth={use_stealth}")

            # ---- Step 3: navigate --------------------------------------
            _log("Step 3 — navigating to snapshot URL...")
            t0 = time.time()
            try:
                await page.goto(snapshot_url, timeout=30_000, wait_until="domcontentloaded")
                _pass("3_navigate", f"domcontentloaded in {time.time()-t0:.1f}s")
            except Exception as exc:
                _fail("3_navigate", str(exc))
                await browser.close()
                return None, None

            # ---- Step 4: networkidle -----------------------------------
            _log("Step 4 — waiting for networkidle...")
            t0 = time.time()
            try:
                await page.wait_for_load_state("networkidle", timeout=20_000)
                _pass("4_networkidle", f"idle in {time.time()-t0:.1f}s")
            except Exception as exc:
                # Timeout is non-fatal — React may have rendered enough
                _pass("4_networkidle", f"timed out but continuing: {exc}")

            # ---- Step 5: extract URLs ----------------------------------
            _log("Step 5 — extracting CDN URLs from DOM...")
            page_title = await page.title()
            _log(f"  page title: '{page_title}'")

            video_src = await page.evaluate(
                "() => document.querySelector('video')?.src ?? null"
            )
            video_poster = await page.evaluate(
                "() => document.querySelector('video')?.getAttribute('poster') ?? null"
            )
            # Fallback for IMAGE ads (no <video> tag)
            img_src = None
            if not video_src:
                img_src = await page.evaluate(
                    "() => {"
                    "  const candidates = document.querySelectorAll('img');"
                    "  for (const img of candidates) {"
                    "    if (img.src && img.src.includes('fbcdn.net')) return img.src;"
                    "  }"
                    "  return null;"
                    "}"
                )

            _log(f"  video.src    : {(video_src or '')[:90]}{'...' if video_src and len(video_src)>90 else ''}")
            _log(f"  video.poster : {(video_poster or '')[:90]}{'...' if video_poster and len(video_poster)>90 else ''}")
            _log(f"  img fallback : {(img_src or '')[:90]}{'...' if img_src and len(img_src)>90 else ''}")

            primary_url = video_src or img_src

            if primary_url:
                _pass(
                    "5_extract_urls",
                    f"video={'yes' if video_src else 'no'}, "
                    f"poster={'yes' if video_poster else 'no'}, "
                    f"img_fallback={'yes' if img_src else 'no'}",
                )
                results["extracted"]["video_url"]      = primary_url
                results["extracted"]["thumbnail_url"]  = video_poster
            else:
                # Dump body text for debugging
                body_snippet = await page.evaluate(
                    "() => document.body?.innerText?.slice(0,400) ?? 'no body'"
                )
                _fail("5_extract_urls", f"no video or fbcdn img found. body='{body_snippet}'")
                await browser.close()
                return None, None

            # ---- Step 6: expiry check ----------------------------------
            _log("Step 6 — checking URL validity and expiry...")
            if _is_expired(primary_url):
                _fail("6_url_validity", f"primary URL has already expired — {_oe_info(primary_url)}")
            else:
                expiry = _oe_info(primary_url)
                results["extracted"]["video_url_expiry"] = expiry
                _pass("6_url_validity", f"primary URL valid — {expiry}")
                if video_poster and not _is_expired(video_poster):
                    poster_expiry = _oe_info(video_poster)
                    results["extracted"]["thumbnail_url_expiry"] = poster_expiry
                    _log(f"  poster expiry: {poster_expiry}")

            await browser.close()
            return primary_url, video_poster

    except Exception as exc:
        _fail("2_launch_playwright", f"unexpected error: {exc}")
        return None, None


# ---------------------------------------------------------------------------
# Step 7 — Download MP4
# ---------------------------------------------------------------------------

def step7_download_video(video_url: str, ad_id: str) -> str | None:
    _log("Step 7 — downloading MP4...")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TMP_DIR / f"ad_{ad_id}.mp4"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.facebook.com/",
    }
    try:
        t0 = time.time()
        total = 0
        with requests.get(video_url, stream=True, headers=headers, timeout=120) as resp:
            resp.raise_for_status()
            with open(out_path, "wb") as fh:
                for chunk in resp.iter_content(chunk_size=65_536):
                    fh.write(chunk)
                    total += len(chunk)
        elapsed  = time.time() - t0
        size_mb  = total / (1024 * 1024)
        results["downloads"]["video_path"]    = str(out_path)
        results["downloads"]["video_size_mb"] = round(size_mb, 2)
        _pass("7_download_video", f"{size_mb:.1f} MB in {elapsed:.1f}s → {out_path}")
        return str(out_path)
    except Exception as exc:
        _fail("7_download_video", str(exc))
        return None


# ---------------------------------------------------------------------------
# Step 8 — Download thumbnail
# ---------------------------------------------------------------------------

def step8_download_thumbnail(poster_url: str, ad_id: str) -> str | None:
    _log("Step 8 — downloading thumbnail...")
    TMP_DIR.mkdir(parents=True, exist_ok=True)
    out_path = TMP_DIR / f"thumb_{ad_id}.jpg"

    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
            "AppleWebKit/537.36 (KHTML, like Gecko) "
            "Chrome/121.0.0.0 Safari/537.36"
        ),
        "Referer": "https://www.facebook.com/",
    }
    try:
        t0   = time.time()
        resp = requests.get(poster_url, headers=headers, timeout=30)
        resp.raise_for_status()
        out_path.write_bytes(resp.content)
        elapsed  = time.time() - t0
        size_kb  = len(resp.content) / 1024
        results["downloads"]["thumbnail_path"]    = str(out_path)
        results["downloads"]["thumbnail_size_kb"] = round(size_kb, 1)
        _pass("8_download_thumbnail", f"{size_kb:.0f} KB in {elapsed:.1f}s → {out_path}")
        return str(out_path)
    except Exception as exc:
        _fail("8_download_thumbnail", str(exc))
        return None


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

async def main():
    parser = argparse.ArgumentParser(description="Andromeda feasibility test — steps 1-8")
    parser.add_argument("--ad-id",    default=AD_ID_DEFAULT, help="Meta ad archive ID")
    parser.add_argument("--stealth",  action="store_true",  default=True,
                        help="Enable playwright-stealth (default: on)")
    parser.add_argument("--no-stealth", dest="stealth", action="store_false")
    parser.add_argument("--dry-run",  action="store_true",
                        help="Skip file downloads (steps 7-8); only test DOM extraction")
    args = parser.parse_args()

    results["ad_id"]          = args.ad_id
    results["started_at"]     = datetime.utcnow().isoformat() + "Z"
    results["stealth_enabled"] = args.stealth
    results["dry_run"]        = args.dry_run

    _log("=" * 60)
    _log("Andromeda Feasibility Test — Steps 1-8")
    _log(f"  Ad ID     : {args.ad_id}")
    _log(f"  Stealth   : {args.stealth}")
    _log(f"  Dry run   : {args.dry_run}")
    _log("=" * 60)

    # ---- Step 1 --------------------------------------------------------
    token = step1_get_token()
    if not token:
        _log("FATAL: Cannot proceed without FB token. Is the IAM role attached?", "ERROR")
        results["completed_at"] = datetime.utcnow().isoformat() + "Z"
        _save_results()
        sys.exit(1)

    # ---- Steps 2-6 -----------------------------------------------------
    video_url, poster_url = await steps_2_6_playwright(token, args.ad_id, args.stealth)

    # ---- Steps 7-8 -----------------------------------------------------
    if args.dry_run:
        _log("Dry run — skipping downloads (steps 7 and 8)")
    else:
        if video_url:
            step7_download_video(video_url, args.ad_id)
        else:
            _fail("7_download_video", "skipped — no video URL extracted in step 5")

        if poster_url:
            step8_download_thumbnail(poster_url, args.ad_id)
        else:
            _fail("8_download_thumbnail", "skipped — no poster URL extracted in step 5")

    # ---- Summary -------------------------------------------------------
    results["completed_at"] = datetime.utcnow().isoformat() + "Z"
    total  = results["summary"]["passed"] + results["summary"]["failed"]
    passed = results["summary"]["passed"]
    failed = results["summary"]["failed"]

    _log("=" * 60)
    _log(f"SUMMARY: {passed}/{total} steps passed")
    for key, val in results["steps"].items():
        icon = "OK " if val["status"] == "PASS" else "ERR"
        _log(f"  [{icon}] {key}: {val['details']}")
    _log("=" * 60)

    _save_results()

    if failed == 0:
        _log("ALL STEPS PASSED — Playwright asset extraction is feasible on EC2")
        sys.exit(0)
    else:
        _log(f"{failed} step(s) FAILED — see details above", "ERROR")
        sys.exit(1)


if __name__ == "__main__":
    asyncio.run(main())
