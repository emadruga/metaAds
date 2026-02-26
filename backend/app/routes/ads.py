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

    # Pagination params
    page_num = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 20, type=int), 100)

    # Fetch all matching ads (we need to group them first)
    all_ads = query.all()

    # Group by (page_name + headline)
    from collections import defaultdict
    groups = defaultdict(list)
    for ad in all_ads:
        group_key = f"{ad.page_name}|{ad.headline or ''}"
        groups[group_key].append(ad)

    # Convert to list of groups
    groups_list = list(groups.values())

    # Sort groups based on sort_field
    if sort_field == 'variants':
        # Sort by number of variants
        groups_list.sort(
            key=lambda group: len(group),
            reverse=(sort_order == 'desc')
        )
    elif sort_field == 'days_active':
        # Sort by first ad's days_active
        groups_list.sort(
            key=lambda group: group[0].days_active or 0,
            reverse=(sort_order == 'desc')
        )
    elif sort_field == 'start_date':
        # Sort by first ad's start_date
        groups_list.sort(
            key=lambda group: group[0].start_date or '',
            reverse=(sort_order == 'desc')
        )
    elif sort_field == 'collected_at':
        # Sort by first ad's collected_at
        groups_list.sort(
            key=lambda group: group[0].collected_at or '',
            reverse=(sort_order == 'desc')
        )
    else:
        # Default: sort by variants
        groups_list.sort(
            key=lambda group: len(group),
            reverse=(sort_order == 'desc')
        )

    # Apply pagination to GROUPS (not individual ads)
    total_groups = len(groups_list)
    pages = (total_groups + per_page - 1) // per_page if per_page > 0 else 1
    start_idx = (page_num - 1) * per_page
    end_idx = start_idx + per_page
    paginated_groups = groups_list[start_idx:end_idx]

    # Convert paginated groups to grouped objects for frontend
    grouped_data = []
    for group in paginated_groups:
        # Use first ad as representative for group-level fields
        first_ad = group[0]
        variant_key = f"{first_ad.page_name}|{first_ad.headline or ''}"

        grouped_data.append({
            'variant_key': variant_key,
            'page_name': first_ad.page_name,
            'headline': first_ad.headline,
            'count': len(group),
            'days_active': first_ad.days_active,
            'is_active': first_ad.is_active,
            'start_date': first_ad.start_date.isoformat() if first_ad.start_date else None,
            'thumbnail_url': first_ad.thumbnail_url,
            'platforms': first_ad.platforms,
            'cta': first_ad.cta_detected,
            'body': first_ad.body,
            'ads': [ad.to_card_dict() for ad in group]  # Include all variants
        })

    return jsonify({
        'success': True,
        'data': grouped_data,
        'pagination': {
            'page': page_num,
            'per_page': per_page,
            'total': len(all_ads),  # Total individual ads
            'total_groups': total_groups,  # Total groups
            'pages': pages,  # Pages based on groups
            'has_next': page_num < pages,
            'has_prev': page_num > 1
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

    # Count variants (same page + same headline)
    variant_count = Ad.query.filter(
        Ad.niche_id == niche.niche_id,
        Ad.page_id == ad.page_id,
        Ad.headline == ad.headline
    ).count()

    ad_data = ad.to_dict()
    ad_data['variant_count'] = variant_count

    return jsonify({
        'success': True,
        'data': ad_data
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

    # Find ads from the same page but DIFFERENT campaigns (different headlines)
    # This excludes variants of the current ad (which are handled by variant analysis)
    related = Ad.query.filter(
        Ad.niche_id == niche.niche_id,
        Ad.page_id == ad.page_id,
        Ad.headline != ad.headline,  # Different campaign
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


@ads_bp.route('/<ad_id>/variants/analysis', methods=('GET',))
@require_auth
def analyze_ad_variants(slug, ad_id):
    """
    Analyze differences between ad variants.

    Returns a detailed comparison of all variants with the same page_name + headline,
    identifying what changes between them (images, body text, CTAs, etc.).
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

    # Find all variants (same page_name + headline)
    variants = Ad.query.filter(
        Ad.niche_id == niche.niche_id,
        Ad.page_name == ad.page_name,
        Ad.headline == ad.headline
    ).order_by(Ad.start_date.asc()).all()

    if len(variants) <= 1:
        return jsonify({
            'success': True,
            'data': {
                'total_variants': 1,
                'differences': [],
                'variants': [ad.to_dict()]
            }
        })

    # Analyze differences
    differences = _analyze_variant_differences(variants)

    return jsonify({
        'success': True,
        'data': {
            'total_variants': len(variants),
            'differences': differences,
            'variants': [v.to_dict() for v in variants]
        }
    })


def _analyze_variant_differences(variants):
    """
    Analyze what differs between variants.

    Returns a list of difference types found and their frequency.
    """
    differences = {
        'body_text': [],
        'description': [],
        'link_caption': [],
        'cta': [],
        'platforms': [],
        'media': []
    }

    # Extract unique values for each field
    unique_bodies = set()
    unique_descriptions = set()
    unique_captions = set()
    unique_ctas = set()
    unique_platforms = set()

    for variant in variants:
        if variant.body:
            unique_bodies.add(variant.body)
        if variant.description:
            unique_descriptions.add(variant.description)
        if variant.link_caption:
            unique_captions.add(variant.link_caption)
        if variant.cta_detected:
            unique_ctas.add(variant.cta_detected)
        if variant.platforms:
            # Convert list to tuple for hashability
            platforms_tuple = tuple(variant.platforms) if isinstance(variant.platforms, list) else (variant.platforms,)
            unique_platforms.add(platforms_tuple)

    # Build difference summary
    analysis = []

    if len(unique_bodies) > 1:
        analysis.append({
            'field': 'body_text',
            'variations_count': len(unique_bodies),
            'label': 'Body Text',
            'description': f'{len(unique_bodies)} different body text versions',
            'values': list(unique_bodies)[:5]  # Show first 5 examples
        })

    if len(unique_descriptions) > 1:
        analysis.append({
            'field': 'description',
            'variations_count': len(unique_descriptions),
            'label': 'Description',
            'description': f'{len(unique_descriptions)} different descriptions',
            'values': list(unique_descriptions)[:5]
        })

    if len(unique_captions) > 1:
        analysis.append({
            'field': 'link_caption',
            'variations_count': len(unique_captions),
            'label': 'Link Caption',
            'description': f'{len(unique_captions)} different link captions',
            'values': list(unique_captions)[:5]
        })

    if len(unique_ctas) > 1:
        analysis.append({
            'field': 'cta',
            'variations_count': len(unique_ctas),
            'label': 'Call-to-Action',
            'description': f'{len(unique_ctas)} different CTAs',
            'values': list(unique_ctas)
        })

    if len(unique_platforms) > 1:
        analysis.append({
            'field': 'platforms',
            'variations_count': len(unique_platforms),
            'label': 'Platforms',
            'description': f'{len(unique_platforms)} different platform combinations',
            'values': [', '.join(p) if isinstance(p, tuple) else p for p in unique_platforms]
        })

    # Check for text length variations
    body_lengths = [len(v.body or '') for v in variants]
    if len(set(body_lengths)) > 1:
        analysis.append({
            'field': 'body_length',
            'variations_count': len(set(body_lengths)),
            'label': 'Body Text Length',
            'description': f'Text length varies from {min(body_lengths)} to {max(body_lengths)} characters',
            'values': [f'{l} chars' for l in sorted(set(body_lengths))]
        })

    # If no major differences found, they might be image/video variations
    if not analysis:
        analysis.append({
            'field': 'media',
            'variations_count': len(variants),
            'label': 'Creative Media',
            'description': f'{len(variants)} variants - likely image/video variations with identical text',
            'values': []
        })

    return analysis


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


@ads_bp.route('/clear', methods=['DELETE'])
@require_auth
def clear_all_ads(slug):
    """
    Clear all ads from a niche.

    This permanently deletes all collected ads for this niche.
    Use this to start fresh with better search terms or when data quality is poor.
    """
    niche = get_niche_or_404(slug)
    if not niche:
        return jsonify({'success': False, 'error': 'Niche not found'}), 404

    # Count ads before deletion
    ads_count = Ad.query.filter_by(niche_id=niche.niche_id).count()

    # Delete all ads for this niche
    Ad.query.filter_by(niche_id=niche.niche_id).delete()

    # Clear niche pages (they'll be recreated on next collection)
    NichePage.query.filter_by(niche_id=niche.niche_id).delete()

    db.session.commit()

    return jsonify({
        'success': True,
        'message': f'Cleared {ads_count} ads from niche',
        'ads_deleted': ads_count
    })
