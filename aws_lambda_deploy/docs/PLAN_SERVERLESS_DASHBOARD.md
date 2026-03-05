# Plan: Rate Limit Monitoring Dashboard + Bug Fixes

## Context

Meta Ad Library API uses **200 req/hour per access token**. All keyword searches failed because the EventBridge scheduler fires all niche workers simultaneously (3 niches × multiple keywords = rate limit blown in one burst). Additionally: (1) error code #613 (rate limit) is mishandled, showing "Unknown" instead of a clear message; (2) the FB access token still appears in CloudWatch error tracebacks.

This plan adds full observability (line chart, global history table, threshold alert), then fixes the root causes.

**User's priority order:** Admin dashboard first → then bug fixes.

---

## Phase 0: Admin Access Control (Clerk publicMetadata)

**Goal:** Only users with `role: "admin"` in Clerk can access admin routes — managed entirely in Clerk Dashboard, zero deploys needed to add/remove admins.

### One-time Clerk setup (manual, no code)
1. **Clerk Dashboard → Configure → JWT Templates → Default** — add this claim:
   ```json
   { "metadata": "{{user.public_metadata}}" }
   ```
2. **Clerk Dashboard → Users → [your account] → Edit public metadata**:
   ```json
   { "role": "admin" }
   ```
3. Sign out and back in for the new claim to appear in tokens.

To add future admins: repeat step 2 for any user — no code deploy needed.

### 0a. `lambda_src/authorizer/handler.py`
Extract `role` from the `metadata` claim and forward it in the authorizer context:
```python
metadata = payload.get("metadata", {}) or {}
role = metadata.get("role", "user")

return {
    "isAuthorized": True,
    "context": {
        "user_id": user_id,
        "session_id": payload.get("sid", ""),
        "role": role,          # ← new: "admin" or "user"
    },
}
```

### 0b. `lambda_src/niches/handler.py`
Add helper and guard all admin endpoints:
```python
def _get_role(event: dict) -> str:
    return (
        event.get("requestContext", {})
             .get("authorizer", {})
             .get("lambda", {})
             .get("role", "user")
    )

# In every admin endpoint:
if _get_role(event) != "admin":
    return _response(403, {"success": False, "error": "Admin access required"})
```

### 0c. `frontend/src/router/index.js`
Add `requiresAdmin: true` to the admin route meta and guard in `beforeEach`:
```javascript
// Route:
{ path: '/admin/collection-health', meta: { requiresAuth: true, requiresAdmin: true } }

// Guard (after isSignedIn check):
if (to.meta.requiresAdmin) {
  const { sessionClaims } = useAuth()
  const role = sessionClaims.value?.metadata?.role
  if (role !== 'admin') {
    next({ name: 'NicheSelector' })
    return
  }
}
```

---

## Phase 1: Track API Requests per Worker Run

**Goal:** Know how many HTTP requests each worker made — the missing data that drives everything else.

### 1a. `meta_api_collector.py` (Lambda Layer)
- Change `search_ads()` to **return `(ads, requests_made)`** instead of just `ads`
- Increment a local counter for each HTTP GET inside the pagination loop
- No change to error paths

### 1b. `app/models.py` (Lambda Layer)
- Add field to `CollectionRun` dataclass:
  ```python
  api_requests_made: int = 0
  ```
- Update `to_item()` and `from_item()` to serialize/deserialize it

### 1c. `app/dynamodb/collection_repo.py` (Lambda Layer)
- Update `mark_completed()` signature to accept `api_requests_made: int = 0`
- Add it to the UpdateItem expression

### 1d. `collect_worker/handler.py`
- Unpack `(raw_ads, requests_made)` from `api.search_ads()`
- Pass `requests_made` to `CollectionRepo.mark_completed()`

---

## Phase 2: Hourly Rate-Limit Counter in DynamoDB

**Goal:** Atomic, global, per-hour bucket tracking total Meta API requests across all workers.

### 2a. New DynamoDB item type `RATE_WINDOW`
```
PK = SYSTEM
SK = RATE#2026-03-05T06   (one item per UTC hour)
entity_type = RATE_WINDOW
total_requests = N          (atomic counter)
alert_sent = False          (flag: alert already fired this hour)
ttl = <unix_ts 7 days out> (auto-expire via DynamoDB TTL)
```

### 2b. New `app/dynamodb/rate_limit_repo.py` (Lambda Layer)
Methods:
- `increment(hour_str: str, n: int) -> int` — `UpdateItem` with `ADD total_requests :n`, returns new total
- `list_recent(hours: int = 48) -> List[dict]` — Query `PK=SYSTEM, SK begins_with RATE#` with descending sort, returns `[{hour, total_requests}]`
- `mark_alert_sent(hour_str: str)` — set `alert_sent = True`

### 2c. `collect_worker/handler.py` (updated again)
After marking run completed:
```python
hour_str = datetime.utcnow().strftime("%Y-%m-%dT%H")
new_total = RateLimitRepo.increment(hour_str, requests_made)

# Alert at 80% threshold (160/200)
if new_total >= 160:
    window = RateLimitRepo.get(hour_str)
    if not window.get("alert_sent"):
        RateLimitRepo.mark_alert_sent(hour_str)
        _send_rate_limit_alert(new_total, hour_str)
```

### 2d. Alert delivery via SNS
- `collect_worker` env: add `SNS_ALARM_TOPIC_ARN` (from existing `aws_sns_topic.alarms`)
- `_send_rate_limit_alert()` publishes to SNS topic
- SNS already has email subscription wired — just need `alarm_email` set in `dev.tfvars`

**dev.tfvars change:**
```hcl
alarm_email = "emadruga@gmail.com"
```

**lambda.tf change:** Pass `SNS_ALARM_TOPIC_ARN` env var to `collect_worker`.

---

## Phase 3: New Admin API Endpoints (Backend)

### 3a. `GET /api/admin/rate-limit/history?hours=48`
- In `niches/handler.py` (new function `_get_rate_limit_history`)
- Calls `RateLimitRepo.list_recent(hours=int)`
- Returns: `[{hour: "2026-03-05T06", total_requests: 47}]` for last 48 hours
- No auth scope change needed (existing JWT check is sufficient)

### 3b. `GET /api/admin/collection-runs?hours=24&limit=100`
- In `niches/handler.py` (new function `_get_global_collection_runs`)
- DynamoDB Scan: `FilterExpression = entity_type = COLLECTION_RUN AND started_at >= cutoff`
- Returns all runs across all niches/users, sorted newest-first
- Response shape mirrors per-niche runs but adds `niche_id` field

### 3c. `api_gateway.tf`
Add two routes:
```hcl
GET /api/admin/rate-limit/history  → niches Lambda, JWT
GET /api/admin/collection-runs      → niches Lambda, JWT
```

---

## Phase 4: Frontend Admin Dashboard

**File:** `frontend/src/views/AdminCollectionView.vue`

### 4a. Install Chart.js
```bash
npm install chart.js
```

### 4b. `frontend/src/services/api.js`
Add to `collectApi`:
```javascript
getRateLimitHistory: (hours = 48) => api.get(`/admin/rate-limit/history?hours=${hours}`)
getGlobalRuns: (params = {}) => api.get('/admin/collection-runs', { params })
```

### 4c. Extend `AdminCollectionView.vue` — add two new sections below existing health table

**Section 1: API Requests/Hour Line Chart**
- Chart.js `Line` chart
- X-axis: last 48 hours (UTC hour labels)
- Y-axis: total requests (0–200)
- Red dashed horizontal line at y=160 (alert threshold)
- Red dashed at y=200 (hard limit)
- Data fetched on mount + refresh button
- Current hour shown with a different color dot

**Section 2: Global Collection History Table**
Columns: Timestamp | Niche | Keyword | Countries | Limit | API Reqs | Returned | New | Updated | Status
- Same color-coded status badges as per-niche History tab
- Filter by: last 24h / 48h / 7d (dropdown)
- "Refresh" button

**Section 3: Alert Banner**
- If current-hour bucket ≥ 160: show yellow warning banner at top
- "⚠️ Rate limit at risk: 163/200 requests used this hour"

---

## Phase 5 (A): Daily Email Report at 8pm BRT

**Goal:** Automated daily summary of all collection activity — sent every day at 20:00 BRT (23:00 UTC) to `emadruga@gmail.com` via the existing SNS topic.

### 5a-i. New Lambda: `collect_daily_reporter`
**File:** `lambda_src/collect_daily_reporter/handler.py`

Triggered by EventBridge cron `cron(0 23 * * ? *)`.

**Report contents:**
```
MetaAds Daily Report — 2026-03-05

RATE LIMIT USAGE (last 24h)
  Peak hour: 2026-03-05T14 — 87 requests
  Total requests: 312 / 4800 quota (200/hr × 24h)
  Alerts fired: 0

COLLECTION SUMMARY
  Total runs:      42  (38 completed, 3 failed, 1 running)
  Ads found:       1,840
  New ads:         312
  Updated ads:     1,528

TOP KEYWORDS
  "fitness app for seniors" — 14 runs, 480 ads found
  "desenvolvedor python"    — 12 runs, 390 ads found
  ...

ERRORS (last 24h)
  2026-03-05T06:35 — Rate limit exceeded (3 runs failed)
```

**Implementation:**
- Query `RateLimitRepo.list_recent(hours=24)` → hourly usage
- Scan DynamoDB for `entity_type=COLLECTION_RUN AND started_at >= cutoff`
- Aggregate: total runs, success/fail counts, ads stats, top keywords
- Publish formatted text to SNS topic (`SNS_ALARM_TOPIC_ARN`)

### 5a-ii. Terraform additions
```hcl
# lambda.tf — new Lambda function
resource "aws_lambda_function" "collect_daily_reporter" { ... }

# eventbridge.tf — new daily trigger
resource "aws_cloudwatch_event_rule" "daily_report" {
  schedule_expression = "cron(0 23 * * ? *)"   # 23:00 UTC = 20:00 BRT
}
resource "aws_cloudwatch_event_target" "daily_report" { ... }
```

---

## Phase 5 (B): Bug Fixes

### 5b-i. Fix error #613 (Rate Limit) handling in `meta_api_collector.py`
Currently: 400 errors re-raised as "Meta API error: Unknown" due to exception chaining losing `e.response`.

Fix: explicitly catch status 400 + check error code 613 from response body:
```python
if e.response.status_code == 400:
    body = e.response.json()
    code = body.get("error", {}).get("code")
    if code == 613:
        raise Exception("Meta API rate limit exceeded. Too many requests this hour. Try again later.")
    raise Exception(f"Meta API error: 400")
```

### 5b-ii. Fix token leak in CloudWatch logs (`meta_api_collector.py`)
The full URL with token appears in HTTPError tracebacks. Fix: sanitize before logging:
```python
except requests.exceptions.HTTPError as e:
    safe_url = re.sub(r'access_token=[^&]+', 'access_token=REDACTED', str(e))
    print(f"HTTP error: {safe_url[:300]}")
    # raise clean exception (no URL in message)
```

### 5b-iii. Stagger workers in `collect_scheduler/handler.py`
Add `time.sleep(2)` between keyword workers per niche, `time.sleep(5)` between niches:
```python
for i, keyword in enumerate(niche.keywords):
    _invoke_worker(...)
    if i < len(niche.keywords) - 1:
        time.sleep(2)
# between niches:
time.sleep(5)
```

---

## Files to Modify

| File | Change |
|---|---|
| `lambda_src/authorizer/handler.py` | Extract `role` from JWT metadata, add to context |
| `lambda_layers/shared/python/meta_api_collector.py` | Return `(ads, requests_made)`, fix 613 error, scrub token from logs |
| `lambda_layers/shared/python/app/models.py` | Add `api_requests_made` to `CollectionRun` |
| `lambda_layers/shared/python/app/dynamodb/collection_repo.py` | `mark_completed()` accepts `api_requests_made` |
| `lambda_layers/shared/python/app/dynamodb/rate_limit_repo.py` | **NEW** — hourly counter CRUD |
| `lambda_src/collect_worker/handler.py` | Unpack requests count, update counter, fire alert |
| `lambda_src/collect_scheduler/handler.py` | Add inter-worker sleep (stagger) |
| `lambda_src/collect_daily_reporter/handler.py` | **NEW** — daily summary email Lambda |
| `lambda_src/niches/handler.py` | Add `_get_role()` helper + 2 new admin endpoints + 403 guards |
| `infra/api_gateway.tf` | Add 2 new routes |
| `infra/lambda.tf` | Pass `SNS_ALARM_TOPIC_ARN` env var to collect_worker |
| `infra/dev.tfvars` | Set `alarm_email = "emadruga@gmail.com"` |
| `infra/eventbridge.tf` | Add daily report cron rule `cron(0 23 * * ? *)` |
| `frontend/src/router/index.js` | Add `requiresAdmin` meta + guard in `beforeEach` |
| `frontend/src/services/api.js` | Add `getRateLimitHistory()`, `getGlobalRuns()` |
| `frontend/src/views/AdminCollectionView.vue` | Add chart + global history sections |

---

## Deployment Sequence

1. Package Lambda layer (Python changes): `cd aws_lambda_deploy && ./scripts/package.sh`
2. `terraform apply -var-file=dev.tfvars` (new routes + env vars + alarm_email)
3. Update Lambda function code (`collect_worker`, `collect_scheduler`, `niches`)
4. `npm install chart.js && ./scripts/deploy.sh dev` (frontend)

## Verification

- Trigger a manual collection → check CollectionRun has `api_requests_made > 0`
- Check DynamoDB for `PK=SYSTEM SK=RATE#<current_hour>` item exists
- Hit `/api/admin/rate-limit/history` → returns array with current hour
- Hit `/api/admin/collection-runs` → returns recent runs
- Admin dashboard: chart shows data, global table shows runs
- Trigger enough collections to hit 160 → SNS email fires
- Check CloudWatch logs → no `access_token=` strings in error messages
- Multiple simultaneous manual collections → no more error 613 (staggered)
