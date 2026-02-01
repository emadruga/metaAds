"""
Ads Routes - Search and detail endpoints for ads.

All routes are niche-scoped (ads belong to niches).
"""
from flask import Blueprint, request, jsonify

from app import db
from app.models.niche import Niche
from app.models.ad import Ad
from app.models.niche_page import NichePage
from app.middleware.auth import require_auth, get_current_user_id

ads_bp = Blueprint('ads', __name__, url_prefix='/api/niches/<slug>/ads')


def get_niche_or_404(slug: str):
    """Get niche by slug for current user, or return 404."""
    user_id = get_current_user_id()
    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()
    return niche


@ads_bp.route('/search', methods=['GET'])
@require_auth
def search_ads(slug):
    """
    Search ads within a niche.

    Query parameters:
        q: str - Search term (searches full_text)
        platform: str - Filter by platform (comma-separated)
        country: str - Filter by country (comma-separated)
        status: str - 'active', 'inactive', or 'all' (default: 'all')
        min_days: int - Minimum days active
        max_days: int - Maximum days active
        cta: str - Filter by CTA type
        date_from: str - Start date (ISO8601)
        date_to: str - End date (ISO8601)
        page_id: str - Filter by page ID
        sort: str - Sort field (days_active, start_date, created_at)
        order: str - Sort order (asc, desc)
        page: int - Page number (default: 1)
        per_page: int - Results per page (default: 20, max: 100)
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    # Build query
    query = Ad.query.filter_by(niche_id=niche.niche_id)

    # Text search
    search_term = request.args.get('q')
    if search_term:
        query = query.filter(Ad.full_text.ilike(f'%{search_term}%'))

    # Platform filter
    platform = request.args.get('platform')
    if platform:
        # Filter by platform (stored as JSON array string like ["instagram", "facebook"])
        # Search for the platform name within the JSON array with quotes
        platform_lower = platform.strip().lower()
        query = query.filter(Ad._platforms.ilike(f'%"{platform_lower}"%'))

    # Country filter
    country = request.args.get('country')
    if country:
        countries = country.split(',')
        for c in countries:
            query = query.filter(Ad._country_codes.ilike(f'%{c.strip()}%'))

    # Status filter - accept both 'status' and 'is_active' parameters
    status = request.args.get('status', 'all')
    is_active = request.args.get('is_active')

    # If is_active is explicitly set, use it (from frontend)
    if is_active is not None and is_active != '':
        if is_active.lower() == 'true':
            query = query.filter_by(is_active=True)
        elif is_active.lower() == 'false':
            query = query.filter_by(is_active=False)
    # Otherwise use status parameter
    elif status == 'active':
        query = query.filter_by(is_active=True)
    elif status == 'inactive':
        query = query.filter_by(is_active=False)

    # Days active filter
    min_days = request.args.get('min_days', type=int)
    if min_days is not None:
        query = query.filter(Ad.days_active >= min_days)

    max_days = request.args.get('max_days', type=int)
    if max_days is not None:
        query = query.filter(Ad.days_active <= max_days)

    # CTA filter
    cta = request.args.get('cta')
    if cta:
        query = query.filter_by(cta_detected=cta)

    # Date filters
    date_from = request.args.get('date_from')
    if date_from:
        query = query.filter(Ad.start_date >= date_from)

    date_to = request.args.get('date_to')
    if date_to:
        query = query.filter(Ad.start_date <= date_to)

    # Page filter
    page_id = request.args.get('page_id')
    if page_id:
        query = query.filter_by(page_id=page_id)

    # Sorting
    sort_field = request.args.get('sort', 'days_active')
    sort_order = request.args.get('order', 'desc')

    sort_column = getattr(Ad, sort_field, Ad.days_active)
    if sort_order == 'asc':
        query = query.order_by(sort_column.asc())
    else:
        query = query.order_by(sort_column.desc())

    # Pagination
    page_num = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    pagination = query.paginate(
        page=page_num,
        per_page=per_page,
        error_out=False
    )

    return jsonify({
        'success': True,
        'data': [ad.to_card_dict() for ad in pagination.items],
        'pagination': {
            'page': page_num,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@ads_bp.route('/<ad_id>', methods=['GET'])
@require_auth
def get_ad(slug, ad_id):
    """
    Get ad details by ID.
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    ad = Ad.query.filter_by(
        niche_id=niche.niche_id,
        id=ad_id
    ).first()

    if not ad:
        return jsonify({'success': False, 'error': 'Ad not found'}), 404

    return jsonify({
        'success': True,
        'data': ad.to_dict()
    })


@ads_bp.route('/<ad_id>/related', methods=['GET'])
@require_auth
def get_related_ads(slug, ad_id):
    """
    Get related ads/variants for an ad.

    Related ads are:
    1. From the same page
    2. Within a similar time period (overlap or close dates)
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    ad = Ad.query.filter_by(
        niche_id=niche.niche_id,
        id=ad_id
    ).first()

    if not ad:
        return jsonify({'success': False, 'error': 'Ad not found'}), 404

    # Find ads from the same page
    related = Ad.query.filter(
        Ad.niche_id == niche.niche_id,
        Ad.page_id == ad.page_id,
        Ad.id != ad.id
    ).order_by(Ad.start_date.desc()).limit(20).all()

    # Calculate insights
    if related:
        total_variants = len(related) + 1
        longest = max([ad] + related, key=lambda x: x.days_active or 0)
        newest = max([ad] + related, key=lambda x: x.start_date or '')

        insights = {
            'total_variants': total_variants,
            'longest_running': {
                'id': longest.id,
                'days_active': longest.days_active
            },
            'newest': {
                'id': newest.id,
                'start_date': newest.start_date
            }
        }
    else:
        insights = {
            'total_variants': 1,
            'longest_running': None,
            'newest': None
        }

    return jsonify({
        'success': True,
        'data': {
            'original': ad.to_card_dict(),
            'related': [r.to_card_dict() for r in related],
            'insights': insights
        }
    })


# Page-related endpoints

@ads_bp.route('/../pages', methods=['GET'])
@require_auth
def list_pages(slug):
    """
    List pages in a niche.
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    niche_pages = NichePage.query.filter_by(
        niche_id=niche.niche_id
    ).order_by(NichePage.total_ads_in_niche.desc()).all()

    return jsonify({
        'success': True,
        'data': [np.to_dict() for np in niche_pages],
        'count': len(niche_pages)
    })


@ads_bp.route('/../pages/<page_id>/ads', methods=['GET'])
@require_auth
def get_page_ads(slug, page_id):
    """
    Get all ads from a specific page in the niche.
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    ads = Ad.query.filter_by(
        niche_id=niche.niche_id,
        page_id=page_id
    ).order_by(Ad.start_date.desc()).all()

    return jsonify({
        'success': True,
        'data': [ad.to_card_dict() for ad in ads],
        'count': len(ads)
    })


@ads_bp.route('/../pages/<page_id>/competitor', methods=['POST'])
@require_auth
def mark_page_competitor(slug, page_id):
    """
    Mark a page as a competitor in the niche.
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    data = request.get_json() or {}
    is_competitor = data.get('is_competitor', True)
    notes = data.get('notes')

    niche_page = NichePage.query.filter_by(
        niche_id=niche.niche_id,
        page_id=page_id
    ).first()

    if not niche_page:
        return jsonify({'success': False, 'error': 'Page not found in niche'}), 404

    niche_page.is_competitor = is_competitor
    if notes:
        niche_page.notes = notes

    # Update ads to reflect competitor status
    Ad.query.filter_by(
        niche_id=niche.niche_id,
        page_id=page_id
    ).update({'is_competitor_page': is_competitor})

    db.session.commit()

    return jsonify({
        'success': True,
        'data': niche_page.to_dict()
    })
