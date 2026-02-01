#!/usr/bin/env python3
"""
MetAds Backend - Entry Point

Run the Flask development server or CLI commands.

Usage:
    # Run development server
    python run.py

    # CLI commands
    python run.py niche create --user "user_xxx" --name "Video Editing Apps"
    python run.py niche list --user "user_xxx"
    python run.py collect --niche "video-editing-apps" --user "user_xxx" --limit 50
"""
import os
import sys
import click

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.models import User, Niche, Ad, Page, NichePage, CollectionRun
from app.utils.ids import generate_uuid, now_iso8601


# Create Flask application
app = create_app()


@app.shell_context_processor
def make_shell_context():
    """Add models to Flask shell context."""
    return {
        'db': db,
        'User': User,
        'Niche': Niche,
        'Ad': Ad,
        'Page': Page,
        'NichePage': NichePage,
        'CollectionRun': CollectionRun
    }


# CLI Commands
@app.cli.group()
def niche():
    """Niche management commands."""
    pass


@niche.command('create')
@click.option('--user', required=True, help='User ID (Clerk user_id)')
@click.option('--name', required=True, help='Niche name')
@click.option('--slug', default=None, help='URL slug (auto-generated if not provided)')
@click.option('--keywords', default='', help='Comma-separated keywords')
@click.option('--countries', default='US', help='Comma-separated country codes')
def niche_create(user, name, slug, keywords, countries):
    """Create a new niche for a user."""
    import re

    # Generate slug if not provided
    if not slug:
        slug = name.lower().strip()
        slug = re.sub(r'[^\w\s-]', '', slug)
        slug = re.sub(r'[\s_-]+', '-', slug)

    # Check if niche already exists
    existing = Niche.query.filter_by(user_id=user, slug=slug).first()
    if existing:
        click.echo(f"Error: Niche '{slug}' already exists for user {user}")
        return

    # Parse keywords and countries
    keyword_list = [k.strip() for k in keywords.split(',') if k.strip()] if keywords else []
    country_list = [c.strip().upper() for c in countries.split(',') if c.strip()]

    niche = Niche(
        niche_id=generate_uuid(),
        user_id=user,
        slug=slug,
        name=name,
        created_at=now_iso8601()
    )
    niche.keywords = keyword_list
    niche.countries = country_list

    db.session.add(niche)
    db.session.commit()

    click.echo(f"Created niche: {name} (slug: {slug})")
    click.echo(f"  ID: {niche.niche_id}")
    click.echo(f"  Keywords: {keyword_list}")
    click.echo(f"  Countries: {country_list}")


@niche.command('list')
@click.option('--user', required=True, help='User ID (Clerk user_id)')
def niche_list(user):
    """List all niches for a user."""
    niches = Niche.query.filter_by(user_id=user, is_active=True).all()

    if not niches:
        click.echo(f"No niches found for user {user}")
        return

    click.echo(f"Niches for user {user}:")
    for n in niches:
        ad_count = Ad.query.filter_by(niche_id=n.niche_id).count()
        click.echo(f"  - {n.name} ({n.slug})")
        click.echo(f"      ID: {n.niche_id}")
        click.echo(f"      Ads: {ad_count}")
        click.echo(f"      Keywords: {n.keywords}")


@niche.command('stats')
@click.option('--niche', 'niche_slug', required=True, help='Niche slug')
@click.option('--user', required=True, help='User ID')
def niche_stats(niche_slug, user):
    """Show statistics for a niche."""
    niche = Niche.query.filter_by(user_id=user, slug=niche_slug, is_active=True).first()

    if not niche:
        click.echo(f"Niche '{niche_slug}' not found for user {user}")
        return

    total_ads = Ad.query.filter_by(niche_id=niche.niche_id).count()
    active_ads = Ad.query.filter_by(niche_id=niche.niche_id, is_active=True).count()
    saved_ads = Ad.query.filter_by(niche_id=niche.niche_id, is_saved=True).count()
    unique_pages = db.session.query(Ad.page_id).filter_by(
        niche_id=niche.niche_id
    ).distinct().count()

    click.echo(f"Statistics for '{niche.name}':")
    click.echo(f"  Total Ads: {total_ads}")
    click.echo(f"  Active Ads: {active_ads}")
    click.echo(f"  Saved Ads: {saved_ads}")
    click.echo(f"  Unique Pages: {unique_pages}")


@app.cli.command('collect')
@click.option('--niche', 'niche_slug', required=True, help='Niche slug')
@click.option('--user', required=True, help='User ID')
@click.option('--keyword', default=None, help='Specific keyword (uses niche keywords if not provided)')
@click.option('--limit', default=50, help='Maximum ads to collect')
def collect_ads(niche_slug, user, keyword, limit):
    """Collect ads for a niche."""
    niche = Niche.query.filter_by(user_id=user, slug=niche_slug, is_active=True).first()

    if not niche:
        click.echo(f"Niche '{niche_slug}' not found for user {user}")
        return

    # Determine keywords to use
    keywords_to_collect = [keyword] if keyword else niche.keywords

    if not keywords_to_collect:
        click.echo("No keywords specified. Add keywords to the niche or use --keyword")
        return

    click.echo(f"Collecting ads for '{niche.name}'...")
    click.echo(f"  Keywords: {keywords_to_collect}")
    click.echo(f"  Limit: {limit}")

    # Create collection run
    run = CollectionRun(
        run_id=generate_uuid(),
        niche_id=niche.niche_id,
        keyword=','.join(keywords_to_collect),
        status='running',
        started_at=now_iso8601()
    )
    db.session.add(run)
    db.session.commit()

    try:
        # Import collector and parser
        from collectors.meta_api_collector import MetaAdLibraryAPI
        from processors.ad_parser import AdParser
        from app.services.ad_service import AdService

        api = MetaAdLibraryAPI()
        parser = AdParser()

        total_collected = 0
        total_new = 0
        total_updated = 0

        for kw in keywords_to_collect:
            click.echo(f"  Collecting for keyword: {kw}")

            raw_ads = api.search_ads(
                search_terms=kw,
                countries=niche.countries,
                platforms=niche.platforms,
                limit=limit
            )

            click.echo(f"    Found {len(raw_ads)} raw ads")

            for raw_ad in raw_ads:
                parsed = parser.parse_ad(raw_ad)
                parsed['search_keyword'] = kw
                parsed['country_codes'] = niche.countries

                ad, is_new = AdService.create_or_update_ad(niche.niche_id, parsed)
                total_collected += 1
                if is_new:
                    total_new += 1
                else:
                    total_updated += 1

        # Update run status
        run.mark_completed(
            ads_collected=total_collected,
            ads_new=total_new,
            ads_updated=total_updated
        )
        db.session.commit()

        click.echo(f"\nCollection complete!")
        click.echo(f"  Total collected: {total_collected}")
        click.echo(f"  New ads: {total_new}")
        click.echo(f"  Updated ads: {total_updated}")

    except Exception as e:
        run.mark_error(str(e))
        db.session.commit()
        click.echo(f"Error during collection: {e}")


@app.cli.command('init-db')
def init_db():
    """Initialize the database."""
    click.echo("Creating database tables...")
    db.create_all()
    click.echo("Database initialized successfully!")


@app.cli.command('seed')
@click.option('--user', required=True, help='User ID to seed data for')
def seed_data(user):
    """Seed database with sample data."""
    click.echo(f"Seeding sample data for user {user}...")

    # Create sample user if not exists
    existing_user = User.query.get(user)
    if not existing_user:
        sample_user = User(
            id=user,
            email=f'{user}@example.com',
            first_name='Test',
            last_name='User',
            created_at=now_iso8601()
        )
        db.session.add(sample_user)
        click.echo(f"Created user: {user}")

    # Create sample niches
    sample_niches = [
        {
            'name': 'Video Editing Apps',
            'slug': 'video-editing-apps',
            'icon': '🎬',
            'color': '#8B5CF6',
            'keywords': ['video editing ai', 'opus clip', 'descript'],
            'description': 'AI-powered video editing tools'
        },
        {
            'name': 'CRM Tools',
            'slug': 'crm-tools',
            'icon': '📊',
            'color': '#3B82F6',
            'keywords': ['pipedrive', 'hubspot crm', 'salesforce'],
            'description': 'Customer relationship management software'
        }
    ]

    for niche_data in sample_niches:
        existing = Niche.query.filter_by(user_id=user, slug=niche_data['slug']).first()
        if existing:
            click.echo(f"  Niche '{niche_data['slug']}' already exists, skipping")
            continue

        niche = Niche(
            niche_id=generate_uuid(),
            user_id=user,
            slug=niche_data['slug'],
            name=niche_data['name'],
            description=niche_data['description'],
            icon=niche_data['icon'],
            color=niche_data['color'],
            created_at=now_iso8601()
        )
        niche.keywords = niche_data['keywords']
        niche.countries = ['US', 'BR']
        niche.platforms = ['instagram', 'facebook']

        db.session.add(niche)
        click.echo(f"  Created niche: {niche_data['name']}")

    db.session.commit()
    click.echo("Seeding complete!")


if __name__ == '__main__':
    import os
    # Run the development server
    # Use port 5001 to avoid conflict with macOS AirPlay Receiver on 5000
    port = int(os.environ.get('PORT', 5001))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=True
    )
