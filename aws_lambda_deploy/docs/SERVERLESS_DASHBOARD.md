# Global History Dashboard

## What is it?

The **🌐 Global History** button appears in the top navigation bar of the *Your Niches* view for users with the `admin` role. Clicking it opens the **Global History Dashboard** — an admin-only view that gives a cross-niche, platform-wide picture of all Meta Ad Library collection activity and API quota consumption.

It is the operational nerve centre of the system: while each niche workspace shows the collection history *for that niche*, the Global History Dashboard shows everything happening across *all* niches and *all* users, in one place.

---

## What information is available?

### 1. Rate-Limit Usage Chart

A bar chart of Meta API requests made **per hour**, covering the last 24 h, 48 h, or 7 days (selectable).

| Visual cue | Meaning |
|---|---|
| Blue bars | Normal usage |
| Yellow bars | Approaching the alert threshold (≥ 160 req/h) |
| Red bars | At or above the hard limit (≥ 200 req/h) |
| Purple bar | The current hour |
| Dashed amber line | Alert threshold (160 req/h) |
| Dashed red line | Meta API hard limit (200 req/h) |

An **alert banner** appears automatically at the top of the page when the current hour's request count reaches the alert threshold, escalating to a red danger banner when the hard limit is hit.

> **Why does this matter?**
> Meta's Ad Library API enforces a rate limit of roughly 200 requests per hour per access token. Exceeding it causes collections to fail with HTTP 429 errors. The chart makes quota exhaustion visible *before* it blocks real users.

### 2. All Collection Runs Table

A paginated table of every collection run fired across every niche, sorted newest-first.

| Column | Description |
|---|---|
| **Timestamp** | When the run started (local time) |
| **User** | Email address of the user who triggered the run |
| **Niche** | Name of the niche being collected |
| **Keyword** | Primary keyword used in the Meta API search |
| **Countries** | Target country codes (up to 3 shown, then `…+N`) |
| **Solicited** | Number of ads requested from the API (`limit` parameter) |
| **Returned** | Number of ads the API actually returned |
| **New** | Ads that were inserted into DynamoDB for the first time (highlighted in purple) |
| **Updated** | Existing ads whose status changed |
| **API Reqs** | Number of HTTP calls made to the Meta API for this run (yellow ≥ 5, red ≥ 10) |
| **Status** | `completed` / `running` / `pending` / `error` |

The look-back window is adjustable (24 h / 48 h / 7 days). Pagination is cursor-based ("Load more" button); up to 200 rows per page.

---

## Why is it important?

| Concern | What the dashboard shows |
|---|---|
| **Quota management** | Spot when a heavy collection run is consuming a disproportionate number of API requests before the hour's budget is exhausted |
| **Error detection** | Any run with `status = error` and an error message is visible here, across all niches, without having to inspect each niche individually |
| **Multi-user visibility** | When multiple team members trigger collections, this is the only place that shows who ran what and when |
| **Scheduler auditing** | Auto-collect runs fired by EventBridge appear here alongside manual runs, so you can confirm the nightly schedule is actually executing |
| **Capacity planning** | The 7-day chart shows weekly request patterns, making it straightforward to decide whether to spread scheduled runs across off-peak hours |

---

## How to grant a user admin access

There are two methods. **Method A** (env var) is the current default and requires no Clerk configuration. **Method B** (Clerk JWT template) is the "proper" Clerk-native approach.

---

### Method A — `ADMIN_USER_IDS` environment variable (current default)

This method works without any Clerk Dashboard configuration. The authorizer Lambda checks whether the authenticated user's Clerk user ID is in a comma-separated allow-list.

**Step 1 — Find the user's Clerk user ID**

Log in to the [Clerk Dashboard](https://dashboard.clerk.com) → **Users** → click the target user → copy the **User ID** (format: `user_XXXXXXXXXXXXXXXXXXXXXXXX`).

Alternatively, it appears in the authorizer's CloudWatch logs whenever that user signs in:

```bash
aws logs filter-log-events \
  --profile=metads \
  --log-group-name "/aws/lambda/metaads-dev-authorizer" \
  --filter-pattern "ALLOW" \
  --query 'events[*].message' \
  --output text | grep -o 'user=[^ ]*'
```

**Step 2 — Add the ID to `dev.tfvars`**

```hcl
# aws_lambda_deploy/infra/dev.tfvars
admin_user_ids = "user_ABC123,user_DEF456"   # comma-separated for multiple admins
```

**Step 3 — Apply**

```bash
cd aws_lambda_deploy/infra
terraform apply -var-file=dev.tfvars
```

The Lambda environment variable is updated immediately; no code deployment needed.

---

### Method B — Clerk JWT template (Clerk-native, optional)

This embeds the user's role directly in the JWT so it travels with every request and requires no env-var management.

**Step 1 — Configure the JWT template**

Clerk Dashboard → **Configure** → **JWT Templates** → **Default** → add the following claim:

```json
{
  "metadata": "{{user.public_metadata}}"
}
```

Save the template.

**Step 2 — Set the user's role in Clerk**

Clerk Dashboard → **Users** → click the target user → **Public metadata** → set:

```json
{
  "role": "admin"
}
```

**Step 3 — The user signs out and back in**

The new `metadata` claim is baked into the JWT at sign-in time. After re-authenticating the Global History button will appear and the admin API endpoints will respond without errors.

> **Precedence:** Method B (JWT metadata) takes priority. Method A (`ADMIN_USER_IDS`) is the fallback used when no JWT template is configured. Both can coexist; a user is admin if *either* condition is true.

---

## API endpoints (reference)

| Method | Path | Auth | Description |
|---|---|---|---|
| `GET` | `/api/admin/global-history` | admin | All collection runs, paginated, with time-window filter |
| `GET` | `/api/admin/rate-limit/history` | admin | Hourly request counts + current-hour total |

Query parameters for `/api/admin/global-history`:

| Param | Default | Max | Description |
|---|---|---|---|
| `hours` | `24` | `168` | Look-back window |
| `limit` | `50` | `200` | Rows per page |
| `cursor` | — | — | Opaque pagination token from previous response |

Query parameters for `/api/admin/rate-limit/history`:

| Param | Default | Max | Description |
|---|---|---|---|
| `hours` | `48` | `168` | Look-back window |
