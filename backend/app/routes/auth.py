"""
Authentication Routes - Clerk webhook and user endpoints.

Handles:
- Clerk webhook for user sync (user.created, user.updated, user.deleted)
- Get current user endpoint
"""
from flask import Blueprint, request, jsonify, current_app
import hmac
import hashlib

from app import db
from app.models.user import User
from app.middleware.auth import require_auth, get_current_user_id
from app.utils.ids import now_iso8601

auth_bp = Blueprint('auth', __name__, url_prefix='/api/auth')


@auth_bp.route('/webhook', methods=['POST'])
def clerk_webhook():
    """
    Handle Clerk webhooks for user sync.

    Events:
        - user.created: Create new user in database
        - user.updated: Update existing user
        - user.deleted: Soft delete user (set is_active=False)

    Security:
        Webhook signature is verified using CLERK_WEBHOOK_SECRET
    """
    # Get webhook payload and signature
    payload = request.get_data()
    signature = request.headers.get('svix-signature')

    # Verify signature (in production, use proper Svix verification)
    webhook_secret = current_app.config.get('CLERK_WEBHOOK_SECRET')
    if webhook_secret and not verify_webhook_signature(payload, signature, webhook_secret):
        current_app.logger.warning('Invalid webhook signature')
        return jsonify({'error': 'Invalid signature'}), 401

    # Parse event
    try:
        event = request.get_json()
        event_type = event.get('type')
        user_data = event.get('data', {})

        current_app.logger.info(f'Received Clerk webhook: {event_type}')

        if event_type == 'user.created':
            handle_user_created(user_data)
        elif event_type == 'user.updated':
            handle_user_updated(user_data)
        elif event_type == 'user.deleted':
            handle_user_deleted(user_data)
        else:
            current_app.logger.info(f'Unhandled event type: {event_type}')

        return jsonify({'received': True}), 200

    except Exception as e:
        current_app.logger.error(f'Webhook error: {e}')
        return jsonify({'error': str(e)}), 500


def handle_user_created(user_data: dict):
    """Create a new user from Clerk data."""
    email = get_primary_email(user_data)
    if not email:
        current_app.logger.error('No email found in user data')
        return

    user = User(
        id=user_data['id'],
        email=email,
        first_name=user_data.get('first_name'),
        last_name=user_data.get('last_name'),
        image_url=user_data.get('image_url'),
        created_at=now_iso8601()
    )

    db.session.add(user)
    db.session.commit()
    current_app.logger.info(f'Created user: {email}')


def handle_user_updated(user_data: dict):
    """Update an existing user from Clerk data."""
    user = User.query.get(user_data['id'])
    if not user:
        # User doesn't exist yet, create them
        handle_user_created(user_data)
        return

    email = get_primary_email(user_data)
    if email:
        user.email = email
    user.first_name = user_data.get('first_name')
    user.last_name = user_data.get('last_name')
    user.image_url = user_data.get('image_url')
    user.updated_at = now_iso8601()

    db.session.commit()
    current_app.logger.info(f'Updated user: {user.email}')


def handle_user_deleted(user_data: dict):
    """Soft delete a user (set is_active=False)."""
    user = User.query.get(user_data['id'])
    if user:
        user.is_active = False
        user.updated_at = now_iso8601()
        db.session.commit()
        current_app.logger.info(f'Deactivated user: {user.email}')


def get_primary_email(user_data: dict) -> str:
    """Extract primary email from Clerk user data."""
    email_addresses = user_data.get('email_addresses', [])
    if email_addresses:
        # Find primary email or use first one
        for email in email_addresses:
            if email.get('id') == user_data.get('primary_email_address_id'):
                return email.get('email_address')
        return email_addresses[0].get('email_address')
    return None


def verify_webhook_signature(payload: bytes, signature: str, secret: str) -> bool:
    """
    Verify Clerk webhook signature.

    Note: In production, use the Svix library for proper verification.
    This is a simplified version for development.
    """
    if not signature or not secret:
        return False

    try:
        expected = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()

        # Signature format may vary, handle common formats
        return hmac.compare_digest(signature, expected) or \
               hmac.compare_digest(signature, f'sha256={expected}')
    except Exception:
        return False


@auth_bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """
    Get current authenticated user info.

    If user doesn't exist in database yet (webhook hasn't fired),
    create them from the JWT claims.
    """
    user_id = get_current_user_id()

    if not user_id:
        return jsonify({
            'success': False,
            'error': 'Not authenticated'
        }), 401

    user = User.query.get(user_id)

    if not user:
        # User authenticated via Clerk but not in our DB yet
        # This can happen if webhook hasn't fired yet
        # Create a placeholder user (will be updated by webhook)
        current_app.logger.info(f'Creating placeholder user: {user_id}')
        user = User(
            id=user_id,
            email=f'{user_id}@placeholder.metads.com',
            created_at=now_iso8601()
        )
        db.session.add(user)
        db.session.commit()

    if not user.is_active:
        return jsonify({
            'success': False,
            'error': 'User account is deactivated'
        }), 403

    return jsonify({
        'success': True,
        'data': user.to_dict()
    })
