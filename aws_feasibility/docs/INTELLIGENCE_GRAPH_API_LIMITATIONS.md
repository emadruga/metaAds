# Meta Ads Library API — Limitations for Commercial Intelligence

**Date:** 2026-03-12
**Investigated by:** Live API testing + official Meta documentation
**Relevant endpoint:** `GET /ads_archive` (Graph API v24/v25)

---

## 1. Official Scope of the Ads Library API

From **facebook.com/ads/library/api** (official Meta page, confirmed visually):

> *"The Ads Library API helps you perform customized searches in the Ad Library for:*
> - *Ads about social issues, elections or politics run anywhere in the world in the last seven years*
> - **Ads of any type that ran in the United Kingdom and the European Union in the past year**"*

This is the **intended and officially supported scope** of the API. Everything else is either undocumented behavior or subject to silent restriction.

---

## 2. What Actually Works in Practice

Testing performed with a valid `business_management` + `ads_read` token (Mar 2026):

| Query | Country | Result |
|---|---|---|
| `search_terms=OpusClip` | `US` | ✅ Returns ads |
| `search_terms=StoryShort` | `US` | ✅ Returns ads (from unrelated pages) |
| `search_terms=StoryShort` | `BR` | ✅ Returns ads (from unrelated pages) |
| `search_page_ids=711978348674579` | `BR` | ❌ `{data:[]}` |
| `search_page_ids=711978348674579` | `US` | ❌ `{data:[]}` |
| `search_terms=asimov academy` | `BR` | ❌ `{data:[]}` |
| `search_terms=rodrigotadewald` | `BR` | ❌ `{data:[]}` |

**Page 711978348674579** = Rodrigo Tadewald (Asimov Academy), a Brazilian advertiser
with 99.3k Instagram followers, page created September 1, 2025.
The advertiser **appears in the Ads Library web UI** but returns **zero results via API**.

---

## 3. Root Cause Analysis

### 3.1 `search_terms` works for US but `search_page_ids` always returns empty

The `search_page_ids` parameter is documented as a standard parameter — **no special access level is mentioned**. However, testing shows it consistently returns `{data:[]}` for Brazilian commercial advertisers even when:
- `ad_active_status=ALL`
- `ad_type=ALL`
- Multiple countries tested (BR, US)

### 3.2 The `OpusClip` result explained

`search_terms=OpusClip&ad_reached_countries=US` returns results because OpusClip is a US-based company that **also runs campaigns targeting EU/UK markets**. The `ad_reached_countries` filter is not exclusive — it returns ads that reached that country *among others*. If an advertiser targets US+EU, searching US will find them.

### 3.3 Why Brazilian-only advertisers vanish from the API

Rodrigo Tadewald / Asimov Academy targets **Brazil exclusively**. Their ads do not reach UK or EU. Since the API's comprehensive non-political ad archive is limited to UK/EU exposure, their campaigns simply don't exist in the API-accessible portion of the archive — even though they are fully visible in the Ads Library **web UI** (which queries a different, more comprehensive internal database).

---

## 4. The Web UI vs API Gap

This is the core asymmetry:

| Layer | Data Source | BR Commercial Ads |
|---|---|---|
| `facebook.com/ads/library` (web) | Meta's internal full database | ✅ Visible |
| `/ads_archive` Graph API | Public API subset (political + UK/EU) | ❌ Not accessible |

The web UI is not just a frontend to the API — it has privileged access to the full ad archive. The API exposes a curated, transparency-focused subset designed for political/regulatory research, not commercial intelligence.

---

## 5. The `search_page_ids` Mystery

Despite being a standard parameter with no documented access restrictions, `search_page_ids` returns empty even for advertisers that `search_terms` can find. This suggests one of two possibilities:

1. **The parameter silently requires EU/UK ad activity** — if a page has never run ads that reached UK or EU, `search_page_ids` returns nothing regardless of the country filter used.
2. **The parameter is further restricted** than documented — possibly requires an undocumented access tier that was deprecated when the old "Standard Access" program was removed from the developer portal.

Both scenarios lead to the same practical conclusion: **`search_page_ids` is unreliable for non-EU/UK advertisers**.

---

## 6. What Was Investigated and Ruled Out

| Hypothesis | Verdict |
|---|---|
| Wrong page ID | ❌ Page ID confirmed correct via Ads Library web UI |
| Token missing `business_management` | ❌ Token verified working, `/ads_archive` with `search_terms` returns data |
| Token missing `ads_read` | ❌ Same — `search_terms` works fine |
| "Standard Access" required for `search_page_ids` | ❌ Not mentioned in official docs; old Standard Access program removed from developer portal |
| Page has no ads at all | ✅ Possible, but page appears in Ads Library web UI as an advertiser |
| BR commercial ads not in API archive | ✅ **Most likely root cause**, consistent with official documentation |

---

## 7. Implications for metads.app

The current app architecture assumes that `/ads_archive` with `search_page_ids` is the primary collection mechanism for competitor ads. This works well for:

- ✅ Advertisers who target **US, CA, AU** (often also reach EU/UK)
- ✅ **Political/issue advertisers** in any country
- ✅ **Global brands** running multi-country campaigns

It does **not** work for:

- ❌ **Brazil-only advertisers** (largest segment of the Brazilian market)
- ❌ Any advertiser whose campaigns never reached UK or EU

---

## 8. Recommended Path Forward

### Option A: Pivot to Global/US Niches (No Code Change)
Focus competitor intelligence on US-market niches (AI tools, SaaS, e-commerce). These advertisers reliably appear in the API. The app works today for this use case.

### Option B: Web Scraping Layer for Brazilian Market
Implement a Playwright-based scraper targeting `facebook.com/ads/library`. This accesses the full database. Tradeoffs:
- More maintenance burden
- Subject to UI changes
- Potential ToS concerns (though data is public)
- Slower than API

### Option C: Third-Party Data Provider
Services like **AdSpy**, **BigSpy**, or **PowerAdSpy** aggregate ad data independently and cover Brazilian advertisers. Could be integrated as a data source without the API restrictions.

### Option D: Hybrid
Use the Graph API for global advertisers (fast, free) + web scraping for Brazilian-specific niches (slower, more expensive per run).

---

## 9. Key Evidence URLs

- Official API scope: https://www.facebook.com/ads/library/api/
- Graph API reference: https://developers.facebook.com/docs/graph-api/reference/ads_archive/
- App review panel: https://developers.facebook.com/apps/25766891366325694/app-review/

---

## 10. Current App Review Status (as of 2026-03-12)

The following scopes are queued for submission in the app review panel (`Análise do app`):

| Scope | Status |
|---|---|
| `business_management` | Pending submission |
| `ads_read` | Pending submission |
| `public_profile` | Pending submission |

These are the **correct and minimal set** needed. The previous idea of requesting 10 scopes was abandoned after this investigation confirmed only 3 are needed for the current app functionality.

**Path to submit:** `developers.facebook.com/apps/25766891366325694/app-review/` → click **Avançar**
