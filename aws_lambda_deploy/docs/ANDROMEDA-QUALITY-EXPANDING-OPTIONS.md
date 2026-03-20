# Andromeda Quality Assessment — Expanding Options
## metads.app — Strategic Intelligence Document

**Session date**: 2026-03-10
**Context**: Building on Phase 1 feasibility success (8/8 tests passed).
This document synthesises the strategic thinking around what becomes possible
once a sustainable Andromeda creative-download pipeline is in place, and how
far metads.app can go in serving agencies that advertise in the Meta ecosystem.

---

## Table of Contents

1. [The Foundation — What Phase 1 Proved](#1-the-foundation--what-phase-1-proved)
2. [The Four Core Metrics — Plain English](#2-the-four-core-metrics--plain-english)
3. [Two-Layer Scoring Architecture](#3-two-layer-scoring-architecture)
4. [What the API Does NOT Deliver — Our Edge](#4-what-the-api-does-not-deliver--our-edge)
5. [Agency Positioning — Pain Points We Can Solve](#5-agency-positioning--pain-points-we-can-solve)
6. [Sample Size Requirements Per Niche](#6-sample-size-requirements-per-niche)
7. [Competitor Intelligence — The page_id Strategy](#7-competitor-intelligence--the-page_id-strategy)
8. [What You Can Extract from a Competitor's page_id](#8-what-you-can-extract-from-a-competitors-page_id)
9. [Pipeline Sustainability — Honest Risk Assessment](#9-pipeline-sustainability--honest-risk-assessment)
10. [Dealing with Established Brand Advertisers](#10-dealing-with-established-brand-advertisers)
11. [Roadmap — Four Tiers of Value Delivery](#11-roadmap--four-tiers-of-value-delivery)

---

## 1. The Foundation — What Phase 1 Proved

Phase 1 of the Andromeda feasibility test (2026-03-10, 8/8 PASS) confirmed the
three hardest unknowns:

| Question | Answer |
|---|---|
| Will Meta block headless Chromium on EC2? | **No** — stealth=True works cleanly |
| Can we extract CDN video/thumbnail URLs from the DOM? | **Yes** — in under 2.6s |
| Can we download the assets without extra auth? | **Yes** — 1.64 MB MP4 + 275 KB JPEG in < 1s |

**Critical infrastructure finding**: For many ads, `video_sd_url` and `video_hd_url`
are returned **directly by the Ad Library API** — Playwright is only required as a
fallback when those fields are absent. This significantly reduces bot-detection risk
because the majority of downloads can happen via direct HTTP, not browser automation.

**Memory profile**: Peak 347 MB on a 2 GB t3.small — leaves room for parallel workers.

**Phase 2 still required**: Batch test of 10 ads with 5–15s random delays to confirm
the pipeline survives consecutive page loads without triggering rate limits.
GO/NO-GO threshold: ≥ 8/10 success → proceed to production cron at 50 ads/day.

---

## 2. The Four Core Metrics — Plain English

Understanding these metrics is essential before building scoring logic or pitching to agencies.

### 🎣 Hook Rate — "Did they stop scrolling?"

**What it measures**: Of everyone who *saw* the ad, how many watched at least 3 seconds?
Three seconds is the threshold where a person actively chose not to keep scrolling.

```
Formula:  Hook Rate = (3-sec views ÷ impressions) × 100

Example:  10,000 impressions → 2,800 watched 3+ seconds → Hook Rate = 28%
```

**What it reveals**: Whether the opening frame, thumbnail, or first line of copy
is doing its job. The algorithm notices a weak hook very fast and stops distributing
the ad.

| Score | Signal |
|---|---|
| 35%+ | 🏆 Elite — keep scaling |
| 30–35% | ✅ Very good |
| 25–30% | 👍 Good |
| < 25% | 🚨 Creative problem — fix the opening |

---

### 🤝 Hold Rate — "Did they stay?"

**What it measures**: Of the people who already stopped to watch (3-sec viewers),
how many watched all the way through (ThruPlay)?

```
Formula:  Hold Rate = (ThruPlays ÷ 3-sec views) × 100

Example:  2,800 stopped to watch → 980 watched to the end → Hold Rate = 35%
```

**What it reveals**: Whether the *story* is compelling enough to maintain attention.
A weak middle section, pacing problem, or irrelevant content for the audience all
show up here.

| Score | Signal |
|---|---|
| 50%+ | 🏆 Excellent storytelling |
| 40–50% | ✅ Strong |
| 25–40% | 👍 Adequate |
| < 25% | 🚨 Narrative is weak |

**Hook vs. Hold combined — the decision matrix:**

```
Great Hook + Great Hold  =  Winner 🏆 — scale it
Great Hook + Bad Hold   =  Clickbait — people bounce after 3 sec
Bad Hook  + Great Hold  =  Irrelevant — nobody gets past the opening
Bad Hook  + Bad Hold    =  Kill it immediately
```

---

### 📉 Retention Curve — "Exactly where did they give up?"

**What it measures**: A timeline showing what percentage of viewers were *still
watching* at each milestone: 25%, 50%, 75%, 95%, 100% of the video.

**Available API fields**: `video_p25_watched_actions`, `video_p50_watched_actions`,
`video_p75_watched_actions`, `video_p95_watched_actions`, `video_p100_watched_actions`

```
Example — 60-second video ad:
  Start (0s)  : 2,800 viewers    ← 3-sec viewers (your Hook Rate base)
  At 25% (15s): 2,100 watching   (75% retention)   ✅ strong
  At 50% (30s): 1,400 watching   (50% retention)   👍 ok
  At 75% (45s):   420 watching   (15% retention)   🚨 CLIFF HERE
  At 100% (60s):  980 ThruPlays
```

The cliff at second 45 is an **exact edit instruction** — something specific died
at that moment. Without the retention curve you only know the ad "didn't perform."
With it, you know to cut the video at 40 seconds or rework that specific section.

---

### 🏅 Quality Rankings — "How does Meta rate you vs. the competition?"

**What it measures**: Meta compares the ad against *all other ads competing for
the same audience* and issues three comparative rankings.

| API Field | What it measures |
|---|---|
| `quality_ranking` | Perceived creative quality (visual, copy, no clickbait) |
| `engagement_rate_ranking` | Expected engagement rate vs. competing ads |
| `conversion_rate_ranking` | Expected conversion rate vs. competing ads |

**Possible values**: `ABOVE_AVERAGE`, `AVERAGE`, `BELOW_AVERAGE_10`,
`BELOW_AVERAGE_20`, `BELOW_AVERAGE_35`

**Why it directly affects cost**: Meta's auction is not purely bid-based. An ad
with `BELOW_AVERAGE_35` quality ranking will be out-competed by a *lower-bidding*
advertiser whose creative scores better. Better rankings = lower CPM = more reach
per dollar spent.

> ⚠️ These fields only appear once the ad has sufficient impression volume, and
> are only available for your own ads via the Marketing API — not for competitor
> ads via the Ad Library API. For competitor creatives, **longevity is the proxy**.

---

## 3. Two-Layer Scoring Architecture

The Andromeda score combines quantitative signals (Meta API, free) with qualitative
signals (Claude API vision, paid but controlled).

```
┌─────────────────────────────────────────────────────────┐
│  LAYER 1 — META API  (quantitative, 100% free)          │
│                                                         │
│  Hook Rate    Hold Rate    Retention Curve              │
│  Quality Rankings    Creative Breakdown    Frequency    │
│  CTR / CPA / ROAS    Spend    Days Active  Impressions  │
│                                                         │
│  → Numeric score against known benchmarks              │
│  → Available immediately, zero marginal cost           │
│  → 100% reliable — real performance data               │
└──────────────────────────┬──────────────────────────────┘
                           │ combines with
┌──────────────────────────▼──────────────────────────────┐
│  LAYER 2 — CLAUDE API  (qualitative, controlled cost)   │
│                                                         │
│  Entity ID Risk    Concept/Angle    Visual Diversity    │
│  Persona Signal    Hook Quality     Brief Generation    │
│  Similarity Score  Fatigue Predict  Recommendations     │
│                                                         │
│  → Applied to thumbnail/frames from Andromeda pipeline │
│  → Enriches quantitative score with context            │
│  → Triggered only for new or audited creatives         │
└─────────────────────────────────────────────────────────┘
```

### Combined Score Formula (0–100)

```python
final_score = (
    hook_score          * 0.25 +   # Hook Rate percentile
    hold_score          * 0.20 +   # Hold Rate percentile
    longevity_score     * 0.15 +   # Days active as performance proxy
    quality_score       * 0.15 +   # Meta quality_ranking mapped to 0-100
    entity_id_risk      * 0.15 +   # Claude: similarity risk score
    concept_clarity     * 0.10     # Claude: angle/persona clarity score
)
```

**Important**: For competitor ads (Ad Library), Hook Rate and Hold Rate are
unavailable. The score relies on `longevity_score` + `quality_ranking` (when
visible) + both Claude fields. The score is still meaningful but carries a
lower confidence flag.

---

## 4. What the API Does NOT Deliver — Our Edge

These are the gaps that no tool currently fills — the foundation of our value proposition:

| Gap | Why It Matters | Our Solution |
|---|---|---|
| **Competitor creative download** | You can't see what a competitor's ad looks like in detail | Andromeda pipeline (Playwright + CDN download) |
| **Pre-launch scoring** | No way to predict quality before spending money | Andromeda score against niche benchmarks |
| **Conceptual angle classification** | Meta doesn't tell you *what idea* the ad is selling | Claude API on thumbnail + copy |
| **Entity ID / Similarity Risk** | Similar-looking ads inflate CPM — API doesn't warn you | Claude visual similarity scoring |
| **Portfolio diversity audit** | No diversity score across a whole ad account | Aggregate Claude scoring per account |
| **Fatigue prediction** | API only surfaces fatigue *after* CPM already climbed | Pattern model against historical longevity data |
| **Assist-Impact** | API doesn't show which creative contributed indirectly to conversion | Exposure sequence analysis |
| **Brief generation** | Meta suggests nothing about what to produce next | Claude generation anchored to niche patterns |

---

## 5. Agency Positioning — Pain Points We Can Solve

Agencies managing Meta/Instagram campaigns for clients share four consistent pain points:

### Pain 1: Creative production is the bottleneck, not media buying

Agencies spend 40–60% of their time iterating on creatives with no data to guide
the direction. A **pre-launch quality score** ("this hook will perform below average
for this niche based on 120 similar ads") directly reduces wasted production cycles.

**Feature**: Pre-launch Andromeda score before the first dollar is spent.

---

### Pain 2: They cannot explain to clients *why* ads die

"Your frequency went up" is not a satisfying answer. A diagnosis like *"Entity ID
risk is high — your 6 active video ads are visually too similar; the algorithm is
treating them as one creative and inflating your CPM"* is a deliverable that
justifies the agency's fee.

**Feature**: Portfolio audit with specific, actionable diagnoses.

---

### Pain 3: Competitive monitoring is manual and incomplete

Currently done via the Ad Library web UI — manually, sporadically, by a junior
team member copying screenshots into a slide deck. A niche-aware automated system
that delivers *"competitor X launched 3 new video ads this week — here is the
Andromeda score and concept angle for each"* saves hours and catches things humans miss.

**Caveat**: Named competitor tracking requires a one-time page_id discovery step
(see Section 7). Once the page_id is stored, monitoring is fully automatic and
exhaustive — you see 100% of their ads, not a keyword-filtered sample.

**Feature**: Competitor monitoring dashboard with new-ad alerts.

---

### Pain 4: Brief writing is slow and disconnected from data

Creative briefs are written based on instinct and past experience. Claude-generated
briefs anchored to the top-performing creative patterns in the client's specific
niche turn a 2-hour task into a 10-minute review cycle.

**Feature**: Data-driven brief generation from niche pattern library.

---

## 6. Sample Size Requirements Per Niche

The number of ads needed depends on **which conclusion** you are trying to draw.

### The Three Reliability Thresholds

#### 🟡 Minimum Viable — 50 ads

**Can conclude:**
- Basic pattern recognition (dominant formats, CTA styles, copy tone)
- Obvious outliers (this hook style is unlike the top performers)
- Rough median longevity for the niche

**Cannot conclude reliably:**
- Percentile rankings (P75, P90 unstable at this sample size)
- Sub-segment benchmarks (video vs image, short vs long)
- Saturation of a specific angle

*Analogy: Rating a restaurant from 50 reviews. You get the general picture but
cannot claim it's in the top 10% of the city.*

---

#### 🟢 Sweet Spot — 100–150 ads (rolling 90-day window)

**Can conclude:**
- Reliable median + P25/P75 longevity benchmarks
- Segment by format: ~60–80 videos + ~40–60 image ads
- "Your hook is in the top 30% of video ads in this niche" — statistically defensible
- Angle clustering: 5–8 distinct creative angles typically emerge
- Saturation signal: "3 other advertisers are running this same angle right now"

*Analogy: A doctor diagnosing from 100 patient cases. "80% of cases with this
profile resolve in 3 weeks" is a defensible claim.*

**Why the 90-day window**: Creative trends shift. Ads from 14+ months ago reflect
a different competitive landscape. A living benchmark beats a large stale one.

---

#### 🔵 Strong — 300+ ads

**Can conclude:**
- P90 benchmarks reliable enough to sell as a premium feature
- Sub-segmentation: "top video hooks in fashion for women 25–44" as a distinct cluster
- Trend detection: "UGC testimonials were 40% of top performers 3 months ago, now 65%"
- Cross-advertiser pattern: "Brand X runs a new ad every 21 days — fatigue cycle"
- Early ML classifier training viable (with Claude scores as labels)

---

#### 🏆 ML-Grade — 500+ scored ads

At this volume, there are enough `{ thumbnail, copy, longevity, claude_score }`
pairs to train the CLIP+MLP classifier described in the local model strategy.
Estimated 70–80% reduction in Claude API cost. Niche-specific seasonal pattern
detection becomes viable.

---

### The Hidden Catch: Effective Sample Size Is Smaller Than Total

You cannot compare all ads against each other — you must segment by format:

```
150 total ads in a niche
  ├─ 90 video ads
  │   ├─ 45 short-form (< 30 seconds)  ← real comparison pool for a new 20s video
  │   └─ 45 long-form  (30–60 seconds)
  └─ 60 static/image ads
      ├─ 35 single image
      └─ 25 carousel
```

When a new 20-second video ad arrives, the relevant comparison pool is 45 ads —
not 150. **Rule of thumb: collect 3× your target comparison pool size as total library.**

| Target comparison pool | Total library needed |
|---|---|
| 30 comparable ads | ~90 total |
| 50 comparable ads | ~150 total |
| 100 comparable ads | ~300 total |

---

### Confidence Tiers for the UI

Rather than binary "enough / not enough", display confidence tiers:

| Library Size | UI Label |
|---|---|
| < 30 ads | ⚠️ Benchmark building — limited data |
| 30–80 ads | 🟡 Early signal — directional only |
| 80–200 ads | 🟢 Reliable benchmark — 90-day window |
| 200–500 ads | 🔵 Strong benchmark — format-level scoring |
| 500+ scored | 🏆 Predictive model active |

This turns a data limitation into a feature — agencies see the benchmark improving
over time and have an incentive to stay on the platform.

---

### Seeding Priority

Begin with niches where the Meta Ad Library has the most active ads so you reach
100+ faster. Recommended seeding order:

1. Fashion / accessories / DTC products
2. Fitness / health supplements
3. SaaS / software tools
4. Online courses / education (Brazilian market: very active)
5. Real estate / financial services
6. Thin niches (regional B2B, specialist services) — seed last

---

## 7. Competitor Intelligence — The page_id Strategy

### Why Keyword Search Fails for Named Competitors

The `search_terms` parameter in `/ads_archive` matches against **ad copy text only**.
It does not search advertiser names, page names, or text burned into images. This
means searching "rodrigotadewald" returns nothing — his name never appears in the
ad's text body.

**Compounding problems in Brazilian niches:**
- Brand names appear only in images (e.g., "ASIMOV" is rendered in the thumbnail,
  not the caption text — the API does not OCR images)
- Portuguese keyword variation is wide: the same concept appears as *agentes de IA,
  agentes inteligentes, automação com IA, engenheiro de IA, agentes autônomos*
- Meta's Ad Library returns a **sample** of results, not an exhaustive set —
  specific-niche ads are crowded out by broader "IA" / "inteligência artificial" ads

---

### The Correct Approach: `search_page_ids`

Once you have a competitor's Facebook Page ID, use this parameter instead of
`search_terms`:

```python
params = {
    "access_token": TOKEN,
    "search_page_ids": "711978348674579",   # Rodrigo Tadewald / Asimov
    "ad_reached_countries": "BR",
    "ad_active_status": "ALL",
}
```

This returns **100% of their ads** — active and historical — regardless of what
keywords they use in the copy. It is exhaustive, not sampled.

---

### How to Find a Competitor's Page ID

**Method 1 — Ad Library website (most reliable)**
```
1. Go to https://www.facebook.com/ads/library
2. Search the advertiser name in the web UI
3. Click their page → URL contains: ?advertiser_id=123456789
4. That numeric ID is the page_id
```

**Method 2 — Graph API username lookup**
```
GET https://graph.facebook.com/{username}?fields=id&access_token=TOKEN
```
Works when they have a Facebook Page with a matching username.

**Method 3 — From any ad already found**
Any ad returned by a keyword search includes `page_id` in the payload.
One lucky keyword match gives you the ID permanently.

**Method 4 — Playwright scrape of Ad Library**
Natural extension of the existing Andromeda pipeline: Playwright searches the
Ad Library web UI for the advertiser name and extracts the page_id from the
resulting URL. Fully automatable.

---

### Competitor Onboarding Flow (Product Feature)

```
User inputs: "rodrigotadewald"  (or Instagram handle, or Facebook URL)
      ↓
1. Try: GET /{username}?fields=id  (Graph API — fast, free)
      ↓ (if not found)
2. Playwright opens facebook.com/ads/library → searches name → extracts page_id
      ↓
3. Store: { name, page_id, instagram_handle, niche_id, added_at }
      ↓
4. Every 3h (existing EventBridge scheduler):
   GET /ads_archive?search_page_ids={page_id}&ad_reached_countries=BR
      ↓
5. Alert if new ads detected since last run
```

This is fully buildable on the existing stack — `search_page_ids` calls the same
`/ads_archive` endpoint already in use.

---

## 8. What You Can Extract from a Competitor's page_id

### The API Call

```python
PAGE_ID = "711978348674579"  # Rodrigo Tadewald / Asimov Academy

params = {
    "access_token": TOKEN,
    "search_page_ids": PAGE_ID,
    "ad_reached_countries": "BR",
    "ad_active_status": "ALL",
    "fields": ",".join([
        "id",
        "ad_creation_time",
        "ad_delivery_start_time",
        "ad_delivery_stop_time",       # null = still active
        "ad_creative_bodies",
        "ad_creative_link_titles",
        "ad_creative_link_descriptions",
        "ad_snapshot_url",             # → Andromeda pipeline input
        "publisher_platforms",
        "media_type",
        "spend",                       # 💰 estimated spend range
        "impressions",                 # 👁️ estimated impressions range
        "page_name",
    ]),
    "limit": 100,
}
```

---

### Intelligence Derived from Each Field

#### 💰 `spend` — Budget Intelligence

```json
"spend": { "lower_bound": "1000", "upper_bound": "4999" }
```

Meta discloses spend **ranges** for every ad. Calculated intelligence:

| Metric | How to Compute |
|---|---|
| Total all-time spend estimate | Sum midpoints across all ads |
| Monthly burn rate | Filter `ad_delivery_start_time` to last 30 days |
| Effective CPM | `spend_midpoint / impressions_midpoint × 1000` |
| Budget growth trend | Compare 30d-ago period vs current period |
| Spend per winning ad | Filter ads with longevity ≥ 30 days |

Low CPM (R$5–15) → broad awareness targeting.
High CPM (R$40–80) → tight retargeting or competitive audience.
Unexpectedly low CPM given niche competition → excellent creative quality
rewarded by the Andromeda algorithm with cheaper delivery.

---

#### 📅 `start_time` + `stop_time` — Behavioral Intelligence

**Kill threshold detection**:
```
Ad 1: ran 4 days   → tested, killed
Ad 2: ran 3 days   → tested, killed
Ad 3: ran 41 days  → WINNER — still running
Ad 4: ran 7 days   → tested, killed
```
Reveals their internal decision process: how many days before they pull
an underperformer. If most die before day 7, they test aggressively with
small budgets and scale only proven winners.

**Launch frequency and marketing calendar**:
```
Week 1: 3 new ads
Week 4: 5 new ads   ← course launch week?
```
Spikes in new ad creation correspond to product launches, seasonal pushes,
or campaigns. You can reverse-engineer their marketing calendar.

**Simultaneous active ads**:
6+ concurrent ads = active A/B testing = serious advertiser with real budget.
1–2 concurrent ads = small spend or low testing sophistication.

---

#### 🎬 `media_type` + `ad_snapshot_url` — Creative Strategy

Format distribution across all ads:
```
VIDEO:    65% of ads  ← primary format
IMAGE:    30% of ads
CAROUSEL:  5% of ads
```

Each `ad_snapshot_url` is the input to the **Andromeda pipeline** — downloaded,
frame-extracted, scored by Claude — building a complete creative quality profile
for the competitor.

---

#### 📝 `ad_creative_bodies` — Copy Intelligence

Across all ads, identify:
- **Recurring hooks**: phrases kept across multiple creatives = they work
- **Copy evolution**: messaging changes after a date = earlier version underperformed
- **Angle strategy**: fear ("don't get left behind"), aspiration ("become the
  engineer companies fight over"), social proof ("97k developers already")
- **CTA patterns**: "Saiba mais" vs "Inscreva-se" vs "Vagas limitadas"

---

### Full Competitor Intelligence Card (UI Target)

```
┌─────────────────────────────────────────────────────────┐
│  Rodrigo Tadewald / Asimov Academy                      │
│  Page ID: 711978348674579                               │
│  Page created: Sep 1, 2025  (6 months old)             │
│  Instagram: @rodrigotadewald  →  99.3k followers        │
│  Facebook: 1,200 followers  (Instagram-first advertiser)│
├─────────────────────────────────────────────────────────┤
│  AD PORTFOLIO                                           │
│  Total ads found:         23                           │
│  Currently active:         4   ← running right now     │
│  Avg ad longevity:        12 days                      │
│  Longest-running ad:      41 days  ← their WINNER      │
│  New ads (last 30 days):   7   ← actively testing      │
├─────────────────────────────────────────────────────────┤
│  SPEND ESTIMATE (all time)                              │
│  Minimum:    R$ 28,000                                 │
│  Maximum:    R$ 119,000                                │
│  Last 30 days:  R$ 8,000 – R$ 35,000                  │
├─────────────────────────────────────────────────────────┤
│  CREATIVE MIX                                           │
│  Video: 52%  │  Image: 43%  │  Carousel: 5%            │
│  Avg Andromeda Score: 71/100                           │
│  Best scoring ad:     89/100  (41-day winner)          │
├─────────────────────────────────────────────────────────┤
│  TOP COPY ANGLES (Claude-classified)                    │
│  1. "Engenheiro de Agentes de IA"  (brand/aspirational)│
│  2. "+45h de aulas práticas"       (volume/value)      │
│  3. "Certificado exclusivo"        (credential/status) │
├─────────────────────────────────────────────────────────┤
│  PLATFORM DISTRIBUTION                                  │
│  Instagram: 89%   │   Facebook: 11%                    │
└─────────────────────────────────────────────────────────┘
```

---

## 9. Pipeline Sustainability — Honest Risk Assessment

### The Central Question

Will Meta rate-limit or block the Playwright download pipeline after N consecutive
snapshot page loads from the same EC2 IP?

**Phase 1 answer**: No detection on a single ad test.
**Unknown**: Behaviour at 50 ads/day batch. Phase 2 required.

### Risk Mitigations Already in Place

| Risk | Mitigation |
|---|---|
| EC2 IP fingerprinting | `stealth=True` (playwright-stealth v2 confirmed working) |
| Rate limiting at batch scale | 5–15s random delay between page loads (Phase 2 config C) |
| CAPTCHA on some pages | Residential proxy as fallback (~R$150–250/mo) |
| CDN URLs expiring | ~106h validity window — no urgency to download immediately |
| Full IP block | Proxy rotation + `video_sd_url` direct API fallback |

### The Direct API URL Fallback

This is underappreciated: the Ad Library API already returns `video_sd_url` and
`video_hd_url` for many ads. When these fields are populated, **no Playwright
is needed at all** — just a direct HTTP download. Playwright is only required
when those fields are absent. This means:

- The majority of downloads are low-risk (direct HTTP)
- Playwright sessions are reserved for the minority of ads where direct URLs
  are absent
- The sustainable daily volume is therefore much higher than a pure-Playwright
  approach would suggest

### Sustainable Volume Estimate

| Scenario | Daily capacity | Risk level |
|---|---|---|
| Direct API URL only (no Playwright) | 500+ ads/day | Very Low |
| Mixed (direct URL + Playwright fallback) | 100–200 ads/day | Low |
| Playwright only, 5–15s delays | 50 ads/day | Low-Medium (pending Phase 2) |
| Playwright only, no delays | 200+ ads/day | High — do not use |

---

## 10. Dealing with Established Brand Advertisers

### The Core Observation

Not all advertiser pages display a numeric ID on their Ad Library "Sobre" tab.
The behaviour depends entirely on page age and setup:

| Page type | What the UI shows | Example |
|---|---|---|
| New / small page | `Identificação: 711978348674579` (numeric) | Rodrigo Tadewald (Sep 2025) |
| Old / established page with vanity URL | `@lancomeUS` only | Lancôme US (Jun 2008) |

**The numeric page_id always exists.** Meta stopped surfacing it visually for older
verified pages with vanity usernames — it is a UI presentation difference, not a
data absence. The ID is present in every API response, in the page's HTML source,
and is trivially retrievable via the Graph API.

---

### 5 Methods to Retrieve the Numeric ID

#### Method 1 — Graph API Username Lookup ✅ Best (fast, free, automatable)

```python
def get_page_id_from_username(username: str, token: str) -> str | None:
    """
    Works for any page with a public vanity URL.
    'lancomeUS' → '164617323561910'
    """
    resp = requests.get(
        f"https://graph.facebook.com/{username}",
        params={"fields": "id,name,fan_count,category", "access_token": token}
    )
    if resp.status_code == 200:
        return resp.json().get("id")
    return None
```

Takes ~200ms. Works for virtually every public Facebook Page with a username.
Returns the numeric ID plus useful metadata (follower count, category) in one call.

---

#### Method 2 — Ad Library Keyword Search, Extract from First Result

```python
def get_page_id_from_ad_search(brand_name: str, token: str) -> str | None:
    """
    Search for any ad from this brand — every result includes page_id.
    Useful when the username is unknown or ambiguous.
    """
    resp = requests.get(
        "https://graph.facebook.com/v21.0/ads_archive",
        params={
            "access_token": token,
            "search_terms": brand_name,
            "ad_reached_countries": "US",
            "fields": "page_id,page_name",
            "limit": 10,
        }
    )
    ads = resp.json().get("data", [])
    for ad in ads:
        if brand_name.lower() in ad.get("page_name", "").lower():
            return ad["page_id"]
    return None
```

Even a single matching ad in the results gives you the page_id permanently.
This also handles the case where a brand runs ads under a slightly different
page name than their username (e.g., "Lancôme Paris" vs "lancomeUS").

---

#### Method 3 — Playwright Scrape of Ad Library "Sobre" Tab

Natural extension of the existing Andromeda pipeline. Navigate to the page's
"Sobre" tab and extract either the numeric ID when displayed, or parse the
`advertiser_id` that Meta embeds in the page source HTML.

```python
async def get_page_id_via_playwright(advertiser_name: str) -> str | None:
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        await page.goto("https://www.facebook.com/ads/library/")
        await page.fill('[placeholder*="Pesquise"]', advertiser_name)
        await page.keyboard.press("Enter")
        await page.wait_for_load_state("networkidle")
        content = await page.content()
        # advertiser_id appears in the URL or embedded JSON
        import re
        match = re.search(r'"advertiser_id["\s:]+(\d{10,20})', content)
        if match:
            return match.group(1)
    return None
```

---

#### Method 4 — Facebook Page HTML Source (manual fallback)

Navigate to `facebook.com/lancomeUS`, view page source, search for `"pageID"`.
Meta always embeds the numeric ID in the page's server-rendered HTML.
Useful for one-off lookups, not suitable for automation at scale.

---

#### Method 5 — Third-Party Lookup Tools

Sites like `findmyfbid.com` convert any Facebook URL to a numeric ID.
Useful for manual verification, not automatable for production use.

---

### The Multi-Page Problem for Large Global Brands

This is the more significant challenge that goes beyond just finding the ID.
Large established brands do not have a single Facebook Page — they operate a
**constellation of regional and product-line pages**, each with its own page_id
and its own independent ad campaigns:

```
Lancôme global page ecosystem (illustrative):
  @lancome            → global page          (page_id: AAA)
  @lancomeUS          → US market            (page_id: BBB)  ← shown in screenshot
  @lancomeUK          → UK / Ireland         (page_id: CCC)
  @lancomeAU          → Australia            (page_id: DDD)
  @lancomeCanada      → Canada               (page_id: EEE)
  @lancomeParfums     → fragrance line       (page_id: FFF)
  @lancomeDE          → Germany              (page_id: GGG)
```

A keyword search for "Lancôme" may return ads from three or four of these pages
simultaneously, each identified by a different page_id. If you only monitor
`@lancomeUS`, you miss their global campaigns running from `@lancome`.

**What this means for the product:**

The data model needs a **brand entity layer** sitting above the page_id layer:

```
Brand entity: "Lancôme"
  └─ Pages (multiple):
      ├─ { page_id: "BBB", handle: "lancomeUS",  market: "US",     monitor: true  }
      ├─ { page_id: "AAA", handle: "lancome",    market: "Global", monitor: true  }
      ├─ { page_id: "CCC", handle: "lancomeUK",  market: "UK",     monitor: false }
      └─ { page_id: "FFF", handle: "lancomeParfums", market: "—",  monitor: false }
```

The competitor intelligence card in the UI rolls up data across all monitored
pages for the same brand, while still allowing filtering by individual page/market.
The user controls which pages are actively monitored.

---

### Established Brand Resolution Pipeline (Product Feature)

The competitor onboarding flow must handle both new/small pages (Section 7) and
established brands transparently. The user should never need to understand the
difference:

```
User inputs: "Lancôme"  or  "lancomeUS"  or  facebook.com/lancomeUS
        ↓
STEP 1 — Normalise input
  Strip URL → extract username: "lancomeUS"
  Or keep brand name for fuzzy match: "Lancôme"
        ↓
STEP 2 — Graph API primary lookup (fast, free)
  GET /lancomeUS?fields=id,name,fan_count,category
  → returns page_id, follower count, and category in ~200ms
  → SUCCESS for most established brands with known usernames
        ↓ (if 404 or username unknown)
STEP 3 — Ad Library keyword search fallback
  GET /ads_archive?search_terms="Lancôme"&fields=page_id,page_name&limit=10
  → scan results for exact or close name match → extract page_id
        ↓ (if still not found)
STEP 4 — Playwright Ad Library scrape (last resort)
  → search web UI → extract advertiser_id from URL or page source
        ↓
STEP 5 — Confirm with user (ambiguous name matches)
  "Found: Lancôme US (@lancomeUS) · 11.2M followers · Health/Beauty
   Page created: June 5, 2008
   Is this the right page?  [Confirm]  [Search again]"
        ↓
STEP 6 — Discover related pages (brand constellation)
  Run broader keyword search: "Lancôme"
  Collect ALL unique page_ids that appear across results
  Present: "We also found @lancome (Global, 8.4M followers) and
            @lancomeUK (UK, 2.1M followers) — add to monitoring?"
        ↓
STEP 7 — Store brand entity
  {
    brand_id:   "lancome",
    brand_name: "Lancôme",
    niche_id:   "health-beauty-us",
    pages: [
      { page_id: "BBB", handle: "lancomeUS", market: "US",     active: true  },
      { page_id: "AAA", handle: "lancome",   market: "Global", active: true  },
    ]
  }
        ↓
STEP 8 — EventBridge scheduler queries ALL active page_ids every 3h
  For each page_id: GET /ads_archive?search_page_ids={id}
  Merge results under the brand entity
  Alert on any new ad detected across any of the brand's monitored pages
```

---

### The Special Ad Category Filter Gotcha

The Lancôme screenshot had the filter set to **"Produtos e serviços financeiros"**
(Financial products & services) — a Special Ad Category filter that only shows ads
Meta has flagged as being in restricted categories (housing, credit, employment,
social issues). Lancôme's beauty ads are not in this category, so that filter would
return zero or very few results even though they are actively advertising.

**Product implication**: When a user sets up a competitor and the Ad Library returns
an unexpectedly low ad count, check whether a Special Ad Category filter is active
and warn the user. The correct default for general competitive monitoring is always
**"Todos os anúncios" (All ads)** — no special category restriction.

```python
# Always use ad_active_status=ALL and omit special_ad_categories
# unless the user is specifically monitoring regulated industry advertisers
params = {
    "search_page_ids": PAGE_ID,
    "ad_active_status": "ALL",         # active + historical
    "ad_reached_countries": "US",
    # Do NOT set: "special_ad_categories": "FINANCIAL_PRODUCTS_SERVICES"
}
```

---

### How Established Brands Differ Analytically

Beyond the page_id discovery challenge, large established brand advertisers
behave differently from small/independent advertisers in ways that affect
how the intelligence card should be interpreted:

| Dimension | Small advertiser (Rodrigo Tadewald) | Large brand (Lancôme) |
|---|---|---|
| Pages | 1 page | 5–10+ regional pages |
| Ad volume | 5–30 ads/month | 50–200+ ads/month |
| Testing behaviour | Aggressive kill/scale cycles (7-day threshold) | Longer test windows, seasonal campaigns |
| Spend visibility | Most ads meet Meta's spend disclosure threshold | Some institutional buys may be below threshold |
| Creative production | Individual / small team | Agency-produced, high production value |
| Longevity signal | Strong (longevity = performance) | Weaker (planned campaign end dates, not performance-driven kill) |
| Andromeda score utility | High — score predicts survival | Medium — planned campaigns survive regardless of creative score |

The last point is important: for large brands with planned media budgets, a
30-day-active ad may reflect a booked campaign flight, not organic creative
performance. The longevity-as-quality-proxy is most reliable for
**performance-driven advertisers** (DTC, lead-gen, online courses) where budget
allocation is directly tied to creative results.

---

### Reference: Lancôme US

Used in this section as the established-brand worked example.

| Field | Value |
|---|---|
| Facebook handle | `@lancomeUS` |
| Facebook followers | 11.2 million |
| Page category | Saúde/beleza (Health/beauty) |
| Page created | June 5, 2008 |
| Verified | Yes (blue checkmark) |
| Global parent page | `@lancome` |
| Notable | One of the oldest brand pages on Facebook |
| Longevity signal reliability | Medium (large brand with planned media buys) |
| page_id retrieval method | Graph API username lookup (`GET /lancomeUS?fields=id`) |

---

## 11. Roadmap — Four Tiers of Value Delivery

### Tier 1 — Achievable Now (engineering is clear, data exists)

- Longevity-based quality score for competitor ads (Ad Library + days_active proxy)
- Visual concept/angle classification via Claude on thumbnails
- Niche competitive monitoring with weekly digest
- Portfolio diversity audit for connected accounts (Layer 1 quantitative only)
- Competitor page_id onboarding flow (username → page_id → permanent monitoring)

**Target user**: Single advertiser or small agency wanting competitive awareness.

---

### Tier 2 — After Phase 2 Batch Validation

- Full Andromeda score (Layer 1 + Layer 2) on competitor creatives
- Frame-level hook analysis (FFmpeg extracts seconds 0–3, Claude scores hook quality)
- Fatigue prediction (pattern-match against historical longevity data)
- New competitor ad alerts with Andromeda score attached

**Target user**: Agency managing 3–10 client accounts in one niche.

---

### Tier 3 — Requires Data Accumulation (500+ analyzed pairs)

- Pre-launch creative scoring with confidence interval
- Brief generation anchored to niche-specific winning patterns
- Local CLIP+MLP classifier reducing Claude API cost by 70–80%
- Cross-niche comparison ("this hook angle is already saturated in fashion but
  not yet tried in fitness")

**Target user**: Mid-size agency or in-house team running multiple product lines.

---

### Tier 4 — Long-Term Competitive Moat

- Proprietary benchmark database per niche (what Hook Rate range is "elite" in
  online education vs. SaaS vs. fashion in Brazil)
- Cross-account saturation detection (which creative angles are flooding a niche)
- API access tier (agencies query our benchmark data programmatically)
- White-label reporting for agency-to-client deliverables

**Moat sources**:
1. **Data moat** — historical creative performance database that grows over time
2. **Technical moat** — Andromeda download pipeline (hard to replicate)
3. **Model moat** — scored pairs accumulate into a training dataset competitors
   cannot easily replicate
4. **Network moat** — more agency clients → more niche benchmark data → better
   scores → more agencies

---

### Revised Pitch to Agencies

> *"You give us your competitors' Instagram handles or page names. We do a
> one-time lookup to lock in their Facebook Page ID, then we monitor every
> ad they run — indefinitely, regardless of what keywords they use. When they
> launch a new ad, you get an alert with the creative, the Andromeda quality
> score, and the concept angle. Before spending a dollar on your next creative,
> you see how it scores against 120 ads that already ran in your niche."*

That is stronger than keyword monitoring because it is:
- **Exhaustive** — you see 100% of a named competitor's ads
- **Pre-spend** — you score before launching, not after wasting budget
- **Explainable** — agencies can show clients a number, not just a screenshot

---

## Reference: Rodrigo Tadewald / Asimov Academy

Used throughout this document as a worked example.

| Field | Value |
|---|---|
| Facebook Page ID | `711978348674579` |
| Page name | Rodrigo Tadewald |
| Instagram | @rodrigotadewald |
| Instagram followers | 99,300 |
| Facebook followers | 1,200 |
| Page category | Tutor/professor |
| Page created | September 1, 2025 |
| Brand | ASIMOV Academy |
| Product | Formação Engenheiro de Agentes de IA |
| Notable | Page only 6 months old — aggressive ramp-up |
| Platform bias | Instagram-first (~89% of ad spend estimate) |

---

*Document created 2026-03-10 | metads.app — Creative Intelligence for the Andromeda Era*
*Based on strategic session covering feasibility results, metric definitions,*
*sample size methodology, competitor intelligence architecture, and*
*established brand advertiser handling (Lancôme US as worked example).*
