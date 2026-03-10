# Andromeda Scoring Pipeline — Feasibility Plan

## Document Purpose

This document extends the original `FEASIBILITY_PLAN.md` to cover a specific and more demanding
sub-problem: validating whether **Playwright running on an EC2 instance can reliably extract creative
assets (video + thumbnail) from Meta Ad Library snapshot pages** and whether the full
**Andromeda quality-scoring pipeline** described in section 9 of
`ANDROMEDA-QUALITY-ASSESSMENT-FINDINGS.md` can be operationalised on that same instance.

The original feasibility study validated Meta API connectivity and the data-collection pipeline.
This study validates the *asset extraction + AI scoring* layer that sits on top of it.

---

## Objective

**Primary Goal**: Determine whether an EC2 instance running Playwright + Python + FFmpeg can:

1. Load a Meta Ad Library snapshot page (`render_ad/?id=...&access_token=...`) in a real headless
   Chromium browser without triggering Meta's bot-detection.
2. Extract fresh CDN URLs for video (`video.src`) and thumbnail (`video.poster`) from the rendered
   DOM.
3. Download the video MP4 and extract frame screenshots suitable for Claude vision analysis.
4. Do this reliably across multiple consecutive ads (batch mode) without getting IP-blocked or rate-
   limited into failure.
5. Send the extracted frames + ad copy to the Claude API and receive a structured Andromeda score.
6. Write the score back to DynamoDB and confirm the serverless app can read it through a new
   `GET /api/niches/{slug}/ads/{ad_id}/score` endpoint.

**Reference ad throughout**: ID `2162596270894996` (Lost Dutchman Leather Goods, Moda niche,
35 days active — the benchmark top-performer used in the original findings doc).

**Success Criteria**:

- ✅ Playwright loads the snapshot page and the `<video>` element is present in the DOM
- ✅ `video.src` resolves to a valid `video.fsdu40-*.fna.fbcdn.net` MP4 URL
- ✅ `video.poster` resolves to a valid `scontent.*.fna.fbcdn.net` JPEG URL
- ✅ The MP4 downloads successfully via `requests` (or `wget`) using the extracted URL
- ✅ FFmpeg extracts at least 4 frames (0s, 1s, 3s, 10s) as JPEG files
- ✅ Claude API accepts the frames + ad copy and returns a structured JSON score
- ✅ The score is written to DynamoDB under `PK=NICHE#<id> SK=SCORE#<ad_id>`
- ✅ Running 10 consecutive ads does not trigger a CAPTCHA or empty-page response
- ✅ All of the above runs on a `t3.small` EC2 instance (2 vCPU, 2 GB RAM)

**Non-Goals for this study**:

- Storing or permanently archiving creative files (files are deleted after scoring)
- Modifying the existing `collect_worker` Lambda
- A/B testing proxy vs. no-proxy strategies at scale (that is post-feasibility work)

---

## Background: What Section 9 Proposes

The alternative architecture from the findings doc is a fully decoupled batch process:

```
EC2 / local machine (Playwright + Python + FFmpeg + Claude API)
  │
  ├─ 1. Pull ads to score from DynamoDB
  │      filter: is_active=True, days_active >= 14, score not yet written
  │
  ├─ 2. For each ad:
  │      a. Reconstruct snapshot URL with current token from Secrets Manager
  │      b. Open snapshot URL in Playwright (headless Chromium)
  │      c. Wait for networkidle → DOM has video.src + video.poster
  │      d. Extract CDN URLs from DOM
  │      e. Download MP4 + thumbnail to /tmp
  │      f. FFmpeg: extract frames at 0s, 1s, 3s, 10s
  │      g. Claude API vision: send frames + ad copy → Andromeda score JSON
  │      h. Write score to DynamoDB  PK=NICHE#<id>  SK=SCORE#<ad_id>
  │      i. Delete /tmp files
  │      j. Sleep 5–15s (randomised) before next ad
  │
  └─ 3. Repeat until queue is empty; cron reschedules daily
```

**What persists in DynamoDB** (never the creative files):
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

The serverless app (Lambda + API Gateway) remains unchanged except for one new read-only endpoint.

---

## What We're Testing

### 1. Playwright on EC2 — Bot-Detection Risk

**Key questions**:
- Does headless Chromium on Amazon Linux 2023 (AWS IP range) pass Meta's browser fingerprint
  check, or does it receive a CAPTCHA / login wall?
- Does `playwright-stealth` (patch that spoofs `navigator.webdriver`, canvas fingerprint, plugin
  count) make a material difference?
- What happens after 10, 50, 100 consecutive snapshot-page loads from the same IP?

**Test matrix**:

| Config | Stealth | Delay between ads | Expected outcome |
|---|---|---|---|
| A | No | 0s | Likely detected after N ads |
| B | No | 5–15s random | May survive moderate batches |
| C | Yes | 5–15s random | Best chance — baseline for production |
| D | Yes | 5–15s + residential proxy | Fallback if C fails at scale |

### 2. Snapshot URL Reconstruction

The `snapshot_url` stored in DynamoDB embeds the access token at collection time. When the token
rotates the stored URL returns HTTP 400.

**Test**: Confirm that reconstructing the URL from the current Secrets Manager token works:

```python
# Fetch current token from Secrets Manager
secret = boto3.client('secretsmanager', region_name='us-east-1').get_secret_value(
    SecretId='metaads/dev/meta-api'
)
current_token = json.loads(secret['SecretString'])['access_token']

# Reconstruct URL
snapshot_url = (
    f"https://www.facebook.com/ads/archive/render_ad/"
    f"?id={ad_meta_id}&access_token={current_token}"
)
```

### 3. DOM Asset Extraction

**Test**: After `page.wait_for_load_state('networkidle')`, confirm the expected DOM elements exist:

```python
video_src    = await page.evaluate("document.querySelector('video')?.src")
video_poster = await page.evaluate("document.querySelector('video')?.getAttribute('poster')")
```

Edge cases to validate:
- IMAGE ads (no `<video>` tag — use `<img>` instead)
- CAROUSEL ads (multiple `<video>` or `<img>` elements)
- Ads where the snapshot returns a React error boundary (ad removed / privacy restricted)

### 4. MP4 Download

**Test**: Download the extracted video URL with `requests` (streaming), measure:
- Download time for the reference ad (known ~7 MB, 57s SD)
- Whether the CDN URL accepts the download without extra authentication
- Whether the URL has expired (check `oe` hex timestamp before attempting download)

```python
import time, struct

def is_url_expired(url: str) -> bool:
    import re
    match = re.search(r'[&?]oe=([0-9a-fA-F]+)', url)
    if not match:
        return False
    expiry_unix = int(match.group(1), 16)
    return time.time() > expiry_unix
```

### 5. FFmpeg Frame Extraction

**Test**: Confirm FFmpeg is available on the instance and produces valid JPEG frames:

```bash
ffmpeg -version
ffmpeg -ss 00:00:00 -i /tmp/ad.mp4 -vframes 1 -q:v 2 /tmp/frame_0s.jpg -y
ffmpeg -ss 00:00:01 -i /tmp/ad.mp4 -vframes 1 -q:v 2 /tmp/frame_1s.jpg -y
ffmpeg -ss 00:00:03 -i /tmp/ad.mp4 -vframes 1 -q:v 2 /tmp/frame_3s.jpg -y
ffmpeg -ss 00:00:10 -i /tmp/ad.mp4 -vframes 1 -q:v 2 /tmp/frame_10s.jpg -y
```

Image ads: extract a single frame from the downloaded JPEG (trivial — no FFmpeg needed).

### 6. Claude API Vision Scoring

**Test**: Construct a multi-image message to the Claude API with the 4 frames + ad copy text and
confirm it returns a valid Andromeda score JSON.

Scoring rubric fields to verify are present in the response:
- `andromeda_score` (0–100 integer)
- `hook_quality` (`{ score: int, observation: str }`)
- `entity_id_risk` (`"baixo" | "médio" | "alto"`)
- `fatigue_risk` (`"baixo" | "médio" | "alto"`)
- `estimated_longevity_days` (integer)
- `strengths` (list of strings)
- `weaknesses` (list of strings)

**Expected score for reference ad**: 85–100 (35-day active top performer, per the findings doc).

### 7. DynamoDB Write + Read-Back

**Test**: Write the score item and read it back to confirm the schema is correct.

```python
import boto3, json
from datetime import datetime, timezone

dynamodb = boto3.resource('dynamodb', region_name='us-east-1')
table = dynamodb.Table('metaads-dev-table')

table.put_item(Item={
    'PK': f'NICHE#{niche_id}',
    'SK': f'SCORE#{ad_id}',
    'entity_type': 'SCORE',
    'andromeda_score': score['andromeda_score'],
    'hook_quality': score['hook_quality'],
    'entity_id_risk': score['entity_id_risk'],
    'fatigue_risk': score['fatigue_risk'],
    'estimated_longevity_days': score['estimated_longevity_days'],
    'strengths': score['strengths'],
    'weaknesses': score['weaknesses'],
    'scored_at': datetime.now(timezone.utc).isoformat(),
    'days_active_at_scoring': ad['days_active'],
})
```

Then confirm a `GET` to the new Lambda endpoint returns the same data in the frontend-expected
shape.

### 8. End-to-End Batch Run (10 ads)

The final test: run the full pipeline for 10 ads pulled from a real DynamoDB niche, back-to-back
with randomised 5–15s delays. Measure:
- Success rate (ads successfully scored / total attempted)
- CAPTCHA / detection rate
- Average time per ad (snapshot load + download + scoring)
- Total `/tmp` disk usage at peak (before cleanup)
- Claude API cost per ad (token count × price)

---

## Infrastructure

### Instance Sizing

| Component | Requirement | Reason |
|---|---|---|
| Chromium (headless) | ~350 MB RSS at peak | One browser instance during snapshot load |
| FFmpeg | ~50 MB | Frame extraction |
| Python + deps | ~150 MB | boto3, playwright, requests, anthropic SDK |
| /tmp for one ad | ~30–50 MB peak | 7 MB MP4 + 4 JPEG frames at ~1 MB each |
| **Total** | **~600 MB peak** | |

`t3.micro` (1 GB RAM) is borderline — Chromium alone may OOM under load.
**Recommended instance: `t3.small` (2 GB RAM, 2 vCPU)** — cost ~$0.023/hour, ~$17/month on-demand,
or ~$5/month on a 1-year Savings Plan.

For the feasibility test itself, a `t3.small` with a 20 GB gp3 EBS volume is sufficient.

### Required Software on the Instance

The existing `user_data.sh` needs to be extended to install:

```bash
# Chromium dependencies (Amazon Linux 2023)
sudo dnf install -y \
    chromium \
    nss \
    atk \
    at-spi2-atk \
    cups-libs \
    libdrm \
    libxkbcommon \
    libXcomposite \
    libXdamage \
    libXfixes \
    libXrandr \
    mesa-libgbm \
    pango \
    alsa-lib

# FFmpeg (from rpmfusion or static build)
# Static build is simplest — no dependency conflicts:
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-arm64-static.tar.xz
# (adjust arch for x86_64)
tar xf ffmpeg-release-*.tar.xz
sudo mv ffmpeg*/ffmpeg /usr/local/bin/
sudo mv ffmpeg*/ffprobe /usr/local/bin/

# Python packages
pip install playwright playwright-stealth anthropic boto3 requests
playwright install chromium
playwright install-deps chromium
```

### IAM Permissions Required

The EC2 instance needs an IAM role with:

```json
{
  "Version": "2012-10-17",
  "Statement": [
    {
      "Effect": "Allow",
      "Action": [
        "dynamodb:Query",
        "dynamodb:PutItem",
        "dynamodb:GetItem"
      ],
      "Resource": "arn:aws:dynamodb:us-east-1:*:table/metaads-dev-table"
    },
    {
      "Effect": "Allow",
      "Action": "secretsmanager:GetSecretValue",
      "Resource": [
        "arn:aws:secretsmanager:us-east-1:*:secret:metaads/dev/meta-api*"
      ]
    }
  ]
}
```

The Anthropic API key can be stored either in Secrets Manager (preferred) or in a `.env` file
(acceptable for the feasibility test).

---

## Test Methodology

### Phase 0: Terraform Changes

Extend `aws_feasibility/terraform/` to support the Andromeda test:

1. Change default `instance_type` to `t3.small`
2. Add IAM role + instance profile with the permissions above
3. Extend `user_data.sh` to install Chromium dependencies, FFmpeg, and the new Python packages

### Phase 1: Single Ad — Reference Validation

Run every step manually against ad `2162596270894996`:

```bash
# On EC2 instance, inside venv
python andromeda_single_ad_test.py \
  --ad-id 2162596270894996 \
  --niche-id <niche_id_from_dynamodb>
```

Expected output:
```
[1/7] Fetching current Meta token from Secrets Manager... OK
[2/7] Launching Playwright (stealth=True)... OK
[3/7] Loading snapshot URL... OK (networkidle in 4.2s)
[4/7] Extracting DOM URLs...
       video_src:    https://video.fsdu40-1.fna.fbcdn.net/...mp4?...
       video_poster: https://scontent.fsdu40-1.fna.fbcdn.net/...jpg?...
[5/7] Downloading MP4 (7.3 MB)... OK (3.1s)
[6/7] Extracting frames with FFmpeg... OK (frame_0s.jpg, frame_1s.jpg, frame_3s.jpg, frame_10s.jpg)
[7/7] Sending to Claude API (claude-sonnet-4-6)...
       andromeda_score: 91
       hook_quality: { score: 9, observation: "Opens with a POV shot of the leather good in use" }
       entity_id_risk: "baixo"
       ...OK
[WRITE] Score written to DynamoDB under NICHE#abc / SCORE#2162596270894996
[CLEANUP] /tmp files deleted
Total time: 18.4s
```

### Phase 2: Bot-Detection Matrix (10 ads × 4 configs)

Run the 4 Playwright configs from the test matrix (A–D in the table above) against a set of
10 real active ads from the DynamoDB niche. Record:
- Whether the snapshot page loaded with ad content (pass) or a CAPTCHA / error (fail)
- Time to `networkidle`

### Phase 3: Batch Run Simulation (50 ads)

Using the best-performing config from Phase 2, run a batch of 50 ads. Record:
- Success rate
- CAPTCHA / block events (and at which ad number they first appear)
- Average per-ad wall time
- Peak `/tmp` disk usage
- Total Claude API token usage and estimated cost

### Phase 4: DynamoDB + Frontend Integration

1. Confirm all 50 scores are present in DynamoDB
2. Implement `GET /api/niches/{slug}/ads/{ad_id}/score` in the `ads` Lambda handler
3. Confirm the endpoint returns the score JSON to the frontend
4. Verify `AdDetailPanel.vue` can display a score badge

---

## Success Metrics

### Must Pass (Go/No-Go for Andromeda pipeline)

| # | Check | Pass condition |
|---|---|---|
| 1 | Snapshot loads in Playwright | `<video>` tag present in DOM for video ads |
| 2 | CDN URLs extracted | Both `video_src` and `video_poster` are non-null and not expired |
| 3 | MP4 download | File size > 1 MB, download completes without error |
| 4 | FFmpeg frame extraction | 4 JPEG files, each > 10 KB |
| 5 | Claude API scoring | Response contains all 7 required score fields |
| 6 | DynamoDB write | Score item readable within 1s of write |
| 7 | 10-ad batch success rate | ≥ 8/10 ads scored without CAPTCHA (80%) |
| 8 | Memory stays within bounds | RSS < 1.5 GB at peak on t3.small |

### Performance Targets (Nice to Have)

| Metric | Target |
|---|---|
| Time per ad (end-to-end) | < 30s |
| 50-ad batch success rate | ≥ 45/50 (90%) |
| Andromeda score for reference ad | 85–100 |
| Claude API cost per ad | < $0.05 |
| Estimated monthly cost (50 ads/day) | < $30 total (EC2 + Claude) |

---

## Risk Assessment

| Risk | Likelihood | Impact | Mitigation |
|---|---|---|---|
| Playwright fingerprint detected by Meta | Medium | High | Use `playwright-stealth`; fallback to real Chrome binary |
| IP range block (AWS EC2 IPs) | Low-Medium | High | Use Elastic IP with residential proxy for Playwright requests only |
| `render_ad` page gated behind FB login | Low | High | Maintain a dormant Facebook account in Playwright context |
| CDN URL expired before download | Low | Medium | Check `oe` hex timestamp immediately after extraction; download in same step |
| `doc_id=32740921038887979` rotated by Meta | Low | Medium | Re-run Playwright network capture monthly to detect rotation |
| FFmpeg not available / broken on AL2023 | Low | Low | Use static FFmpeg binary from johnvansickle.com |
| Claude API rate limit during batch | Low | Low | Add exponential backoff; store pending ads in DynamoDB queue |
| t3.small OOM with Chromium | Low-Medium | Medium | Monitor RSS; upgrade to t3.medium ($34/month) if needed |
| DynamoDB write throttle | Very Low | Low | On-demand billing mode absorbs bursts; no change needed |

---

## Test Script Outline

The single-ad test script to be created at `aws_feasibility/andromeda_single_ad_test.py`:

```
Input:
  --ad-id       Meta ad archive ID
  --niche-id    DynamoDB niche ID (for PK construction)
  --stealth     Enable playwright-stealth (default: True)
  --dry-run     Skip DynamoDB write and Claude API call (for DOM extraction testing only)

Steps:
  1. Fetch current FB access token from Secrets Manager
  2. Launch Playwright (async, headless Chromium, stealth if enabled)
  3. Navigate to reconstructed snapshot URL
  4. Wait for networkidle (timeout 30s)
  5. Extract video_src, video_poster from DOM
  6. Assert URLs are non-null and not expired (check oe param)
  7. Download MP4 to /tmp/ad_<id>.mp4
  8. Download thumbnail to /tmp/thumb_<id>.jpg
  9. Run FFmpeg to extract 4 frames to /tmp/frame_<ts>_<id>.jpg
  10. Base64-encode the 4 frames
  11. Construct Claude API message (image blocks + ad copy text)
  12. Call claude-sonnet-4-6, parse response JSON
  13. Validate all 7 required fields present
  14. Write score item to DynamoDB (skip if --dry-run)
  15. Delete all /tmp files
  16. Print summary report
```

The batch script `aws_feasibility/andromeda_batch_test.py` wraps the above in a loop:

```
Input:
  --niche-id    DynamoDB niche ID to pull unscored ads from
  --limit       Max ads to process (default: 10)
  --min-days    Minimum days_active to include (default: 14)
  --delay-min   Minimum inter-ad delay in seconds (default: 5)
  --delay-max   Maximum inter-ad delay in seconds (default: 15)

Steps:
  1. Query DynamoDB for ads: is_active=True, days_active >= min_days, no SCORE# item yet
  2. For each ad (up to limit): run single-ad pipeline with randomised delay
  3. Print batch summary: success count, failure count, avg time per ad
```

---

## Cost Analysis

### Feasibility Test (one-time, 2–4 hours)

| Item | Cost |
|---|---|
| t3.small EC2 (4 hours) | $0.09 |
| EBS 20 GB gp3 (4 hours) | < $0.01 |
| Claude API (50 ads × ~2000 tokens) | ~$0.15 |
| Data transfer (50 ads × 10 MB MP4) | ~$0.04 |
| **Total feasibility test** | **~$0.30** |

### Production (daily cron, 50 ads/day)

| Item | Monthly cost |
|---|---|
| t3.small on-demand (24×7) | $17 |
| t3.small 1-year Savings Plan | ~$11 |
| EBS 20 GB gp3 | $1.60 |
| Claude API (50 ads/day × 30 days × $0.05/ad) | $75 |
| **Total/month** | **~$88 on-demand / ~$78 Savings Plan** |

**Cost optimisation**: Run the cron only during off-peak hours; spot instance with on-demand
fallback can cut EC2 cost to ~$5/month. Claude API cost dominates — reducing frame count from
4 to 2 frames per ad saves ~40% on vision token cost.

---

## Deliverables

After completing all four test phases, produce `aws_feasibility/docs/ANDROMEDA_FEASIBILITY_RESULTS.md` containing:

1. Pass/fail result for each of the 8 must-pass checks
2. Bot-detection matrix results (Phase 2)
3. 50-ad batch metrics (Phase 3)
4. Observed Andromeda score for reference ad `2162596270894996`
5. Go/No-Go recommendation for production deployment
6. Infrastructure changes required before production (Terraform diffs, IAM policy additions)
7. Open questions / risks to address before scaling beyond 50 ads/day

---

## Relationship to the Existing Feasibility Infrastructure

This study **reuses** the existing `aws_feasibility/terraform/` infrastructure with the following
additions:

| Change | Where |
|---|---|
| `instance_type = "t3.small"` | `terraform.tfvars` |
| IAM role + instance profile | New resource block in `main.tf` |
| Extended `user_data.sh` | Install Chromium, FFmpeg, new Python deps |
| New test scripts | `aws_feasibility/andromeda_single_ad_test.py`, `andromeda_batch_test.py` |
| Results doc | `aws_feasibility/docs/ANDROMEDA_FEASIBILITY_RESULTS.md` |

No changes are needed to the production Lambda stack, DynamoDB schema (new item type is additive),
API Gateway, or CloudFront until Phase 4 (the new read endpoint). The batch scorer is fully
decoupled — it can be iterated independently of the serverless app.

---

## Decision Tree

```
Phase 1 (single ad) result
    │
    ├─ PASS → continue to Phase 2
    │
    └─ FAIL (DOM empty / CAPTCHA)
        ├─ Try playwright-stealth → re-run Phase 1
        └─ Still failing → snapshot URL gated behind login?
               → test with a real Facebook session in Playwright context

Phase 2 (bot-detection matrix)
    │
    ├─ Config C (stealth + delay) succeeds at 10 ads → use as production config
    ├─ Config C fails, Config D (stealth + proxy) succeeds → add proxy to production
    └─ All configs fail at < 10 ads → revisit architecture (dedicated service + rotating IPs)

Phase 3 (50-ad batch) success rate
    │
    ├─ ≥ 90% → ✅ PROCEED to production cron on t3.small
    ├─ 70–89% → ⚠️  Add proxy rotation; re-run Phase 3
    └─ < 70% → ❌ Batch approach not viable as-is; consider on-demand scoring
                  (trigger per ad on collection, not in a batch cron)

Phase 4 (DynamoDB + frontend)
    │
    └─ Score badge visible in AdDetailPanel → ✅ Full pipeline validated
```

---

**Document Version**: 1.0
**Date**: 2026-03-09
**Author**: MetaAds Team
**Status**: Ready for Implementation
**Depends on**: `ANDROMEDA-QUALITY-ASSESSMENT-FINDINGS.md` section 9, `FEASIBILITY_PLAN.md`
