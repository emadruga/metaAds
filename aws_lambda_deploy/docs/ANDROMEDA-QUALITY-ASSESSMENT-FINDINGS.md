# Creative Asset Extraction — Investigation Findings

**metads.app | Date: 2026-03-08**

---

## 1. Objective

Extract fresh CDN URLs (thumbnail + MP4 video) for a given Meta ad creative so that:
- V1: The modal reports whether the assets are accessible (thumbs up / down)
- V2: Download buttons for thumbnail and video

Reference ad used throughout: **ID 2162596270894996** (Lost Dutchman Leather Goods, Moda niche, 35 days active — benchmark top performer from `PLAN-CREATIVE-ANDROMEDA-QUALITY-ASSESSMENT.pdf`).

---

## 2. What We Know About the Asset URLs

The reference ad has the following CDN URLs (captured previously via real browser):

**Thumbnail (poster frame):**
```
https://scontent.fsdu40-1.fna.fbcdn.net/v/t39.35426-6/
569066098_1182226610418541_1801287585517399472_n.jpg
?_nc_cat=109&ccb=1-7&_nc_sid=c53f8f
&_nc_ohc=...&oh=...&oe=69B1FA68
```
Host: `scontent.fsdu40-1.fna.fbcdn.net` (Facebook image CDN, region sdu40)

**Video (SD Progressive MP4):**
```
https://video.fsdu40-1.fna.fbcdn.net/o1/v/t2/f2/m412/
AQN0W1TaDC-kVOaoQFKVhgv4p5VfkD2uobE3HgTf7j...mp4
?_nc_cat=101&_nc_sid=8bf8fe&efg=...&oh=...&oe=69B1FBFD
```
Host: `video.fsdu40-1.fna.fbcdn.net` (Facebook video CDN, region sdu40)

**Key properties of CDN URLs:**
- Signed with `oh` (HMAC token) and `oe` (expiry as hex Unix timestamp)
- URLs expire after a few hours — must be fetched fresh at analysis time, never stored
- `oe=69B1FA68` → convert hex to Unix time to check validity before download

---

## 3. Approaches Attempted

### 3.1 Meta Graph API — `ads_archive` endpoint

**Endpoint:** `GET https://graph.facebook.com/v24.0/ads_archive`

**Fields requested:** `id, picture, video_hd_url, video_sd_url, thumbnail_url, image_url, video_url`

**Result:** ❌ Only returns `id` and `ad_snapshot_url`. All media fields silently return nothing.

**Root cause:** Meta does not expose media CDN URLs via the public `ads_archive` Graph API endpoint, regardless of which field names are requested. The `ad_snapshot_url` it returns is the JS-rendered preview page, not a direct asset URL.

---

### 3.2 Raw HTTP fetch of `ad_snapshot_url`

**URL format:** `https://www.facebook.com/ads/archive/render_ad/?id=<AD_ID>&access_token=<TOKEN>`

**Result:** ❌ The page is a React SPA. A plain `requests.get()` (without JS execution) returns 168KB of HTML that contains zero content CDN URLs — only `static.xx.fbcdn.net` CSS/JS asset references.

**Evidence:**
```
.jpg occurrences: 0
.mp4 occurrences: 0
scontent found at index: -1
<video> tags: 0
```

The page body only contains `__DEV__=0` and a `<noscript>` redirect — all ad content is injected by React after JavaScript executes. A Lambda cannot use this approach without a headless browser.

**Note on stored `snapshot_url`:** The `snapshot_url` stored in DynamoDB contains the access token at collection time. When the token rotates, the stored URL returns 400. The URL must be reconstructed with the current token: `render_ad/?id=<AD_ID>&access_token=<CURRENT_TOKEN>`.

---

### 3.3 Meta internal GraphQL endpoint

**Endpoint:** `POST https://www.facebook.com/api/graphql/`

**Discovery method:** Playwright (headless Chromium) loaded the snapshot URL and intercepted all network requests. One GraphQL POST was captured:

```
doc_id: 32740921038887979
fb_api_req_friendly_name: AdLibraryV3DemoAdContentQuery
variables: {"adID": "2162596270894996"}
```

**Result when called via Playwright (real browser session):** ✅ Returns full snapshot JSON:

```json
{
  "data": {
    "ad_library_main": {
      "demo_ad_archive_result": {
        "demo_ad_archive": {
          "ad_archive_id": "2162596270894996",
          "snapshot": {
            "display_format": "VIDEO",
            "videos": [{
              "video_hd_url": null,
              "video_sd_url": "https://video.fsdu40-1.fna.fbcdn.net/...",
              "video_preview_image_url": "https://scontent.fsdu40-1.fna.fbcdn.net/...",
              "watermarked_video_hd_url": null,
              "watermarked_video_sd_url": null
            }],
            "images": [],
            "cards": [],
            "page_name": "Lost Dutchman Leather Goods",
            "display_format": "VIDEO",
            "cta_type": "SHOP_NOW",
            "body": {...},
            "title": "🌵Upgrade Your Everyday Carry"
          }
        }
      }
    }
  }
}
```

**Result when called via plain `requests.post()` (no browser session):** ❌ 400 — Meta returns the generic Facebook error HTML page.

**Root cause:** The GraphQL endpoint requires a full Facebook browser session. The POST body must include anti-CSRF/session tokens that are only present in an active browser session:
- `lsd` — per-request CSRF token
- `jazoest` — form integrity token
- `fb_dtsg` — session token
- `__user`, `__hs`, `__rev`, `__dyn`, `__hsi`, `__s` — session state fields
- `__spin_r`, `__spin_b`, `__spin_t` — revision tracking

These tokens cannot be obtained without first loading the Facebook page in a real browser, executing its JavaScript, and extracting the session state from the DOM/cookies.

---

### 3.4 Frontend iframe approach

**Idea:** Load the snapshot URL in a hidden `<iframe>` inside the modal, wait for React to render, then read the `<video>` and `<img>` elements via JavaScript.

**Result:** ❌ Blocked by `X-Frame-Options: DENY` on the snapshot URL response.

```
X-Frame-Options: DENY
```

The `facebook.com` domain categorically refuses to be embedded in any iframe from any origin.

---

### 3.5 Frontend popup / `window.open` approach

**Idea:** Open the snapshot URL in a new browser tab, inject a content script that reads CDN URLs and sends them back via `postMessage`.

**Result:** ❌ Cross-origin policy prevents the opener from accessing `window.open(...).document` when the loaded page is on a different origin (`facebook.com` vs our domain). `postMessage` would only work if the Facebook page itself sent the message, which it does not.

---

## 4. What Actually Works

### Playwright (headless Chromium) rendering the snapshot URL

When a real browser loads `render_ad/?id=...&access_token=...`:
1. React bootstraps and calls `doc_id=32740921038887979` GraphQL (with session tokens injected into the page's JS)
2. GraphQL returns the full snapshot with `videos[].video_sd_url` and `videos[].video_preview_image_url`
3. React renders `<video poster="...">` and `<source src="...">` into the DOM
4. The CDN URLs are accessible via `document.querySelector('video').src` and `.poster`

**Playwright test confirmed:**
```python
media['videos'] == [{
  'src': 'https://video.fsdu40-1.fna.fbcdn.net/...AQN0W1TaDC....mp4?...',
  'poster': 'https://scontent.fsdu40-1.fna.fbcdn.net/.../569066098_...n.jpg?...'
}]
```
Both match the reference URLs from the doc exactly (fresh signed copies).

---

## 5. Snapshot Data Structure (GraphQL response)

For reference when implementing the Playwright-based extractor:

```
snapshot
├── display_format       "VIDEO" | "IMAGE" | "DCO" | ...
├── videos[]
│   ├── video_hd_url     string | null
│   ├── video_sd_url     string             ← use this (always present for video ads)
│   ├── video_preview_image_url  string     ← thumbnail/poster frame
│   ├── watermarked_video_hd_url  null
│   └── watermarked_video_sd_url  null
├── images[]
│   ├── original_image_url   string         ← for IMAGE ads
│   └── resized_image_url    string
├── cards[]                                 ← for CAROUSEL ads
│   ├── video_hd_url / video_sd_url
│   └── original_image_url / resized_image_url
├── page_name
├── body { text }
├── title
├── cta_type             "SHOP_NOW" | "LEARN_MORE" | ...
├── cta_text
├── link_url
└── page_profile_picture_url
```

---

## 6. Architecture Decision

### Rejected: Lambda runtime Playwright
Running Playwright inside an AWS Lambda at request time requires a ~300MB Chromium layer, cold start of 10–15s, and complex layer management. Not suitable for a real-time modal endpoint.

### Rejected: Frontend iframe / popup
Blocked by `X-Frame-Options: DENY` and cross-origin policy. Cannot read DOM from `facebook.com` pages in the browser.

### Recommended: Playwright at collection time (collect_worker)

Run Playwright **once per ad during collection**, store the CDN URLs in DynamoDB alongside the ad record. The modal then reads from DynamoDB — no runtime Playwright needed.

**Implementation plan:**
1. Add `thumbnail_url` and `video_url` fields to the DynamoDB ad schema
2. In `collect_worker` Lambda, after storing each ad, launch a Playwright step that:
   - Opens `render_ad/?id=<AD_ID>&access_token=<TOKEN>`
   - Waits for `networkidle`
   - Reads `video.src`, `video.poster` from the DOM
   - Stores the URLs (without the `oe` expiry params stripped — note they will expire)
3. The `creative-assets` Lambda endpoint reads the stored URLs and probes them with HEAD
4. If the stored URL has expired (`oe` timestamp < now), trigger a background re-fetch

**Alternative: On-demand Playwright via a dedicated microservice**
A lightweight always-on service (Fly.io, Railway, or a single EC2 t3.nano) running Playwright that accepts `POST /extract?adId=...&token=...` and returns the CDN URLs. The Lambda calls this service synchronously. Cheaper and simpler than a Lambda layer.

---

## 7. Current State of the `creative-assets` Endpoint

The Lambda handler at `lambda_src/ads/handler.py → _get_creative_assets()` currently:
- Calls `POST /api/graphql/` with `doc_id=32740921038887979` via plain `requests`
- **Returns "HTTP error"** because Meta rejects unauthenticated GraphQL calls (no session tokens)
- The modal shows: `⚠️ Snapshot fetch issue: HTTP error`

This code needs to be replaced once the collection-time Playwright approach is implemented.

---

## 8. Next Steps

| Priority | Task |
|---|---|
| 1 | Decide on architecture: collection-time Playwright vs dedicated microservice |
| 2 | Add `thumbnail_url`, `video_url` fields to DynamoDB ad schema |
| 3 | Implement Playwright extraction in `collect_worker` (or microservice) |
| 4 | Update `_get_creative_assets()` to read stored URLs from DynamoDB |
| 5 | Add URL expiry check (`oe` hex timestamp → Unix → compare with `time.time()`) |
| 6 | V2: Add download buttons to `CreativeQualityModal.vue` once URLs are reliably available |

---

*Document created: 2026-03-08 | metads.app — Creative Intelligence for the Andromeda Era*

---

## 9. Possible Alternative Architecture

This is actually a very sound architecture. The core insight: you don't need to *store* the creatives. You need to *score* them. The scoring happens once, the score persists forever, the creative URL expires and nobody cares.

### The pipeline

```
EC2 / local machine (Playwright + Python)
  │
  ├─ 1. Pull list of ads to score from DynamoDB
  │      (filter: is_active=True, days_active >= 14, no score yet)
  │
  ├─ 2. For each ad:
  │      a. Open snapshot_url in Playwright (real browser)
  │      b. Wait for networkidle → DOM has video.src + video.poster
  │      c. Download thumbnail + video frames (0s, 1s, 3s, 10s) to /tmp
  │      d. Send frames + ad copy to Claude API (vision)
  │         → analyzeCreativeAndromeadaQuality() from section 4.2 of the plan doc
  │      e. Receive JSON score: andromeda_score, hook_quality, entity_id_risk, etc.
  │      f. Write score back to DynamoDB (new item: SCORE#<ad_id>)
  │      g. Delete /tmp files
  │
  └─ 3. Loop, respect rate limits
```

### What persists in DynamoDB

```
PK: NICHE#<niche_id>
SK: SCORE#<ad_id>
andromeda_score: 87
hook_quality: { score: 9, observation: "..." }
entity_id_risk: "baixo"
fatigue_risk: "baixo"
estimated_longevity_days: 42
strengths: [...]
weaknesses: [...]
scored_at: "2026-03-08T..."
days_active_at_scoring: 35
```

The creative files are never stored. The score lives forever.

### Why this is clean

- Meta cannot block it — Playwright looks exactly like a human browser
- No Lambda layer bloat — scoring runs on EC2/local, off the critical path
- The serverless app just reads scores from DynamoDB — zero new infrastructure in the Lambda
- Ads can be re-scored periodically (e.g. every 7 days on still-active ads) to track quality drift
- The batch runner can be a simple Python script run manually, or a cron on a t3.small (~$15/month)

### What the frontend gains

The Ad Detail panel can show an Andromeda score badge next to `days_active`, with the full breakdown available in the Creative Quality Modal — replacing the current "asset availability" check with actual intelligence per the scoring rubric in section 4.3 of the plan doc.

### Practical implementation path

1. **Start local** — `score_batch.py` script using `boto3` + Playwright + Claude API
2. **Validate on reference ad** — ID 2162596270894996 (known top performer, 35 days active) should score 85–100
3. **Move to t3.small** once scoring quality is confirmed — add a cron schedule
4. **Add score read endpoint** to the serverless app — `GET /api/niches/{slug}/ads/{ad_id}/score`
5. **Surface scores in frontend** — badge in Ad Detail, filter/sort in Ad Search

The serverless app needs zero changes to benefit from the scoring — just one new read endpoint. The batch scorer is fully decoupled and can be iterated independently.

### Key constraint

The `snapshot_url` stored in DynamoDB embeds the access token at collection time. When the token rotates the URL returns 400. The batch scorer must reconstruct the URL using the current token from Secrets Manager:

```python
snapshot_url = f"https://www.facebook.com/ads/archive/render_ad/?id={ad.meta_ad_id}&access_token={current_token}"
```

### Video download

Once Playwright has rendered the snapshot page, the `<video>` element's `src` is a direct `https://video.fsdu40-1.fna.fbcdn.net/...mp4` URL — a plain HTTPS file, no special auth required at that point. Download and trim with FFmpeg:

```python
# Playwright extracts the URL from the rendered DOM
video_url = await page.evaluate("document.querySelector('video').src")
poster_url = await page.evaluate("document.querySelector('video').getAttribute('poster')")

# Download full MP4 (typically 3–8MB for a 57s SD video)
with requests.get(video_url, stream=True, headers={'User-Agent': '...'}) as r:
    with open('/tmp/ad.mp4', 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

# Trim to first 10 seconds
subprocess.run(['ffmpeg', '-i', '/tmp/ad.mp4', '-t', '10', '-c', 'copy', '/tmp/ad_10s.mp4'])

# Extract frames for Claude vision (0s, 1s, 3s, 10s)
for ts in ['00:00:00', '00:00:01', '00:00:03', '00:00:10']:
    subprocess.run([
        'ffmpeg', '-ss', ts, '-i', '/tmp/ad.mp4',
        '-vframes', '1', '-q:v', '2', f'/tmp/frame_{ts.replace(":","")}.jpg', '-y'
    ])
```

The reference ad is 57 seconds SD at ~1Mbps (~7MB total). Downloading the full file before trimming is the right call — trimming a complete file is cleaner than relying on HTTP Range requests, which depend on the MP4 `moov` atom being at the front of the file (not guaranteed for Facebook's encoding).

### Honest risk assessment

This architecture looks clean on paper, but several things can go wrong when moving from notebook to production:

- **Playwright fingerprinting** — Meta may detect headless Chromium via `navigator.webdriver`, missing browser plugins, or canvas fingerprint mismatches, and serve a CAPTCHA or empty page instead of the ad. Mitigation: `playwright-stealth` patch or using a real Chrome binary instead of Chromium.

- **Rate limiting / IP blocking** — Batch-processing hundreds of ads from a single EC2 IP will likely trigger Meta's bot detection. Mitigation: add random delays (5–15s between ads), rotate requests across multiple IPs or use a residential proxy for the Playwright requests.

- **Session token requirements** — We confirmed that the `render_ad` URL works without a Facebook login session today, but Meta could gate it behind authentication at any time. If that happens, the batch scorer would need a real logged-in Facebook account maintained in Playwright's browser context.

- **CDN URL expiry before download** — The video URL extracted by Playwright is fresh at render time but expires via the `oe` parameter (typically a few hours). If the batch queue is long and an ad sits waiting, its URL may expire before the download step. Mitigation: download immediately after extraction, not in a separate queue step.

- **GraphQL doc_id rotation** — The internal query `doc_id=32740921038887979` is not a public API. Meta can change or retire it in any frontend deploy. Mitigation: periodically re-run the Playwright network capture to detect a new doc_id and update accordingly.

The approach is genuinely viable — Playwright running a real Chromium is the same as a human browser from Meta's perspective. But production reliability will require the mitigations above. Validate thoroughly on the reference ad (ID 2162596270894996) before scaling to batch processing.
