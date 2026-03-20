# Competitor Intelligence Card — Feasibility Test Plan

## Document Purpose

This document defines a set of **executable, verifiable tests** for every field
proposed in the "Full Competitor Intelligence Card" UI target (ANDROMEDA doc §8).

The ANDROMEDA document mixed confirmed results, reasonable assumptions, and
aspirational claims without clearly distinguishing between them. This plan
corrects that: every field in the proposed UI card is treated as **unverified
until a test passes**.

No implementation work will begin until the relevant test has a recorded result.

**Reference advertisers — Phase A (ground cases):**

These are Brazilian advertisers on newer pages where the numeric page_id
IS displayed on the "Sobre" tab. All feasibility tests run against these two
first.

| Advertiser | Page ID | Niche | "Sobre" shows page_id? | API status |
|---|---|---|---|---|
| Rodrigo Tadewald / Asimov Academy | `711978348674579` | AI / Python education | ✅ Yes (confirmed by screenshot) | Returns 0 ads — under investigation |
| Ivangelica | Unknown — to be found in T-5 | Stand-up comedy (BR) | Expected yes — to be confirmed | Unknown |

**Reference advertisers — Phase B (deferred, NOT in scope for this feasibility):**

These are established brands where the "Sobre" tab shows only a vanity
username (`@lancomeUS`) and does NOT display the numeric page_id. Different
extraction techniques are required. Phase B begins only after Phase A tests
are complete and the implementation is stable.

| Advertiser | Type | Why deferred |
|---|---|---|
| Lancôme US | Global brand, page created 2008 | Vanity URL only — page_id not in "Sobre" DOM |
| Other established BR brands | TBD | Same issue — DOM structure differs |

**Note on "Sobre" tab page_id visibility** (documented in ANDROMEDA §10):
Meta stopped surfacing the numeric page_id on the "Sobre" tab for older
pages that have verified vanity usernames. New pages (< ~2 years, smaller
following) still show the full numeric ID. This is a UI presentation
difference, not a data absence — the page_id always exists and is always in
API responses and page HTML source. Phase B will address extraction methods
for the established-brand case.

**Test environment:**
- Local venv: `/Users/emadruga/proj/metaAds/venv` (playwright 1.57.0 installed)
- AWS profile: `metads`, region: `us-east-1`
- Meta API secret: `metaads/dev/meta-api`
- EC2 feasibility instance: reuse setup from `andromeda_single_ad_test.py` if
  Playwright must run in an AWS context

---

## What Phase 1 (Andromeda) Actually Proved

Only these items are **confirmed**:

| Confirmed fact | Source |
|---|---|
| Playwright headless Chromium runs on EC2 AL2023 with stealth=True | Phase 1 test 2026-03-10 |
| `ad_snapshot_url` page loads, `<video>` tag is present in DOM | Phase 1 step 3–5 |
| CDN MP4 URL extractable from DOM; 1.64 MB SD video downloads cleanly | Phase 1 step 7 |
| Thumbnail JPEG URL extractable from DOM; 275 KB downloads cleanly | Phase 1 step 8 |
| CDN URLs are valid for ~106 hours | Phase 1 step 6 |
| Peak RAM ~347 MB on t3.small for single-ad Playwright session | Phase 1 step 8 |
| `ads_archive` with `search_page_ids` returns ads for at least one advertiser (Nike) | Live API test |
| Meta API token is valid, `ads_read` scope granted | Certification doc |

Everything else in the UI card is **unverified**.

---

## Field Audit — Verified vs. Unverified

| Field in UI Card | Claimed source | Verified? | Test # |
|---|---|---|---|
| Page ID | `ads_archive` or Playwright | ✅ Confirmed (manual lookup) | — |
| Page created date | Graph API `created_time` | ❌ No | T-4 |
| Facebook followers | Graph API `fan_count` | ❌ No (code 10 seen for Tadewald) | T-4 |
| Instagram handle + follower count | ??? | ❌ No — not in Ad Library API | T-5 |
| Total / active / longevity / new ads in 30d | Computed from `search_page_ids` | ❌ `search_page_ids` fails for Tadewald | T-1 |
| Spend estimate (R$ figures) | `spend` field in `ads_archive` | ❌ Suspected null for BR — unverified | T-2 |
| Impressions | `impressions` field in `ads_archive` | ❌ Same concern as spend | T-2 |
| Creative mix % (video / image / carousel) | `media_type` field | ❌ Field population rate unknown | T-3 |
| Platform distribution % | `publisher_platforms` field | ❌ Field population rate unknown | T-3 |
| Top copy angles (Claude-classified) | Claude on `ad_creative_bodies` | ❌ Field population rate unknown | T-3 |
| Andromeda Score (71/100) | Playwright + Claude pipeline | ❌ Phase 2 not done | T-6 |
| MP4 creative download to S3 | Playwright + boto3 | Partially — `/tmp` proven, S3 not tested | T-6 |
| Thumbnail download to S3 | Playwright + boto3 | Partially — `/tmp` proven, S3 not tested | T-6 |

---

## Test Plan

---

### T-1 — `search_page_ids` Reliability Across Multiple Advertisers

**Question**: Is the zero-result for Tadewald (`711978348674579`) an isolated
anomaly (new page, indexing lag) or a systematic API limitation?

**Why this matters**: Every ad-portfolio field in the UI card (total ads,
active count, longevity, spend, creative mix, copy angles) depends entirely
on `search_page_ids` returning results. If it fails silently for a class of
pages, the whole card is empty.

**Test script**: `aws_feasibility/test_search_page_ids.py`

**Test matrix** — run all four variants for each advertiser:

| Variant | Parameters |
|---|---|
| A | `search_page_ids={id}` + `ad_reached_countries=BR` + `ad_active_status=ALL` |
| B | `search_page_ids={id}` + `ad_reached_countries=BR,PT,MX,AR,US` + `ad_active_status=ALL` |
| C | `search_page_ids={id}` + `ad_reached_countries=ALL` + `ad_active_status=ALL` |
| D | `search_terms={page_name}` + `ad_reached_countries=BR` + `ad_active_status=ALL` |

**Advertisers to test (Phase A ground cases first):**

| Advertiser | Page ID | Expected (web UI) | Priority |
|---|---|---|---|
| Rodrigo Tadewald | `711978348674579` | ~120 ads | Primary |
| Ivangelica | From T-5 | Unknown | Primary |
| Lost Dutchman Leather Goods | From web UI "Sobre" tab | ~110 ads | Secondary — US advertiser, control case |
| One large BR advertiser (e.g. Magazine Luiza) | From web UI | Many ads | Secondary — scale check |

**Logged per call**: HTTP status, `len(data)`, `data[0].keys()` if non-empty,
any `error` node in response.

**Pass criteria:**

| Result | Verdict |
|---|---|
| Variants A/B/C all return 0 for Tadewald AND return >0 for Lost Dutchman | Tadewald is anomalous — investigate page age / type |
| All variants return 0 for all tested advertisers | `search_page_ids` is broken for BR — major finding |
| Variant A returns >0 for Tadewald | Earlier manual test was wrong — recheck |
| `ad_reached_countries=ALL` is not a valid value | Document the accepted values |

**Failure action**: If `search_page_ids` returns 0 for all BR advertisers
across all variants, the entire ad-portfolio section of the UI card requires
Playwright scraping of the web UI as the data source. Do not proceed to
implementation without understanding the root cause.

---

### T-2 — `spend` and `impressions` Field Population for BR Ads

**Question**: Are the `spend` and `impressions` fields populated for
Brazilian ads, or are they EU-only (DSA mandate)?

**Why this matters**: The UI card shows "R$ 28,000 – R$ 119,000" spend
estimates. If these fields are null for BR, that entire section is impossible
without a different data source.

**Test script**: `aws_feasibility/test_spend_fields.py`

**Method:**
1. Run `search_page_ids` for a BR advertiser that returns ads (use whichever
   T-1 confirms works).
2. Request fields: `spend,impressions,ad_delivery_start_time,page_name,id`
3. Log the raw JSON for the first 10 ads.
4. Repeat with a known EU advertiser (e.g. a French brand) as a control.

**Pass criteria:**

| Result | Verdict |
|---|---|
| `spend` is non-null for BR ads | Spend section is buildable |
| `spend` is null for BR, non-null for EU control | Spend is EU-only — remove from BR UI card |
| `spend` is null for both BR and EU | Field requires special app permission — investigate |
| `impressions` follows same pattern as `spend` | Document accordingly |

**Expected result** (based on public Meta documentation on DSA):
`spend` will be null for BR. Test is required to confirm, not assume.

---

### T-3 — `media_type`, `publisher_platforms`, `ad_creative_bodies` Population Rate

**Question**: For a real set of ads from a BR advertiser, what percentage
actually have these fields populated? Missing fields are common in the
Ad Library API.

**Test script**: `aws_feasibility/test_field_population.py`

**Method:**
1. Use the advertiser from T-1 that returns the most ads.
2. Fetch up to 100 ads with all relevant fields requested.
3. For each field, count: populated vs. null/empty.

**Fields to audit:**

| Field | Expected presence | Used for |
|---|---|---|
| `media_type` | Unknown | Creative mix % |
| `publisher_platforms` | Unknown | Platform distribution % |
| `ad_creative_bodies` | Unknown | Copy angles (Claude) |
| `ad_creative_link_titles` | Unknown | Copy angles (Claude) |
| `ad_snapshot_url` | Unknown | Andromeda pipeline input |
| `ad_delivery_start_time` | Unknown | Longevity calculation |
| `ad_delivery_stop_time` | Unknown | Active vs. inactive |

**Pass criteria (per field):**

| Population rate | Verdict |
|---|---|
| ≥ 80% | Field is reliable — build on it |
| 40–79% | Field is sparse — show "N/A" where missing |
| < 40% | Field is unreliable — remove from UI card or show warning |

---

### T-4 — Graph API Page Node: `fan_count`, `created_time`, `category`

**Question**: Can we retrieve Facebook follower count and page creation date
from the Graph API page node for pages we do NOT manage?

**Context**: Testing `GET /{page_id}?fields=name,fan_count,category,about`
for Tadewald returned **error code 10** in a prior session. This test
characterises the failure and determines if any page type succeeds.

**Test script**: `aws_feasibility/test_graph_page_node.py`

**Test matrix (Phase A ground cases first):**

| Page | Page ID | Type | Expected |
|---|---|---|---|
| Rodrigo Tadewald | `711978348674579` | New page (Sep 2025), no vanity URL | Code 10 (known from prior session) |
| Ivangelica | From T-5 | New/mid-size BR page | Unknown |
| Lost Dutchman Leather Goods | From T-1 | Older US page, has vanity URL | Unknown |
| Our own app page (if one exists) | — | Page we manage | Should work — baseline control |

**Phase B (deferred — established brands):**
Lancôme, Magazine Luiza, and similar established brands are NOT in this test
matrix. They are a separate variation requiring different extraction techniques
and are out of scope until Phase A completes.

**Fields requested**: `name,fan_count,category,about,created_time`

**Pass criteria:**

| Result | Verdict |
|---|---|
| Any page returns `fan_count` without error | Field available for some pages — document which type |
| All pages return code 10 | "Page Public Content Access" review required — remove from card |
| Pages we manage work, others fail | Field only available for own pages — remove from card for competitors |

---

### T-5 — Playwright "Sobre" Tab Scrape

**Question**: Can Playwright navigate to `facebook.com/ads/library`, search
an advertiser by name, click "Sobre", and extract these fields from the DOM:
- Facebook page ID (numeric)
- Facebook followers
- Instagram handle
- Instagram follower count
- Page creation date

**Why this matters**: These fields are visually present in the "Sobre" tab
(confirmed by screenshot of Tadewald's page). This test determines whether
they are machine-extractable without App Review.

**Scope**: Phase A only — advertisers where the numeric page_id IS shown on
the "Sobre" tab (new/smaller pages). The established-brand variation (Lancôme,
large brands where only a vanity username appears) is Phase B and is
explicitly out of scope here.

**Test script**: `aws_feasibility/test_playwright_sobre.py`

**Method:**
```python
# Pseudocode — actual selectors to be discovered during test
# Run with headless=False first to observe the real DOM interactively
await page.goto("https://www.facebook.com/ads/library/")
await page.fill('[placeholder*="Pesquise"]', "Rodrigo Tadewald")
await page.keyboard.press("Enter")
await page.wait_for_selector(".advertiser-name-or-selector")
await page.click("tab-sobre-selector")
await page.wait_for_load_state("networkidle")
content = await page.content()
# Attempt regex extraction (selectors confirmed during interactive run):
#   r"Identificação[:\s]+(\d{10,20})"    ← numeric page_id
#   r"([\d,\.]+)\s+seguidores"           ← Facebook followers (first match)
#   r"@([\w\.]+)"                        ← Instagram handle
#   r"([\d,\.]+)\s+mil seguidores"       ← Instagram followers (second match)
#   r"Página criada\s+(.+?)(?:\n|<)"     ← creation date
```

**Start with `headless=False`** to observe the real DOM, discover actual
selectors, and confirm the page renders without a login wall or CAPTCHA.
Only switch to `headless=True` once the selectors are confirmed working.

**Logged per advertiser**: Raw HTML of the "Sobre" section, extracted values
or None for each field, any CAPTCHA / login redirect / empty page encountered.

**Ground case pass criteria — Rodrigo Tadewald:**

| Field | Pass condition |
|---|---|
| Facebook page ID | Extracted numeric string == `711978348674579` |
| Facebook followers | Extracted number within ±10% of value shown in screenshot |
| Instagram handle | Extracted string == `rodrigotadewald` |
| Instagram followers | Extracted number within ±10% of value shown in screenshot |
| Page creation date | Extracted string contains "set" and "2025" |
| CAPTCHA triggered | ❌ Hard fail |
| Login wall before "Sobre" renders | ❌ Hard fail |
| Page renders but selectors return None | ❌ Fail — inspect HTML, adjust regex |

**Second ground case — Ivangelica (stand-up comedy, BR):**

Run the identical script with `search_term = "Ivangelica"`. Goals:
1. Confirm the page_id is visible on Ivangelica's "Sobre" tab (expected yes,
   unconfirmed).
2. Capture Ivangelica's page_id — this becomes the second reference
   advertiser for all subsequent tests.
3. Confirm the DOM structure and regex patterns are consistent across two
   different BR advertisers, not just Tadewald.

| Field | Pass condition |
|---|---|
| Facebook page ID | Any numeric string ≥ 10 digits extracted |
| "Sobre" tab renders | Page_id section visible (consistent with Tadewald) |
| Selectors work without modification | ✅ Same regex as Tadewald succeeds |

**Phase B (NOT in this test)**: Lancôme US and other established brands where
the "Sobre" tab shows only `@lancomeUS` and no numeric ID. Different
techniques are required (Graph API username lookup, page HTML source parsing).
Phase B is deferred until Phase A is confirmed stable.

---

### T-6 — Phase 2 Batch Creative Download (10 Ads → S3)

**Question**: Does the Andromeda Playwright download pipeline survive 10
consecutive ads without bot detection? And can assets be written to S3?

**Prerequisite**: T-1 must pass for at least one advertiser (need real
`ad_snapshot_url` values). T-1 failure = T-6 blocked.

**Test script**: `aws_feasibility/test_batch_creative_download.py`
(extension of `andromeda_single_ad_test.py`)

**Configuration (Config C from Phase 1 plan):**
- `stealth=True`
- Random delay between ads: 5–15 seconds
- Reuse same Playwright browser instance across all 10 ads (warm browser)
- Target: 10 ads from whichever advertiser T-1 confirms works

**Per-ad steps:**
1. Navigate to `ad_snapshot_url`
2. Wait for `networkidle`
3. Extract `video.src` (MP4 URL) and `video.poster` (thumbnail URL)
4. If no `<video>` tag: check for `<img>` (image ad) — download that instead
5. HTTP download MP4 to `/tmp/{ad_id}.mp4`
6. HTTP download thumbnail to `/tmp/{ad_id}_thumb.jpg`
7. Upload both to `s3://metaads-dev-creatives/{page_id}/{ad_id}/`
8. Delete from `/tmp`
9. Log result: success / timeout / CAPTCHA / empty DOM / CDN error

**S3 bucket**: `metaads-dev-creatives` — must be created before test.
**IAM**: EC2 instance role must have `s3:PutObject` on that bucket.

**Pass criteria:**

| Metric | Pass threshold |
|---|---|
| Ads downloaded successfully | ≥ 8 / 10 |
| CAPTCHA triggered | 0 — any CAPTCHA = conditional fail (add proxy) |
| S3 upload confirmed (`s3.head_object` after upload) | 100% of downloaded files |
| Peak RAM during batch | < 1.5 GB |
| Total elapsed time for 10 ads | < 30 minutes |

**Failure modes and actions:**

| Failure | Action |
|---|---|
| < 8/10 download success, no CAPTCHA | Check CDN URL expiry — may need shorter batch window |
| CAPTCHA on any ad | Add residential proxy for snapshot page requests only |
| S3 upload fails | IAM policy issue — fix before re-run |
| OOM on t3.small | Restart browser between ads; or upgrade to t3.medium |

---

## Test Execution Order and Dependencies

```
T-5 (Playwright Sobre — Tadewald + Ivangelica)
      │
      ├─→ Discovers Ivangelica page_id  ──────────────────────────────┐
      │                                                                │
      └─→ Run in parallel with T-2 and T-4 on day 1                  │
                                                                       ▼
T-2 (spend/impressions)  ─┐                              T-1 (search_page_ids)
T-4 (Graph page node)    ─┤─── Independent, day 1             │
                           ┘   (requests only, no EC2)         ├─→ PASS → T-3 → T-6
                                                                │
                                                                └─→ FAIL: Playwright
                                                                    web-scrape as alt
                                                                    data source — new plan
```

**Day 1 target** (no EC2 needed — local venv + AWS credentials):
- T-5 first (headless=False): discover selectors, confirm Tadewald, get
  Ivangelica page_id
- T-1: run with Tadewald + Ivangelica page_ids in hand
- T-2: check spend/impressions for whatever advertiser T-1 returns ads for
- T-4: Graph API page node for Tadewald + Ivangelica

**Day 2 target** (requires T-1 to have returned at least one advertiser with
ads):
- T-3: field population audit on a real ad set
- T-6: batch creative download on EC2 (10 ads → S3)

---

## GO / NO-GO Decision Matrix per UI Card Field

| UI Card section | Depends on | GO condition | NO-GO consequence |
|---|---|---|---|
| **Ad portfolio** (total, active, longevity) | T-1 pass | `search_page_ids` returns ads | Section shows "unavailable" or requires Playwright scrape |
| **Spend estimate** | T-2 pass | `spend` non-null for BR | Remove spend section from UI card for BR advertisers |
| **Impressions / CPM** | T-2 pass | `impressions` non-null for BR | Remove |
| **Creative mix %** | T-1 + T-3 pass | `media_type` ≥ 80% populated | Show only for ads where field present |
| **Platform distribution %** | T-1 + T-3 pass | `publisher_platforms` ≥ 80% populated | Show only where present |
| **Copy angles (Claude)** | T-1 + T-3 pass | `ad_creative_bodies` ≥ 80% populated | Show only where present |
| **Facebook followers** | T-4 OR T-5 pass | Either Graph API or Playwright extracts it | Omit from card |
| **Page creation date** | T-4 OR T-5 pass | Either Graph API or Playwright extracts it | Omit from card |
| **Instagram handle + followers** | T-5 pass | Playwright extracts from "Sobre" tab | Omit from card — no API alternative |
| **Andromeda Score** | T-1 + T-6 pass | Batch download works + Claude scoring (Phase 2) | Score section hidden until pipeline live |
| **Creative download to S3** | T-6 pass | ≥ 8/10 batch success + S3 upload confirmed | Keep pipeline on EC2 only until confirmed |

---

## Explicit Non-Goals for This Feasibility Phase

The following are **out of scope** until the above tests complete:

- Implementing the Competitor Onboarding Flow in any Lambda or EC2 handler
- Adding Playwright to the Lambda layer or building a container image Lambda
- Building the UI card component in Vue
- Running Claude copy-angle classification at scale
- Phase 2 batch creative download at > 10 ads
- Proxy integration (only relevant if T-6 triggers CAPTCHA)
- Spend estimation workarounds (e.g. scraping third-party tools)

---

## Test Result Recording

Each test result must be recorded in a companion file:
`aws_feasibility/docs/RESULTS-COMPETITOR-INTELLIGENCE-CARD.md`

Format per test:

```
### T-N — [Test name]
Date: YYYY-MM-DD
Outcome: PASS / FAIL / PARTIAL
Key finding: [one sentence]
Raw output: [paste or link]
Impact on UI card: [which fields are confirmed / removed]
```

---

**Document version**: 1.0
**Date**: 2026-03-11
**Status**: Plan only — no tests run yet
**Next action**: Run T-1, T-2, T-4, T-5 locally (day 1)
