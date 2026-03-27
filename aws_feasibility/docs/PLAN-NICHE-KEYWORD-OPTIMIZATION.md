# Niche Keyword Optimization — Implementation Plan

**Date:** 2026-03-26
**Status:** Draft — pending approval
**Depends on:** Playwright scraper Lambda (deployed), EventBridge scheduler (deployed)

---

## 1. Problem Statement

The current niche ad collection relies entirely on the Meta Graph API `search_terms`
parameter. This produces low-quality results:

- **Spam dominance**: keywords like "women apparel" return novels, vertical soap
  operas, and throwaway ads that ran for 1-2 days.
- **Missing serious advertisers**: brands like Marcella NYC (54 active ads, some
  running 140+ days) return only 2 archived stubs via the API because Meta restricts
  third-party token visibility for non-political commercial ads.
- **No quality signal**: the API has no way to filter by ad longevity, so the user
  gets a firehose of noise with no way to separate real advertisers from junk.

The manual discovery heuristic that *did* work: Google "women apparel" → find a brand
(Marcella NYC) → check Meta Ad Library web UI → confirm 54 active long-running ads.
The key insight is that the **Meta Ad Library web UI** has the full ad archive that
the Graph API hides, and **ad longevity (days_active > 10)** is the strongest
available quality signal.

---

## 2. Proposed Solution

Replace the Graph API keyword search with a **Playwright-based keyword search**
against the Meta Ad Library web UI, combined with an **automated keyword optimization
loop** that tests keyword variations over time and promotes the ones that find the
most quality advertisers.

### 2.1 Core Concept

```
User creates niche "Women Fashion in the US"
  → seeds keyword "women apparel"
  → system searches Meta Ad Library web UI via Playwright
  → filters: only advertisers with at least one ad active > 10 days
  → scores keyword: G = count of quality advertisers found
  → generates variations: "women skirts", "women dresses", "designer women clothing"
  → tests each variation on subsequent EventBridge ticks
  → promotes keywords that find more quality advertisers
  → demotes keywords that find mostly junk
  → over 24-48h, the niche converges on "keywords of the week"
```

### 2.2 What Changes

| Component | Today | After |
|---|---|---|
| Niche ad discovery | Graph API `search_terms` | Playwright keyword search on Ad Library web UI |
| Keyword management | Static (user provides up to 5) | Dynamic: user seeds 1-3, system generates + tests variations |
| Quality filtering | None (all results kept) | `days_active >= 10` gate on advertisers |
| EventBridge schedule | Every 3h, collects ads for all keywords | Two modes: (A) keyword optimization ticks every 30 min, (B) ad collection for promoted keywords every 3h |
| Scraper Lambda | Only does `view_all_page_id` (page-specific) | New mode: `keyword_search` (keyword-based discovery) |

---

## 3. Architecture

### 3.1 New EventBridge Schedule: Keyword Optimizer

A second EventBridge schedule (or a mode flag on the existing one) that fires
every **30 minutes** with **jitter of 0-5 minutes** (implemented in the handler
via random sleep before doing work).

```
EventBridge (every 30 min)
        │
        ▼
  keyword_optimizer Lambda (new, or mode of collect_scheduler)
        │
        ├─ For each niche with keyword_optimization_enabled:
        │     1. Pick one CANDIDATE keyword from the queue
        │     2. Invoke Playwright scraper in keyword_search mode
        │     3. Wait for result (sync invoke, ≤ 120s)
        │     4. Score: G = unique advertisers with any ad days_active > 10
        │     5. Compare to niche's best_score
        │     6. Update keyword state: PROMOTED / COOLING_OFF / RETIRED
        │     7. If no candidates remain: generate new variations
        │
        └─ Stagger: one keyword test per niche per tick
           (avoids Playwright concurrency / Meta detection)
```

### 3.2 Playwright Scraper — New `keyword_search` Mode

Extend the existing `competitors_scraper` Lambda to accept a second invocation mode:

```json
{
    "mode": "keyword_search",
    "keyword": "women apparel",
    "country": "US",
    "max_scroll": 3
}
```

**URL pattern:**
```
https://www.facebook.com/ads/library/
  ?active_status=all
  &ad_type=all
  &country=US
  &search_type=keyword_unordered
  &q=women+apparel
```

**Differences from the existing `page_ads` mode:**

| Aspect | `page_ads` (existing) | `keyword_search` (new) |
|---|---|---|
| URL parameter | `view_all_page_id=<id>` | `search_type=keyword_unordered&q=<keyword>` |
| Result scope | All ads from one advertiser | Ads from many advertisers matching keyword |
| Scroll depth | `max_scroll=6` (load all) | `max_scroll=3` (first ~30-50 ads is enough) |
| Extraction | ad_id, body, start_date, is_active | Same + **page_name** (must add to JS) |
| Return | List of ads cached in DynamoDB | List of ads returned directly to caller |
| Invocation | Async (fire-and-forget) | **Sync** (caller waits for result to score) |

**Key extraction addition**: the `_EXTRACT_JS` must also capture the **advertiser
page name** from each card, since keyword search results contain ads from multiple
pages. The page name is visible in the card DOM above "Patrocinado".

### 3.3 Keyword State Machine

```
                 ┌──────────────────────────────────────────┐
                 │                                          │
                 ▼                                          │
  ┌──────────┐  test   ┌──────────┐  score >= threshold     │
  │ CANDIDATE ├───────→│ TESTING  ├─────────────────────→ PROMOTED
  └──────────┘         └────┬─────┘                          │
       ▲                    │ score < threshold               │
       │                    ▼                                 │
       │             ┌──────────────┐  cooldown expired       │
       │             │ COOLING_OFF  ├─────────→ CANDIDATE     │
       │             └──────┬───────┘                         │
       │                    │ tested 3+ times, never promoted │
       │                    ▼                                 │
       │              ┌──────────┐                            │
       │              │ RETIRED  │                            │
       │              └──────────┘                            │
       │                                                      │
       └───── re-validation (every 48h) ── score dropped ────┘
```

**Scoring formula:**

```python
G = count of unique page_ids with at least one ad where days_active >= 10

noise_ratio = G / total_unique_page_ids   # 0.0 to 1.0

# Promotion threshold: relative to niche's current best
promoted = G >= max(3, niche.best_keyword_score * 0.8)

# Cooling off threshold
cooling_off = G < max(1, niche.best_keyword_score * 0.3)
cooloff_duration = 24 hours

# Retirement
retired = test_count >= 3 and never_promoted
```

The minimum threshold of `G >= 3` means a keyword must find at least 3 quality
advertisers to be considered useful, regardless of what other keywords scored.

### 3.4 Keyword Variation Generation

**Phase 1 — Rule-based (no external dependencies):**

```python
MODIFIERS = {
    "prefix": ["luxury", "affordable", "best", "designer", "vintage",
               "trendy", "handmade", "sustainable", "premium"],
    "suffix": ["online", "shop", "store", "brand", "boutique"],
}

CATEGORY_SYNONYMS = {
    "apparel": ["clothing", "garments", "fashion", "wear", "outfits"],
    "women": ["ladies", "womens", "female"],
    "skirts": ["dresses", "blouses", "tops", "jeans", "pants"],
    # ... expand per niche category
}

def generate_variations(seed_keyword: str, existing: set[str]) -> list[str]:
    """Generate candidate keywords from a seed, excluding already-known ones."""
    words = seed_keyword.lower().split()
    variations = set()

    # Synonym substitution for each word
    for i, word in enumerate(words):
        for syn in CATEGORY_SYNONYMS.get(word, []):
            variant = words[:i] + [syn] + words[i+1:]
            variations.add(" ".join(variant))

    # Modifier prepend/append
    for mod in MODIFIERS["prefix"]:
        variations.add(f"{mod} {seed_keyword}")
    for mod in MODIFIERS["suffix"]:
        variations.add(f"{seed_keyword} {mod}")

    # Remove already-known keywords
    return [v for v in variations if v not in existing]
```

**Phase 2 — Ad-text extraction (deferred, medium effort):**

After collecting quality ads, extract frequently occurring nouns/phrases from their
body text and use those as new keyword candidates. For example, if Marcella NYC's ads
mention "minimalist dresses" and "European handcrafted", those become candidates.

**Phase 3 — LLM-assisted (deferred, low effort but adds cost):**

A single Claude Haiku call: "Given the niche 'Women Fashion in the US' and these
top-performing keywords: [...], suggest 10 new keyword variations to find more
advertisers." Cost: ~$0.002/call, triggered only when rule-based candidates are
exhausted.

---

## 4. DynamoDB Schema

### 4.1 New Entity: NicheKeyword

```
PK = NICHE#<niche_id>
SK = KEYWORD#<keyword_slug>
```

| Field | Type | Description |
|---|---|---|
| `keyword` | S | The search term, e.g. "women skirts" |
| `slug` | S | URL-safe slug of keyword (SK suffix) |
| `status` | S | `CANDIDATE` / `TESTING` / `PROMOTED` / `COOLING_OFF` / `RETIRED` |
| `source` | S | `user_seed` / `synonym` / `modifier` / `ad_extraction` / `llm` |
| `parent_keyword` | S | The seed keyword this was derived from (empty for user seeds) |
| `test_count` | N | Number of times tested |
| `best_score` | N | Highest G ever observed |
| `last_score` | N | Most recent G |
| `noise_ratio` | N | Most recent G / total_advertisers (Decimal) |
| `quality_advertisers` | S | JSON list of page_names with G-qualifying ads |
| `last_tested_at` | S | ISO8601 timestamp |
| `cooloff_until` | S | ISO8601 timestamp (empty if not cooling) |
| `promoted_at` | S | ISO8601 timestamp (empty if never promoted) |
| `retired_at` | S | ISO8601 timestamp (empty if not retired) |
| `created_at` | S | ISO8601 timestamp |

### 4.2 Niche Model Additions

New fields on the existing `Niche` dataclass:

| Field | Type | Default | Description |
|---|---|---|---|
| `keyword_optimization_enabled` | BOOL | `False` | Opt-in flag for the optimization loop |
| `best_keyword_score` | N | `0` | Highest G across all promoted keywords |
| `quality_threshold_days` | N | `10` | Min days_active to count as quality ad |
| `optimization_last_tick_at` | S | `""` | Timestamp of last optimizer run |

### 4.3 Keyword Search Cache

Reuse the existing `SCRAPE_CACHE` pattern but with a keyword-based key:

```
PK = KW_CACHE#<sha256(keyword+country)[:12]>
SK = DATA
ttl = now + 6 hours
```

| Field | Type | Description |
|---|---|---|
| `keyword` | S | The search term |
| `country` | S | Country code |
| `ads` | S | JSON list of scraped ad dicts (with page_name) |
| `ad_count` | N | Total ads in result |
| `quality_count` | N | Ads with days_active >= threshold |
| `unique_pages` | N | Distinct page_ids |
| `quality_pages` | N | Distinct page_ids with quality ads (= G) |
| `scraped_at` | S | ISO8601 |
| `ttl` | N | DynamoDB TTL |

This cache prevents re-scraping the same keyword within 6 hours. The optimizer
checks the cache before invoking Playwright.

---

## 5. Lambda Changes

### 5.1 `competitors_scraper` — Add `keyword_search` Mode

**File:** `lambda_src/competitors_scraper/handler.py`

New handler dispatch:

```python
def handler(event, context):
    mode = event.get("mode", "page_ads")

    if mode == "keyword_search":
        return _handle_keyword_search(event, context)
    else:
        return _handle_page_ads(event, context)  # existing logic
```

The `_handle_keyword_search` function:
- Builds the keyword search URL
- Uses `max_scroll=3` (fewer results needed for scoring)
- Extracts **page_name** in addition to existing fields
- Returns results directly (sync invocation) — does NOT write to `SCRAPE_CACHE`
- The caller (keyword_optimizer) writes to `KW_CACHE` after scoring

**Updated `_EXTRACT_JS`** must capture the advertiser name from each card. In the
Ad Library DOM, the page name appears as a link above "Patrocinado" in each card.
The exact selector needs T-6-style discovery, but the text is reliably present in
`card.innerText` as a line preceding "Patrocinado".

### 5.2 New Lambda: `keyword_optimizer`

**File:** `lambda_src/keyword_optimizer/handler.py`

Triggered by EventBridge every 30 minutes. Lightweight orchestrator:

```python
def handler(event, context):
    # 1. Random jitter (0-300 seconds) to spread load
    jitter = random.randint(0, 300)
    time.sleep(jitter)

    # 2. List niches with keyword_optimization_enabled
    niches = NicheRepo.list_all_with_keyword_optimization()

    for niche in niches:
        # 3. Pick one keyword to test
        candidate = KeywordRepo.get_next_candidate(niche.id)

        if candidate is None:
            # 4. Generate new candidates from promoted keywords
            promoted = KeywordRepo.list_promoted(niche.id)
            _generate_variations(niche, promoted)
            continue

        # 5. Check keyword cache first
        cached = _get_keyword_cache(candidate.keyword, niche.countries[0])
        if cached:
            _score_and_update(niche, candidate, cached)
            continue

        # 6. Invoke Playwright scraper (SYNC, wait for result)
        result = _invoke_scraper_sync(
            keyword=candidate.keyword,
            country=niche.countries[0],
            max_scroll=3,
        )

        # 7. Score and update keyword state
        _score_and_update(niche, candidate, result)

        # 8. Cache the result
        _write_keyword_cache(candidate.keyword, niche.countries[0], result)

        # 9. One keyword per niche per tick — move on
        break  # remove if we want multiple tests per tick
```

**Important**: the Playwright invoke is **synchronous** here. The Lambda timeout for
`keyword_optimizer` should be set to **180 seconds** (3 min) to accommodate:
- Jitter: up to 5 min (done via sleep)
- Playwright scrape: ~30-60s
- DynamoDB operations: < 1s

Actually, with up to 5 min jitter, the Lambda timeout must be **420 seconds** (7 min).
Alternatively, move jitter to EventBridge itself using a flexible time window.

**Better approach for jitter**: use EventBridge Scheduler's `FlexibleTimeWindow`
feature (1-15 min) instead of sleeping inside the Lambda. This avoids paying for
idle Lambda time.

```hcl
resource "aws_scheduler_schedule" "keyword_optimizer" {
  name       = "metaads-dev-keyword-optimizer"
  group_name = "default"

  schedule_expression = "rate(30 minutes)"

  flexible_time_window {
    mode                      = "FLEXIBLE"
    maximum_window_in_minutes = 5
  }

  target {
    arn      = aws_lambda_function.keyword_optimizer.arn
    role_arn = aws_iam_role.scheduler_role.arn
  }
}
```

### 5.3 New Repo: `KeywordRepo`

**File:** `lambda_layers/shared/python/app/dynamodb/keyword_repo.py`

Key operations:

```python
class KeywordRepo:
    @staticmethod
    def get_next_candidate(niche_id: str) -> NicheKeyword | None:
        """Get oldest untested CANDIDATE keyword for a niche."""

    @staticmethod
    def list_promoted(niche_id: str) -> list[NicheKeyword]:
        """All PROMOTED keywords for a niche."""

    @staticmethod
    def list_all(niche_id: str) -> list[NicheKeyword]:
        """All keywords for a niche (any status)."""

    @staticmethod
    def upsert(keyword: NicheKeyword) -> None:
        """Create or update a keyword record."""

    @staticmethod
    def bulk_create_candidates(niche_id: str, keywords: list[str], source: str, parent: str) -> int:
        """Insert multiple CANDIDATE keywords, skipping duplicates. Returns count created."""

    @staticmethod
    def transition_expired_cooloffs(niche_id: str) -> int:
        """Move COOLING_OFF keywords past their cooloff_until back to CANDIDATE."""
```

### 5.4 Changes to Existing `collect_scheduler`

The existing 3-hourly ad collection continues as-is, but with one addition:

For niches with `keyword_optimization_enabled=True`, the collect_scheduler uses
**PROMOTED keywords** (from `KeywordRepo.list_promoted`) instead of the static
`niche.keywords` list. This means the collection automatically benefits from
the optimizer's discoveries without any extra wiring.

```python
# In collect_scheduler handler, when building keyword list:
if niche.keyword_optimization_enabled:
    promoted = KeywordRepo.list_promoted(niche.id)
    keywords = [kw.keyword for kw in promoted]
    if not keywords:
        # Fall back to user seeds until optimizer has promoted something
        keywords = niche.keywords
else:
    keywords = niche.keywords
```

---

## 6. Frontend Changes (Minimal, Phase 1)

### 6.1 Niche Settings

Add a toggle on the niche edit page:

```
[x] Enable keyword optimization
    Quality threshold: [10] days active
```

### 6.2 Keywords Tab on Niche Detail

A new tab (or section) showing:

| Keyword | Status | Score (G) | Noise Ratio | Last Tested | Source |
|---|---|---|---|---|---|
| women apparel | PROMOTED | 7 | 0.58 | 2h ago | user_seed |
| women dresses | PROMOTED | 5 | 0.42 | 4h ago | synonym |
| luxury women apparel | COOLING_OFF | 1 | 0.08 | 6h ago | modifier |
| women skirts | CANDIDATE | — | — | never | synonym |
| women blouses | RETIRED | 0 | 0.00 | 3 tests | synonym |

With actions:
- **Pin**: force a keyword to PROMOTED (user override)
- **Retire**: manually kill a keyword
- **Add**: manually add a candidate keyword

### 6.3 Quality Advertisers Discovery

The keyword optimization loop naturally discovers quality advertisers. Show these
on the niche detail page:

```
Top Advertisers Discovered
──────────────────────────
Marcella NYC        │ 12 active ads │ longest: 143 days │ found via "women apparel"
Reformation         │  8 active ads │ longest:  87 days │ found via "women dresses"
Everlane            │  6 active ads │ longest:  62 days │ found via "sustainable women clothing"

[+ Add as Competitor]  ← one-click to add to competitor tracking
```

This is where **niche discovery and competitor intelligence converge**.

---

## 7. Cost Estimate

### 7.1 Playwright Lambda

| Item | Calculation | Cost/month |
|---|---|---|
| Keyword test scrapes | 48 ticks/day × 1 scrape × 30 days × ~45s × 1024 MB | ~$0.70/niche |
| Ad collection scrapes | If promoted keywords trigger Playwright for collection too (Phase 2) | ~$0.50/niche |
| **Subtotal per niche** | | **~$1.20/month** |

### 7.2 EventBridge + Lambda Orchestration

| Item | Calculation | Cost/month |
|---|---|---|
| EventBridge invocations | 48/day × 30 = 1,440/month | ~$0.00 (free tier) |
| keyword_optimizer Lambda | 1,440 × ~5s × 256 MB | ~$0.02/month |

### 7.3 DynamoDB

| Item | Calculation | Cost/month |
|---|---|---|
| Keyword records | ~50 per niche × ~1 KB = 50 KB/niche | negligible |
| Keyword cache | ~48 writes/day × 30 = 1,440 WCUs | ~$0.01/month |
| Reads | ~1,500 reads/month/niche | negligible (free tier) |

### 7.4 Total

**~$1.25/month per niche** for the optimization loop, dominated by Playwright
Lambda execution time. At 10 niches: **~$12.50/month**.

---

## 8. Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Meta changes Ad Library DOM | Medium (quarterly) | Scraper breaks | Weekly T-6 health check; auto-disable optimization if health check fails |
| Login wall on keyword searches | Medium | Zero results | Detect and abort; mark keyword INCONCLUSIVE; retry with different locale |
| Keyword explosion (too many candidates) | Low | Wasted scrapes | Cap at 50 active keywords per niche; auto-RETIRE after 3 failed tests |
| Playwright Lambda concurrency | Low | Throttled invocations | One keyword per niche per tick; reserved concurrency = 2 |
| Meta IP-blocks headless browsers | Low-Medium | All scrapes fail | EventBridge FlexibleTimeWindow jitter; low request rate (1/30 min); fall back to Graph API |

---

## 9. Fallback: SerpAPI / Google Search Integration

If Playwright keyword search proves insufficient after initial testing (e.g. the
Ad Library web UI keyword search returns poor results for certain niches), the
architecture supports adding a Google-based discovery layer:

```
keyword_optimizer tick:
    1. SerpAPI: search Google for keyword
       → extract Google Ads sponsor domains
       → extract top organic result domains
    2. For each domain: resolve Facebook Page
       (SerpAPI: "site:facebook.com <brand>")
    3. Playwright: scrape their Ad Library page (page_ads mode, not keyword_search)
    4. Score: same G metric
```

This is **additive** — it slots into the same keyword scoring framework. The
`NicheKeyword.source` field tracks whether a keyword's quality advertisers were
discovered via Playwright keyword search or via Google cross-reference.

**SerpAPI cost**: $50/month for 5,000 searches. Sufficient for ~17 niches at
current tick rate. Only pursue this if Playwright-only testing shows poor results
after a 1-2 week trial.

---

## 10. Implementation Phases

### Phase 1 — Playwright Keyword Search (Week 1-2)

**Goal**: Replace Graph API keyword search with Playwright for niche ad discovery.

1. Extend `competitors_scraper` with `keyword_search` mode
   - New URL builder for keyword search
   - Extract page_name from cards (update `_EXTRACT_JS`)
   - Sync invocation support (return results directly)
2. Add `NicheKeyword` model to `models.py`
3. Add `KeywordRepo` to shared layer
4. Manual testing: search "women apparel" via Playwright, verify Marcella NYC appears

### Phase 2 — Keyword Optimizer Lambda (Week 2-3)

**Goal**: Automated keyword testing loop.

5. Create `keyword_optimizer` Lambda function
6. Add EventBridge schedule (30 min, FlexibleTimeWindow 5 min)
7. Implement scoring logic (G metric, noise ratio)
8. Implement state machine transitions (CANDIDATE → PROMOTED / COOLING_OFF → RETIRED)
9. Wire into Terraform (new Lambda, EventBridge, IAM)

### Phase 3 — Variation Generation (Week 3)

**Goal**: System generates keyword candidates automatically.

10. Rule-based synonym/modifier expansion
11. Seed keyword insertion on niche creation (user keywords → PROMOTED status)
12. Generation trigger when candidate queue is empty

### Phase 4 — Integration with Ad Collection (Week 3-4)

**Goal**: Promoted keywords feed into the existing 3-hourly ad collection.

13. Modify `collect_scheduler` to use promoted keywords when optimization is enabled
14. `collect_worker`: option to use Playwright instead of Graph API for ad fetching
15. Keyword cache integration (avoid duplicate Playwright scrapes)

### Phase 5 — Frontend (Week 4-5)

**Goal**: User visibility and control.

16. Niche settings: keyword optimization toggle + quality threshold
17. Keywords tab: table with status, score, actions (pin/retire/add)
18. Quality advertisers discovery section with "Add as Competitor" action

### Phase 6 — Monitoring and Tuning (Week 5-6)

**Goal**: Production readiness.

19. CloudWatch alarms: scraper failure rate, keyword test throughput
20. Weekly T-6 health check integration
21. Tune scoring thresholds based on real data (G minimums, noise ratios, cooloff duration)
22. Ad-text keyword extraction (Phase 2 of variation generation)

---

## 11. Success Criteria

After 2 weeks of running on a "Women Fashion in the US" niche seeded with
"women apparel":

- [ ] System has tested 20+ keyword variations automatically
- [ ] At least 5 keywords are PROMOTED with G >= 3
- [ ] Quality advertisers list includes brands with ads running 30+ days
- [ ] Marcella NYC (or equivalent quality) discovered without manual intervention
- [ ] Noise ratio of promoted keywords is > 0.30 (30%+ of results are quality)
- [ ] Total cost per niche per month is under $2

If these criteria are not met after 2 weeks, evaluate adding SerpAPI as the
Google-based fallback (Section 9).

---

## 12. Files to Create / Modify

| Action | File | Description |
|---|---|---|
| **Create** | `lambda_src/keyword_optimizer/handler.py` | New Lambda: orchestrates keyword testing loop |
| **Create** | `lambda_layers/shared/python/app/dynamodb/keyword_repo.py` | DynamoDB operations for NicheKeyword |
| **Modify** | `lambda_layers/shared/python/app/dynamodb/models.py` | Add `NicheKeyword` dataclass; add fields to `Niche` |
| **Modify** | `lambda_src/competitors_scraper/handler.py` | Add `keyword_search` mode; extract page_name |
| **Modify** | `lambda_src/collect_scheduler/handler.py` | Use promoted keywords when optimization enabled |
| **Modify** | `lambda_src/niches/handler.py` | Seed NicheKeyword records on niche create/update |
| **Create** | `infra/keyword_optimizer.tf` | Terraform: Lambda, EventBridge, IAM, env vars |
| **Modify** | `infra/lambda.tf` | Add `keyword_optimizer` Lambda resource (or new file) |
| **Modify** | `scripts/package.sh` | Package new keyword_optimizer function |
| **Modify** | `frontend/src/...` (TBD) | Keywords tab, optimization toggle, advertiser discovery |
