#!/usr/bin/env python3
"""
SQLite → DynamoDB migration script.

Reads all data from the existing SQLite database via SQLAlchemy models
and bulk-writes it to the DynamoDB single-table design.

Usage:
    # Dry-run (show counts, no writes)
    python scripts/migrate_sqlite_to_dynamodb.py --dry-run

    # Migrate to dev table
    python scripts/migrate_sqlite_to_dynamodb.py --profile metads --env dev

    # Migrate to prod table
    python scripts/migrate_sqlite_to_dynamodb.py --profile metads --env prod

Prerequisites:
    pip install boto3 sqlalchemy python-dotenv
    Run from the project root (metaAds/)
    AWS profile must have DynamoDB write access.

Safety:
    - Uses condition_expression="attribute_not_exists(PK)" to avoid
      overwriting items that already exist in DynamoDB.
    - Pass --overwrite to skip the condition check.
    - DynamoDB PITR means you can restore if anything goes wrong.
"""

import argparse
import json
import os
import sys
from pathlib import Path

# Allow importing from both /backend and /aws_lambda_deploy/backend
PROJECT_ROOT = Path(__file__).parent.parent.parent  # metaAds/
BACKEND_OLD  = PROJECT_ROOT / "backend"
BACKEND_NEW  = PROJECT_ROOT / "aws_lambda_deploy" / "backend"

sys.path.insert(0, str(BACKEND_OLD))
sys.path.insert(0, str(BACKEND_NEW))

import boto3
from botocore.exceptions import ClientError

# Load .env so SQLAlchemy can find the SQLite file
from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / "backend" / ".env")

# Old SQLAlchemy models
from app import create_app
from app.models.user import User as OldUser
from app.models.niche import Niche as OldNiche
from app.models.ad import Ad as OldAd
from app.models.page import Page as OldPage
from app.models.niche_page import NichePage as OldNichePage
from app.models.collection_run import CollectionRun as OldRun
from app import db as sqldb

# New DynamoDB models
from app.dynamodb.models import (
    User, Niche, Ad, Page, NichePage, CollectionRun,
)
from app.utils.ids import now_iso8601


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _batch_write(table, items: list, overwrite: bool, dry_run: bool) -> tuple[int, int]:
    """
    Write items in batches of 25.
    Returns (written, skipped) counts.
    """
    if dry_run:
        return len(items), 0

    written = 0
    skipped = 0

    for i in range(0, len(items), 25):
        batch = items[i:i + 25]
        if overwrite:
            with table.batch_writer() as bw:
                for item in batch:
                    bw.put_item(Item=item)
            written += len(batch)
        else:
            # Individual PutItem with condition (batch_write_item doesn't support conditions)
            for item in batch:
                try:
                    table.put_item(
                        Item=item,
                        ConditionExpression="attribute_not_exists(PK)",
                    )
                    written += 1
                except ClientError as exc:
                    if exc.response["Error"]["Code"] == "ConditionalCheckFailedException":
                        skipped += 1
                    else:
                        raise

    return written, skipped


def _progress(label: str, current: int, total: int) -> None:
    pct = int(current / total * 100) if total else 0
    bar = "#" * (pct // 5) + "-" * (20 - pct // 5)
    print(f"\r  {label}: [{bar}] {current}/{total} ({pct}%)", end="", flush=True)


# ---------------------------------------------------------------------------
# Per-entity migration functions
# ---------------------------------------------------------------------------

def migrate_users(table, flask_app, overwrite: bool, dry_run: bool) -> dict:
    print("\n[Users]")
    with flask_app.app_context():
        old_users = sqldb.session.query(OldUser).all()
    print(f"  Found {len(old_users)} users in SQLite")

    items = []
    for u in old_users:
        new_user = User(
            id=u.id,
            email=u.email,
            first_name=u.first_name or "",
            last_name=u.last_name or "",
            image_url=u.image_url or "",
            is_active=u.is_active if u.is_active is not None else True,
            created_at=u.created_at.isoformat() + "Z" if u.created_at else now_iso8601(),
            updated_at=u.updated_at.isoformat() + "Z" if u.updated_at else now_iso8601(),
        )
        items.append(new_user.to_item())

    written, skipped = _batch_write(table, items, overwrite, dry_run)
    print(f"\n  Written: {written}  Skipped (already exist): {skipped}")
    return {"written": written, "skipped": skipped}


def migrate_niches(table, flask_app, overwrite: bool, dry_run: bool) -> dict:
    print("\n[Niches]")
    with flask_app.app_context():
        old_niches = sqldb.session.query(OldNiche).all()
    print(f"  Found {len(old_niches)} niches in SQLite")

    items = []
    for n in old_niches:
        new_niche = Niche(
            id=n.id,
            user_id=n.user_id,
            name=n.name,
            slug=n.slug,
            description=n.description or "",
            keywords=n.keywords or [],     # already parsed by property
            countries=n.countries or ["US"],
            platforms=n.platforms or ["instagram"],
            is_active=n.is_active if n.is_active is not None else True,
            created_at=n.created_at.isoformat() + "Z" if n.created_at else now_iso8601(),
            updated_at=n.updated_at.isoformat() + "Z" if n.updated_at else now_iso8601(),
        )
        items.append(new_niche.to_item())

    written, skipped = _batch_write(table, items, overwrite, dry_run)
    print(f"\n  Written: {written}  Skipped: {skipped}")
    return {"written": written, "skipped": skipped}


def migrate_pages(table, flask_app, overwrite: bool, dry_run: bool) -> dict:
    print("\n[Pages]")
    with flask_app.app_context():
        old_pages = sqldb.session.query(OldPage).all()
    print(f"  Found {len(old_pages)} pages in SQLite")

    items = []
    for p in old_pages:
        new_page = Page(
            page_id=p.page_id,
            page_name=p.page_name,
            first_seen_at=p.first_seen_at.isoformat() + "Z" if p.first_seen_at else now_iso8601(),
            last_seen_at=p.last_seen_at.isoformat() + "Z" if p.last_seen_at else now_iso8601(),
        )
        items.append(new_page.to_item())

    written, skipped = _batch_write(table, items, overwrite, dry_run)
    print(f"\n  Written: {written}  Skipped: {skipped}")
    return {"written": written, "skipped": skipped}


def migrate_niche_pages(table, flask_app, overwrite: bool, dry_run: bool) -> dict:
    print("\n[NichePages]")
    with flask_app.app_context():
        old_nps = sqldb.session.query(OldNichePage).all()
    print(f"  Found {len(old_nps)} niche-page links in SQLite")

    items = []
    for np in old_nps:
        new_np = NichePage(
            niche_id=np.niche_id,
            page_id=np.page_id,
            page_name=np.page_name or "",
            is_competitor=np.is_competitor or False,
            ad_count=np.ad_count or 0,
            first_seen_at=np.first_seen_at.isoformat() + "Z" if np.first_seen_at else now_iso8601(),
            last_seen_at=np.last_seen_at.isoformat() + "Z" if np.last_seen_at else now_iso8601(),
        )
        items.append(new_np.to_item())

    written, skipped = _batch_write(table, items, overwrite, dry_run)
    print(f"\n  Written: {written}  Skipped: {skipped}")
    return {"written": written, "skipped": skipped}


def migrate_ads(table, flask_app, overwrite: bool, dry_run: bool) -> dict:
    print("\n[Ads]")
    with flask_app.app_context():
        old_ads = sqldb.session.query(OldAd).all()
    total = len(old_ads)
    print(f"  Found {total} ads in SQLite")

    items = []
    for idx, a in enumerate(old_ads):
        _progress("converting", idx + 1, total)

        new_ad = Ad(
            id=a.id,
            niche_id=a.niche_id,
            meta_ad_id=a.meta_ad_id,
            page_id=a.page_id or None,
            page_name=a.page_name or "",
            start_date=a.start_date.isoformat() + "Z" if a.start_date else None,
            end_date=a.end_date.isoformat() + "Z" if a.end_date else None,
            is_active=a.is_active if a.is_active is not None else True,
            days_active=a.days_active,
            collected_at=a.collected_at.isoformat() + "Z" if a.collected_at else now_iso8601(),
            platforms=a.platforms or [],
            country_codes=a.country_codes or [],
            snapshot_url=a.snapshot_url or "",
            body=a.body or "",
            headline=a.headline or "",
            description=a.description or "",
            link_caption=a.link_caption or "",
            full_text=a.full_text or "",
            text_length=a.text_length or 0,
            has_emoji=a.has_emoji or False,
            has_hashtags=a.has_hashtags or False,
            hashtags=a.hashtags or [],
            mentions=a.mentions or [],
            cta_detected=a.cta_detected or None,
            creative_type=a.creative_type or "image",
            creatives=a.creatives or [],
            is_saved=a.is_saved or False,
            saved_at=a.saved_at.isoformat() + "Z" if a.saved_at else None,
            saved_tags=a.saved_tags or [],
            search_keyword=a.search_keyword or "",
        )
        items.append(new_ad.to_item())

    print()  # newline after progress bar
    written, skipped = _batch_write(table, items, overwrite, dry_run)
    print(f"  Written: {written}  Skipped: {skipped}")
    return {"written": written, "skipped": skipped}


def migrate_collection_runs(table, flask_app, overwrite: bool, dry_run: bool) -> dict:
    print("\n[CollectionRuns]")
    with flask_app.app_context():
        old_runs = sqldb.session.query(OldRun).all()
    print(f"  Found {len(old_runs)} collection runs in SQLite")

    items = []
    for r in old_runs:
        new_run = CollectionRun(
            id=r.id,
            niche_id=r.niche_id,
            status=r.status or "completed",
            keywords_used=r.keywords_used or [],
            ads_found=r.ads_found or 0,
            ads_new=r.ads_new or 0,
            ads_updated=r.ads_updated or 0,
            error_message=r.error_message or None,
            started_at=r.started_at.isoformat() + "Z" if r.started_at else now_iso8601(),
            completed_at=r.completed_at.isoformat() + "Z" if r.completed_at else None,
        )
        items.append(new_run.to_item())

    written, skipped = _batch_write(table, items, overwrite, dry_run)
    print(f"\n  Written: {written}  Skipped: {skipped}")
    return {"written": written, "skipped": skipped}


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(description="Migrate SQLite → DynamoDB")
    parser.add_argument("--profile", default="metads", help="AWS CLI profile")
    parser.add_argument("--env", default="dev", choices=["dev", "prod"])
    parser.add_argument("--dry-run", action="store_true",
                        help="Show counts only; do not write to DynamoDB")
    parser.add_argument("--overwrite", action="store_true",
                        help="Overwrite existing DynamoDB items (skips conditional check)")
    parser.add_argument("--entity", default="all",
                        choices=["all", "users", "niches", "pages", "niche_pages", "ads", "runs"],
                        help="Migrate only a specific entity type")
    args = parser.parse_args()

    table_name = f"metaads-{args.env}-table"

    print(f"\n{'='*60}")
    print(f"  MetaAds SQLite → DynamoDB Migration")
    print(f"  Table  : {table_name}")
    print(f"  Profile: {args.profile}")
    print(f"  Mode   : {'DRY RUN (no writes)' if args.dry_run else 'LIVE'}")
    print(f"  Overwrite existing: {args.overwrite}")
    print(f"{'='*60}")

    # Initialise boto3
    session = boto3.Session(profile_name=args.profile)
    dynamodb = session.resource("dynamodb")
    table = dynamodb.Table(table_name)

    # Initialise Flask app (for SQLAlchemy session)
    flask_app = create_app()

    results = {}
    entity = args.entity

    if entity in ("all", "users"):
        results["users"] = migrate_users(table, flask_app, args.overwrite, args.dry_run)
    if entity in ("all", "niches"):
        results["niches"] = migrate_niches(table, flask_app, args.overwrite, args.dry_run)
    if entity in ("all", "pages"):
        results["pages"] = migrate_pages(table, flask_app, args.overwrite, args.dry_run)
    if entity in ("all", "niche_pages"):
        results["niche_pages"] = migrate_niche_pages(table, flask_app, args.overwrite, args.dry_run)
    if entity in ("all", "ads"):
        results["ads"] = migrate_ads(table, flask_app, args.overwrite, args.dry_run)
    if entity in ("all", "runs"):
        results["runs"] = migrate_collection_runs(table, flask_app, args.overwrite, args.dry_run)

    # Summary
    print(f"\n{'='*60}")
    print("  MIGRATION SUMMARY")
    print(f"{'='*60}")
    total_written = total_skipped = 0
    for entity_name, counts in results.items():
        w = counts["written"]
        s = counts["skipped"]
        total_written += w
        total_skipped += s
        print(f"  {entity_name:<20} written={w:<6} skipped={s}")
    print(f"  {'TOTAL':<20} written={total_written:<6} skipped={total_skipped}")
    print(f"{'='*60}")

    if args.dry_run:
        print("\n  ⚠️  DRY RUN — no data was written to DynamoDB.")
    else:
        print("\n  ✅  Migration complete.")


if __name__ == "__main__":
    main()
