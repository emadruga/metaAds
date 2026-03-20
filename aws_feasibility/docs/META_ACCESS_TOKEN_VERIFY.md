# Meta Access Token — Verification Guide

**Script:** `scripts/check_meta_access_token.sh`
**Last updated:** 2026-03-12

---

## Overview

This script calls Meta's `debug_token` Graph API endpoint to inspect any Meta
User Access Token and display:

- Whether the token is **valid**
- Its **expiry dates** (`expires_at` and `data_access_expires_at`) with
  human-readable countdowns and urgency icons
- The full list of **OAuth scopes** granted to the token
- The **app** and **user** the token belongs to

It works in two modes: pulling the token automatically from AWS Secrets
Manager (default, no arguments), or accepting a token directly on the command
line.

---

## Requirements

### 1. Runtime dependencies

| Dependency | Min version | Notes |
|---|---|---|
| `bash` | 4+ | Ships with macOS (via Homebrew) and Amazon Linux |
| `curl` | any | Used to call the Graph API |
| `python3` | 3.8+ | Used to parse JSON and format timestamps |
| `aws` CLI | v2 | Only needed for the no-argument (AWS) mode |

### 2. AWS CLI configured (for default mode)

The script uses the `metads` AWS profile by default. Verify it is configured:

```bash
aws configure list --profile metads
```

Expected output includes a valid `access_key`, `secret_key`, and `region`.
If not set up, run:

```bash
aws configure --profile metads
```

And enter the Access Key ID, Secret Access Key, and region (`us-east-1`).

### 3. Token stored in AWS Secrets Manager (for default mode)

The script reads from secret `metaads/dev/meta-api` and expects the following
JSON structure:

```json
{
  "access_token": "EAABc..."
}
```

Verify the secret exists and is readable:

```bash
aws secretsmanager get-secret-value \
  --profile metads --region us-east-1 \
  --secret-id metaads/dev/meta-api \
  --query 'SecretString' --output text
```

### 4. Obtaining a token from the Meta web UI (manual mode)

If you need a fresh token (e.g. to test a new set of scopes before storing it
in AWS), generate one from the **Meta Graph API Explorer**:

1. Go to https://developers.facebook.com/tools/explorer/
2. Select your app from the top-right dropdown (**EWD Marketing API**)
3. Click **Generate Access Token**
4. In the permissions dialog, select the scopes you want to test
5. Click **Generate Token** and confirm in the Facebook popup
6. Copy the token string — it starts with `EAA...`

> **Note:** Tokens generated in the Explorer are **short-lived (~1–2 hours)**
> unless you exchange them for a long-lived token. For production use, always
> store long-lived tokens (60–90 days) in AWS Secrets Manager.

To exchange a short-lived token for a long-lived one:

```bash
curl -s "https://graph.facebook.com/oauth/access_token\
?grant_type=fb_exchange_token\
&client_id=YOUR_APP_ID\
&client_secret=YOUR_APP_SECRET\
&fb_exchange_token=SHORT_LIVED_TOKEN"
```

Then update the secret:

```bash
aws secretsmanager put-secret-value \
  --profile metads --region us-east-1 \
  --secret-id metaads/dev/meta-api \
  --secret-string '{"access_token": "LONG_LIVED_TOKEN_HERE"}'
```

---

## Usage

### Mode 1 — No argument (reads from AWS Secrets Manager)

```bash
./scripts/check_meta_access_token.sh
```

The script will print the secret ID it is reading from before calling the API:

```
ℹ️  No token provided — fetching from AWS Secrets Manager...
   (profile: metads, region: us-east-1, secret: metaads/dev/meta-api)
```

### Mode 2 — Explicit token argument

```bash
./scripts/check_meta_access_token.sh EAABc...
```

Useful for validating a freshly generated token before storing it in AWS.

### Mode 3 — Override AWS profile or region via environment

```bash
AWS_PROFILE=prod AWS_REGION=us-west-2 ./scripts/check_meta_access_token.sh
```

---

## Sample Output

```
════════════════════════════════════════════════════════════
  META ACCESS TOKEN INSPECTOR
════════════════════════════════════════════════════════════
  Token source     : AWS Secrets Manager (metaads/dev/meta-api)
  App              : EWD Marketing API  (id: 25766891366325694)
  Token type       : USER
  User ID          : 10164740917690625
  Issued at        : 2026-01-30 15:53 UTC  (-41 days)  ⚠️

  is_valid              : ✅  True
  expires_at            : 2026-05-10 23:41 UTC  (59 days)  ✅
  data_access_expires   : 2026-06-10 13:40 UTC  (89 days)  ✅

  Scopes (9):
    • ads_management
    • ads_read
    • business_management
    • catalog_management
    • leads_retrieval
    • pages_manage_ads
    • pages_read_engagement
    • pages_show_list
    • public_profile
════════════════════════════════════════════════════════════
```

---

## Reading the Output

### `is_valid`
- `✅ True` — token is active and accepted by Meta
- `❌ False` — token is expired, revoked, or malformed; generate a new one

### `expires_at`
The date the token itself stops working entirely. After this date, all API
calls return an authentication error.

### `data_access_expires_at`
An additional expiry specific to user data access permissions. Can differ from
`expires_at`. Whichever comes first is the effective deadline.

### Urgency icons on dates

| Icon | Meaning |
|---|---|
| `✅` | More than 14 days remaining — OK |
| `⚠️` | Less than 14 days remaining — renew soon |
| `❌` | Already expired |

### `issued_at` showing negative days
Normal — it shows how many days ago the token was generated. Example:
`(-41 days)` means the token was generated 41 days ago.

### Scopes
The list of OAuth permissions granted at the time the token was generated.
Scopes reflect what the **user consented to** during the OAuth flow —
not what has been approved in App Review. In development mode, any scope
can be granted to the app admin without App Review approval.

---

## Expiry Reference for This Project

| Token type | Typical validity |
|---|---|
| Short-lived (Graph API Explorer) | ~1–2 hours |
| Long-lived user token | 60–90 days |
| System User token (Business) | Does not expire (unless revoked) |

The token currently stored in `metaads/dev/meta-api` is a **long-lived user
token** generated on 2026-01-30 and expires on **2026-05-10** (~100 days
total, consistent with Meta's 60-day rolling window extended at generation
time).

> **Reminder:** Set a calendar event ~2 weeks before expiry to generate and
> rotate the token. The Lambda collectors will silently return `{data:[]}` if
> the token expires without being rotated.

---

## Troubleshooting

### `curl failed — check your network or token format`
- Verify internet connectivity
- Confirm the token string starts with `EAA` and has no extra whitespace

### `aws: command not found`
AWS CLI is not in `PATH`. On macOS with Homebrew:
```bash
export PATH="/opt/homebrew/bin:$PATH"
```
Add this line to your `~/.zshrc` or `~/.bash_profile` to make it permanent.

### `NoCredentialsError` or `profile not found`
The `metads` AWS profile is not configured. Run:
```bash
aws configure --profile metads
```

### Token shows correct scopes but `/ads_archive` returns `{data:[]}`
Scope presence in the token does not guarantee data availability. See
`INTELLIGENCE_GRAPH_API_LIMITATIONS.md` for a full analysis of what the
Ads Library API actually returns by country and ad type.

---

## Raw API Call (no script)

If you prefer to call the endpoint directly without the script:

```bash
TOKEN="your_token_here"

curl -s "https://graph.facebook.com/debug_token\
?input_token=${TOKEN}\
&access_token=${TOKEN}" | python3 -m json.tool
```

This returns the full raw JSON including `scopes`, `granular_scopes`,
`is_valid`, `expires_at`, `data_access_expires_at`, `app_id`, `user_id`,
and `issued_at`.
