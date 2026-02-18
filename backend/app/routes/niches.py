"""
Niche Routes - CRUD operations for niches.

All routes are user-scoped (each user has their own niches).
"""
from flask import Blueprint, request, jsonify

from app import db
from app.models.niche import Niche
from app.models.ad import Ad
from app.models.collection_run import CollectionRun
from app.middleware.auth import require_auth, get_current_user_id
from app.utils.ids import generate_uuid, now_iso8601

niches_bp = Blueprint('niches', __name__, url_prefix='/api/niches')


@niches_bp.route('', methods=['GET'])
@require_auth
def list_niches():
    """
    List all niches for the current user.

    Returns:
        List of niches with basic info
    """
    user_id = get_current_user_id()

    niches = Niche.query.filter_by(
        user_id=user_id,
        is_active=True
    ).order_by(Niche.created_at.desc()).all()

    return jsonify({
        'success': True,
        'data': [niche.to_dict() for niche in niches],
        'count': len(niches)
    })


@niches_bp.route('', methods=['POST'])
@require_auth
def create_niche():
    """
    Create a new niche for the current user.

    Request body:
        name: str (required)
        slug: str (optional, auto-generated from name)
        description: str (optional)
        color: str (optional, hex color)
        icon: str (optional, emoji)
        keywords: list[str] (optional)
        countries: list[str] (optional)
        platforms: list[str] (optional)
    """
    user_id = get_current_user_id()
    data = request.get_json()

    if not data or not data.get('name'):
        return jsonify({
            'success': False,
            'error': 'Name is required'
        }), 400

    # Generate slug if not provided
    slug = data.get('slug') or slugify(data['name'])

    # Check if slug already exists for this user
    existing = Niche.query.filter_by(
        user_id=user_id,
        slug=slug
    ).first()

    if existing:
        return jsonify({
            'success': False,
            'error': f"Niche with slug '{slug}' already exists"
        }), 409

    niche = Niche(
        niche_id=generate_uuid(),
        user_id=user_id,
        slug=slug,
        name=data['name'],
        description=data.get('description'),
        color=data.get('color', '#8B5CF6'),
        icon=data.get('icon', '📊'),
        created_at=now_iso8601()
    )

    # Set list properties
    if 'keywords' in data:
        niche.keywords = data['keywords']
    if 'countries' in data:
        niche.countries = data['countries']
    if 'platforms' in data:
        niche.platforms = data['platforms']

    db.session.add(niche)
    db.session.commit()

    return jsonify({
        'success': True,
        'data': niche.to_dict()
    }), 201


@niches_bp.route('/<slug>', methods=['GET'])
@require_auth
def get_niche(slug):
    """
    Get a niche by slug for the current user.
    """
    user_id = get_current_user_id()

    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()

    if not niche:
        return jsonify({
            'success': False,
            'error': 'Niche not found'
        }), 404

    return jsonify({
        'success': True,
        'data': niche.to_dict(include_stats=True)
    })


@niches_bp.route('/<slug>', methods=['PATCH'])
@require_auth
def update_niche(slug):
    """
    Update a niche for the current user.

    Request body:
        name: str (optional)
        description: str (optional)
        color: str (optional)
        icon: str (optional)
        keywords: list[str] (optional)
        countries: list[str] (optional)
        platforms: list[str] (optional)
    """
    user_id = get_current_user_id()
    data = request.get_json()

    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()

    if not niche:
        return jsonify({
            'success': False,
            'error': 'Niche not found'
        }), 404

    # Update fields
    if 'name' in data:
        niche.name = data['name']
    if 'description' in data:
        niche.description = data['description']
    if 'color' in data:
        niche.color = data['color']
    if 'icon' in data:
        niche.icon = data['icon']
    if 'keywords' in data:
        niche.keywords = data['keywords']
    if 'countries' in data:
        niche.countries = data['countries']
    if 'platforms' in data:
        niche.platforms = data['platforms']

    niche.updated_at = now_iso8601()
    db.session.commit()

    return jsonify({
        'success': True,
        'data': niche.to_dict()
    })


@niches_bp.route('/<slug>', methods=['DELETE'])
@require_auth
def delete_niche(slug):
    """
    Soft delete a niche for the current user.
    """
    user_id = get_current_user_id()

    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()

    if not niche:
        return jsonify({
            'success': False,
            'error': 'Niche not found'
        }), 404

    niche.is_active = False
    niche.updated_at = now_iso8601()
    db.session.commit()

    return jsonify({
        'success': True,
        'message': f"Niche '{niche.name}' deleted"
    })


@niches_bp.route('/<slug>/stats', methods=['GET'])
@require_auth
def get_niche_stats(slug):
    """
    Get statistics for a niche.
    """
    user_id = get_current_user_id()

    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()

    if not niche:
        return jsonify({
            'success': False,
            'error': 'Niche not found'
        }), 404

    # Calculate stats
    total_ads = Ad.query.filter_by(niche_id=niche.niche_id).count()
    active_ads = Ad.query.filter_by(niche_id=niche.niche_id, is_active=True).count()
    saved_ads = Ad.query.filter_by(niche_id=niche.niche_id, is_saved=True).count()
    unique_pages = db.session.query(Ad.page_id).filter_by(
        niche_id=niche.niche_id
    ).distinct().count()

    # Get last collection run
    last_run = CollectionRun.query.filter_by(
        niche_id=niche.niche_id,
        status='completed'
    ).order_by(CollectionRun.completed_at.desc()).first()

    return jsonify({
        'success': True,
        'data': {
            'niche_id': niche.niche_id,
            'slug': niche.slug,
            'name': niche.name,
            'stats': {
                'total_ads': total_ads,
                'active_ads': active_ads,
                'saved_ads': saved_ads,
                'unique_pages': unique_pages,
                'last_collection': last_run.completed_at if last_run else None
            }
        }
    })


@niches_bp.route('/<slug>/collect', methods=['POST'])
@require_auth
def trigger_collection(slug):
    """
    Trigger a data collection for a niche.

    Request body (optional):
        keyword: str (specific keyword to collect, otherwise uses niche keywords)
        limit: int (max ads to collect, default 50)
    """
    user_id = get_current_user_id()
    data = request.get_json() or {}

    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()

    if not niche:
        return jsonify({
            'success': False,
            'error': 'Niche not found'
        }), 404

    # Create a collection run record
    run = CollectionRun(
        run_id=generate_uuid(),
        niche_id=niche.niche_id,
        keyword=data.get('keyword'),
        status='pending',
        started_at=now_iso8601()
    )

    db.session.add(run)
    db.session.commit()

    # Perform collection
    try:
        from collectors.meta_api_collector import MetaAdLibraryAPI
        from processors.ad_parser import AdParser
        from app.services.ad_service import AdService

        # Initialize collector and parser
        api = MetaAdLibraryAPI()
        parser = AdParser()
        ad_service = AdService()

        # Determine keyword to collect
        keyword = data.get('keyword')
        if not keyword and niche.keywords:
            keyword = niche.keywords[0]  # Use first keyword

        if not keyword:
            run.status = 'error'
            run.error_message = 'No keyword specified and niche has no keywords'
            run.completed_at = now_iso8601()
            db.session.commit()

            return jsonify({
                'success': False,
                'error': 'No keyword specified'
            }), 400

        # Update status to running
        run.status = 'running'
        run.keyword = keyword
        db.session.commit()

        # Collect ads from Meta API
        limit = data.get('limit', 50)
        countries = niche.countries or ['US']
        platforms = niche.platforms or ['instagram', 'facebook']

        # Log collection parameters for debugging
        print(f"[COLLECTION] Niche: {niche.name}")
        print(f"[COLLECTION] Keyword: {keyword}")
        print(f"[COLLECTION] Countries: {countries}")
        print(f"[COLLECTION] Platforms: {platforms}")
        print(f"[COLLECTION] Limit: {limit}")

        raw_ads = api.search_ads(
            search_terms=keyword,
            countries=countries,
            platforms=platforms,
            limit=limit
        )

        # Parse and save ads
        ads_new = 0
        ads_updated = 0

        for raw_ad in raw_ads:
            parsed_ad = parser.parse_ad(raw_ad)

            # Create or update ad
            is_new = ad_service.create_or_update_ad(
                niche_id=niche.niche_id,
                ad_data=parsed_ad,
                search_keyword=keyword
            )

            if is_new:
                ads_new += 1
            else:
                ads_updated += 1

        # Update run status
        run.status = 'completed'
        run.ads_collected = len(raw_ads)
        run.ads_new = ads_new
        run.ads_updated = ads_updated
        run.completed_at = now_iso8601()
        db.session.commit()

        return jsonify({
            'success': True,
            'data': {
                'run_id': run.run_id,
                'status': run.status,
                'keyword': keyword,
                'ads_collected': run.ads_collected,
                'ads_new': ads_new,
                'ads_updated': ads_updated,
                'message': f'Successfully collected {len(raw_ads)} ads for keyword "{keyword}"'
            }
        }), 200

    except Exception as e:
        # Update run with error
        run.status = 'error'
        run.error_message = str(e)
        run.completed_at = now_iso8601()
        db.session.commit()

        return jsonify({
            'success': False,
            'error': f'Collection failed: {str(e)}'
        }), 500


def slugify(text: str) -> str:
    """Convert text to URL-friendly slug."""
    import re
    # Convert to lowercase and replace spaces with hyphens
    slug = text.lower().strip()
    slug = re.sub(r'[^\w\s-]', '', slug)
    slug = re.sub(r'[\s_-]+', '-', slug)
    slug = re.sub(r'^-+|-+$', '', slug)
    return slug
