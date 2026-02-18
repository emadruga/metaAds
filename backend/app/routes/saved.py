"""
Saved Ads Routes - Save/unsave ads with notes and tags.

All routes are niche-scoped (saved ads belong to niches).
"""
from flask import Blueprint, request, jsonify

from app import db
from app.models.niche import Niche
from app.models.ad import Ad
from app.middleware.auth import require_auth, get_current_user_id
from app.utils.ids import now_iso8601

saved_bp = Blueprint('saved', __name__, url_prefix='/api/niches/<slug>')


def get_niche_or_404(slug: str):
    """Get niche by slug for current user, or return 404."""
    user_id = get_current_user_id()
    niche = Niche.query.filter_by(
        user_id=user_id,
        slug=slug,
        is_active=True
    ).first()
    return niche


@saved_bp.route('/saved', methods=['GET'])
@require_auth
def list_saved_ads(slug):
    """
    Get all saved ads in a niche.

    Query parameters:
        tag: str - Filter by tag
        sort: str - Sort field (saved_at, days_active)
        order: str - Sort order (asc, desc)
        page: int - Page number
        per_page: int - Results per page
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    query = Ad.query.filter_by(
        niche_id=niche.niche_id,
        is_saved=True
    )

    # Tag filter
    tag = request.args.get('tag')
    if tag:
        query = query.filter(Ad._saved_tags.ilike(f'%{tag}%'))

    # Sorting
    sort_field = request.args.get('sort', 'saved_at')
    sort_order = request.args.get('order', 'desc')

    sort_column = getattr(Ad, sort_field, Ad.saved_at)
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

    # Get all unique tags for this niche's saved ads
    all_saved = Ad.query.filter_by(
        niche_id=niche.niche_id,
        is_saved=True
    ).all()

    all_tags = set()
    for ad in all_saved:
        if ad.saved_tags:
            all_tags.update(ad.saved_tags)

    return jsonify({
        'success': True,
        'data': [ad.to_card_dict() for ad in pagination.items],
        'tags': sorted(list(all_tags)),
        'pagination': {
            'page': page_num,
            'per_page': per_page,
            'total': pagination.total,
            'pages': pagination.pages,
            'has_next': pagination.has_next,
            'has_prev': pagination.has_prev
        }
    })


@saved_bp.route('/ads/<ad_id>/save', methods=['POST'])
@require_auth
def save_ad(slug, ad_id):
    """
    Save an ad to the niche's saved collection.

    Request body (optional):
        notes: str - Notes about the ad
        tags: list[str] - Tags for the ad
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

    if ad.is_saved:
        return jsonify({
            'success': False,
            'error': 'Ad is already saved'
        }), 400

    data = request.get_json() or {}

    ad.is_saved = True
    ad.saved_at = now_iso8601()
    ad.saved_notes = data.get('notes')
    if 'tags' in data:
        ad.saved_tags = data['tags']

    db.session.commit()

    return jsonify({
        'success': True,
        'data': ad.to_dict()
    })


@saved_bp.route('/ads/<ad_id>/save', methods=['DELETE'])
@require_auth
def unsave_ad(slug, ad_id):
    """
    Remove an ad from the niche's saved collection.
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

    if not ad.is_saved:
        return jsonify({
            'success': False,
            'error': 'Ad is not saved'
        }), 400

    ad.is_saved = False
    ad.saved_at = None
    ad.saved_notes = None
    ad.saved_tags = None

    db.session.commit()

    return jsonify({
        'success': True,
        'message': 'Ad unsaved'
    })


@saved_bp.route('/ads/<ad_id>/save', methods=['PATCH'])
@require_auth
def update_saved_ad(slug, ad_id):
    """
    Update notes/tags for a saved ad.

    Request body:
        notes: str (optional)
        tags: list[str] (optional)
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

    if not ad.is_saved:
        return jsonify({
            'success': False,
            'error': 'Ad is not saved'
        }), 400

    data = request.get_json() or {}

    if 'notes' in data:
        ad.saved_notes = data['notes']
    if 'tags' in data:
        ad.saved_tags = data['tags']

    db.session.commit()

    return jsonify({
        'success': True,
        'data': ad.to_dict()
    })
