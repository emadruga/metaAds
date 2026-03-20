#!/usr/bin/env bash
# -----------------------------------------------------------------------------
# check_meta_access_token.sh
# Usage:
#   ./scripts/check_meta_access_token.sh              # uses token from AWS Secrets
#   ./scripts/check_meta_access_token.sh <ACCESS_TOKEN>  # uses provided token
# -----------------------------------------------------------------------------

set -euo pipefail

AWS_PROFILE="${AWS_PROFILE:-metads}"
AWS_REGION="${AWS_REGION:-us-east-1}"
SECRET_ID="metaads/dev/meta-api"

# ── Resolve token ─────────────────────────────────────────────────────────────
if [[ $# -ge 1 ]]; then
  TOKEN="$1"
  TOKEN_SOURCE="argument"
else
  echo "ℹ️  No token provided — fetching from AWS Secrets Manager..."
  echo "   (profile: ${AWS_PROFILE}, region: ${AWS_REGION}, secret: ${SECRET_ID})"
  echo ""
  TOKEN=$(aws secretsmanager get-secret-value \
    --profile "${AWS_PROFILE}" \
    --region  "${AWS_REGION}" \
    --secret-id "${SECRET_ID}" \
    --query 'SecretString' --output text \
    | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")
  TOKEN_SOURCE="AWS Secrets Manager (${SECRET_ID})"
fi

# ── Call Meta debug_token endpoint ───────────────────────────────────────────
RAW=$(curl -sf \
  "https://graph.facebook.com/debug_token?input_token=${TOKEN}&access_token=${TOKEN}")

if [[ $? -ne 0 || -z "$RAW" ]]; then
  echo "❌  curl failed — check your network or token format."
  exit 1
fi

# ── Parse with python3 (available on macOS + Amazon Linux 2/3) ───────────────
python3 - <<EOF
import json, sys
from datetime import datetime, timezone

raw = json.loads("""${RAW}""")
data = raw.get("data", {})

# ── Validity ──────────────────────────────────────────────────────────────────
is_valid = data.get("is_valid", False)
valid_icon = "✅" if is_valid else "❌"

# ── Expiry helpers ────────────────────────────────────────────────────────────
def fmt_ts(ts):
    if not ts:
        return "N/A"
    dt = datetime.fromtimestamp(int(ts), tz=timezone.utc)
    delta = dt - datetime.now(tz=timezone.utc)
    days  = delta.days
    sign  = "⚠️ " if days < 14 else ("✅" if days > 0 else "❌")
    return f"{dt.strftime('%Y-%m-%d %H:%M UTC')}  ({days} days)  {sign}"

expires_at            = data.get("expires_at")
data_access_expires   = data.get("data_access_expires_at")
issued_at             = data.get("issued_at")

# ── Scopes ────────────────────────────────────────────────────────────────────
scopes = data.get("scopes", [])

# ── Output ────────────────────────────────────────────────────────────────────
print()
print("═" * 60)
print("  META ACCESS TOKEN INSPECTOR")
print("═" * 60)
print(f"  Token source     : ${TOKEN_SOURCE}")
print(f"  App              : {data.get('application', 'N/A')}  (id: {data.get('app_id', 'N/A')})")
print(f"  Token type       : {data.get('type', 'N/A')}")
print(f"  User ID          : {data.get('user_id', 'N/A')}")
print(f"  Issued at        : {fmt_ts(issued_at)}")
print()
print(f"  is_valid              : {valid_icon}  {is_valid}")
print(f"  expires_at            : {fmt_ts(expires_at)}")
print(f"  data_access_expires   : {fmt_ts(data_access_expires)}")
print()
print(f"  Scopes ({len(scopes)}):")
for s in sorted(scopes):
    print(f"    • {s}")
print("═" * 60)
print()

if not is_valid:
    print("❌  Token is INVALID. Generate a new one.")
    sys.exit(1)
EOF
