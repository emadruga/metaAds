# Competitor Intelligence — Playwright Fallback Feasibility Tests

**Status:** ✅ Proof of concept complete — ready for Lambda integration planning
**Date:** 2026-03-20
**Tests:** T-5 (Sobre tab), T-6 (Ads tab)
**Scripts:** `aws_feasibility/test_playwright_sobre.py`, `aws_feasibility/test_playwright_ads_tab.py`

---

## 1. Why Playwright?

The Meta Graph API (`/ads_archive`) has two distinct limitations for US/EU commercial
advertisers that cannot be resolved by changing parameters, cascading countries, or
rotating tokens:

| Data point | Graph API | Meta Ads Library web UI |
|---|---|---|
| Active ads for US brands | ❌ Returns 0–2 archived stubs | ✅ Full set (54 for Marcella NYC) |
| Instagram handle | ❌ Not in any ads_archive field | ✅ Sobre tab |
| Instagram followers | ❌ Not returned | ✅ Sobre tab |
| Facebook followers (live) | `fan_count` (often stale) | ✅ Sobre tab |
| Page creation date | ❌ Not returned | ✅ Sobre tab |
| Ad body text (active) | ❌ Throttled for commercial ads | ✅ Ad cards |

**Root cause confirmed empirically** (2026-03-20) via direct curl against
`/v24.0/ads_archive?search_page_ids=195588473845643&ad_reached_countries=US,GB,CA,AU
&ad_active_status=ALL`:

```json
{ "data": [
    { "id": "875716460877776", "ad_delivery_stop_time": "2024-01-05" },
    { "id": "947401359938574", "ad_delivery_stop_time": "2023-04-13" }
  ]
}
```

The same brand shows **~55 active ads** on the public web interface.
This is a Meta policy restriction on third-party token visibility for non-political
commercial ads — not fixable at the API layer.

---

## 2. T-5 — Sobre Tab Scrape

**Goal:** Extract competitor page profile data (page_id, follower counts, IG handle,
page creation date) from the "Sobre" (About) tab of `facebook.com/ads/library`.

### Ground Cases

| Advertiser | page_id | Country | Status |
|---|---|---|---|
| Rodrigo Tadewald / Asimov Academy | `711978348674579` | BR | ✅ All fields extracted |
| Ivangelica | `811525368628016` | BR | ✅ page_id discovered; Sobre fields need wait fix |
| Marcella NYC | `195588473845643` | US | ✅ All fields extracted |

### Key Findings

**Search strategy matters more than expected.**
`search_type=keyword_unordered&country=BR` returns 0 results for US-only brands.
`search_type=page&country=US` finds them immediately. The app's `_search_by_page_name`
was updated to cascade: user-hint country → full `_DISCOVERY_MARKETS` list with
`ad_active_status=ALL`.

**page_id is not in `innerText` for established pages.**
Older/larger pages do not render their numeric page_id in visible text. Three-level
fallback chain implemented:
1. innerText regex (`Identificação da biblioteca: \d+`)
2. Known `page_id` passed by caller
3. JS `innerHTML` regex scan (`page_id[":\s]+(\d+)`)

**"Sobre" tab requires content confirmation before extraction.**
Clicking the tab is not enough — the panel renders asynchronously. A `wait_for_selector`
for known content strings (`text=Identificação`, `text=Página criada`) must fire before
`innerText` is captured. Without this wait, only the navigation header is captured.

**Discovery via keyword search requires an extra click.**
When arriving via `search_type=page` URL, the page shows a results list. Clicking the
advertiser name navigates to `view_all_page_id=XXX` URL. The `page_id` can be extracted
from the new URL or from the JS bundle. Playwright Step C2 handles this automatically.

### Extraction Results — Marcella NYC

```
page_id      : 195588473845643
fb_followers : 88,5 (88.5K)
ig_handle    : marcellanyc
ig_followers : 214,9 (214.9K)
created      : 24 de set de 2011
```

**Result: 9 pass / 0 fail / 0 warn**

### Architecture Impact

T-5 is now integrated into the competitor onboarding flow as a planned enrichment step.
The current two-step flow (Graph API resolve → confirmation modal → save) will gain a
third step:

```
POST /api/competitors/resolve     ← Graph API, finds page_id
   ↓ user confirms modal
POST /api/competitors             ← saves competitor
   ↓ async (background Lambda)
Playwright Sobre scrape           ← enriches fb_followers, ig_handle,
                                     ig_followers, page_created
   ↓
PATCH competitor record in DynamoDB
```

---

## 3. T-6 — Ads Tab Scrape

**Goal:** Scrape ad cards from the Ads tab of a competitor's Ad Library page —
specifically for brands where `search_page_ids` via the Graph API returns fewer
than a useful threshold of results.

### Ground Case

| Advertiser | page_id | Country | Graph API ads | Playwright ads |
|---|---|---|---|---|
| Marcella NYC | `195588473845643` | US | 2 (archived, 2023) | **54** (52 active) |

### Selector Discovery Process

Selectors were identified using the Claude-in-Chrome extension against the live page,
then validated in JavaScript before being written into Playwright:

```javascript
// Top-level card container — confirmed stable across 984 DOM nodes
const cards = document.querySelectorAll('div.xh8yej3');

// Per-card extraction (runs entirely client-side)
const idMatch   = text.match(/Identificação da biblioteca:\s*(\d+)/);
const dateMatch = text.match(/Veiculação iniciada em\s+(.+?)[\n]/);
const isActive  = text.includes('Ativo');
const body      = lines[lines.findIndex(l => l === 'Patrocinado') + 1];
```

**Why `div.xh8yej3` and not a semantic selector?**
Meta's Ad Library has no stable `data-testid` or ARIA attributes on ad cards.
The `xh8yej3` class was consistent across all 54 cards and across multiple page
loads during testing. It is a FB atomic CSS class that changes less frequently
than component-level class names. The extraction JS degrades gracefully — if the
class changes, the `includes('Identificação da biblioteca')` filter catches only
real card elements regardless of class name.

### Scroll Strategy

The page uses infinite scroll. Cards load in batches as the user scrolls.

| Scroll pass | Cards in DOM |
|---|---|
| Initial load | ~8 cards |
| After scroll 1 | 868 |
| After scroll 2 | 941 |
| After scroll 3 | 984 |
| After scroll 4 | 984 (no change — done) |

**Deduplication is essential.** Meta renders multiple DOM nodes per logical ad
(e.g. for variant previews). The JS extraction deduplicates by `ad_id` before
returning. 984 raw nodes → 54 unique ads.

### Extraction Results — Marcella NYC

```
Total unique ads : 54
Active           : 52 (96%)
Inactive         : 2
Body text        : 54/54 (100%)
Result banner    : ~55 resultados ✅

Sample:
  [4197639607176029] 4 de fev de 2026  | Discover Minimalism with an Edge Essentials...
  [1228951535416253] 19 de fev de 2026 | NYC Designed. European Handcrafted.
  [1203237098275531] 3 de mar de 2026  | The Spring Sale Is On. Up To 30% Off Storewide...
```

**Result: 8 pass / 0 fail / 0 warn**

---

## 4. Combined Architecture — Planned Fallback Flow

```
GET /api/competitors/{page_id}/ads
        │
        ▼
  Graph API search_page_ids
        │
        ├─ ≥ threshold results AND has active ads?
        │         │
        │         ▼
        │     Return Graph API ads  ✅ (fast path, works for BR brands)
        │
        └─ < threshold OR all inactive?
                  │
                  ▼
          Playwright T-6 scrape
          (async Lambda, container image)
                  │
                  ▼
              Return scraped ads  ✅ (works for US/EU brands)
```

**Threshold definition (proposed):** trigger Playwright if `len(graph_api_ads) < 5`
OR `all(a['is_active'] == False for a in graph_api_ads)`.

---

## 5. Infrastructure Requirements for Lambda

Playwright + Chromium cannot run in a ZIP-deployed Lambda (250 MB limit unzipped;
Chromium alone is ~280 MB). Options ranked by implementation effort:

| Option | Effort | Notes |
|---|---|---|
| **Lambda container image** (ECR) | Medium | Only competitors Lambda switches to container; rest stays ZIP. Recommended. |
| Remote browser service (Browserless.io / Browserbase) | Low-Medium | External dependency, ~$50–100/mo, no infra change |
| ECS Fargate task | High | Always-on cost, over-engineered for this use case |

**Recommended path:** container image for the competitors Lambda only.
- Base image: `public.ecr.aws/lambda/python:3.12`
- Install Playwright + Chromium at image build time
- Terraform: add `package_type = "Image"`, `image_uri` pointing to ECR repo
- All other Lambdas remain ZIP-deployed — no changes to their Terraform or packaging

---

## 6. Headless Mode Risk

All T-5 and T-6 runs were performed in **headed mode** (`headless=False`).
Meta's JS fingerprints headless Chromium and may serve degraded content or
a login wall.

**Before committing to the Lambda container approach**, T-5 and T-6 must both
be validated in `--headless` mode. Run:

```bash
python aws_feasibility/test_playwright_ads_tab.py --headless
python aws_feasibility/test_playwright_sobre.py --advertiser marcellanyc --headless
```

If headless detection triggers:
- Add `--disable-blink-features=AutomationControlled` launch arg
- Set `navigator.webdriver = false` via `page.add_init_script`
- Consider using `playwright-stealth` package

---

## 7. Selector Drift Risk & T-5/T-6 as Health Checks

Meta rebuilds their frontend regularly. `div.xh8yej3` and the regex patterns
are undocumented and can break silently.

**Mitigation:** run T-5 and T-6 on a schedule as smoke tests.

Proposed EventBridge schedule: **weekly, Mondays 04:00 UTC**

```bash
# Manual health check
python aws_feasibility/test_playwright_sobre.py --advertiser marcellanyc
python aws_feasibility/test_playwright_ads_tab.py --page-id 195588473845643

# Alert if any FAIL in results JSON
```

If either test fails, the Playwright fallback should be disabled (fall back to
Graph API only + surface a warning in the UI) until selectors are patched.

---

## 8. What T-6 Does NOT Yet Scrape

The current T-6 implementation extracts the minimum viable fields. These are
deferred to the Lambda integration phase:

| Field | Status | Notes |
|---|---|---|
| `snapshot_url` | ⏳ Deferred | Requires clicking "Ver detalhes do anúncio" per card — expensive |
| `platforms` | ⏳ Deferred | Platform icons present in DOM, need icon→string mapping |
| `media_type` | ⏳ Deferred | Image/video/carousel detectable from card DOM |
| `cta_text` | ⏳ Deferred | CTA button visible in expanded card view |
| `spend` / `impressions` | ❌ Not available | Not shown in Ad Library web UI for non-political ads |

---

## 9. Files Reference

| File | Purpose |
|---|---|
| `aws_feasibility/test_playwright_sobre.py` | T-5: Sobre tab — page profile scrape |
| `aws_feasibility/test_playwright_ads_tab.py` | T-6: Ads tab — competitor ad card scrape |
| `aws_feasibility/docs/INTELLIGENCE_GRAPH_API_LIMITATIONS.md` | API limitations context |
| `t5_sobre_results.json` | Last T-5 run output (gitignored) |
| `t6_ads_results.json` | Last T-6 run output (gitignored) |

---

## 10. Open Questions Before Lambda Integration

1. **Does headless mode work?** — must validate before writing Lambda code
2. **What is the right threshold** to trigger Playwright vs accept Graph API results?
3. **Sync or async Lambda invocation?** The 29s API Gateway timeout makes async
   (202 Accepted + polling) almost mandatory for the ads scrape path
4. **How long to cache scraped ads?** Playwright scrapes should be cached in DynamoDB
   (e.g. TTL 4h) to avoid re-scraping on every competitor detail view load
5. **Container image CI/CD:** how does the ECR image build fit into the existing
   `scripts/package.sh` + Terraform apply deploy workflow?
