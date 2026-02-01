"""
Clerk Authentication Middleware

Validates JWT tokens from Clerk and extracts user information.
All protected routes use the @require_auth decorator.

Dev Mode:
    Set DEV_AUTH_BYPASS=true in .env to bypass authentication for local testing.
    This will use DEV_USER_ID as the authenticated user.
"""
from functools import wraps
from flask import request, g, jsonify, current_app
import jwt


def require_auth(f):
    """
    Decorator to protect routes with Clerk authentication.
    Extracts user_id from JWT and adds to Flask's g object.

    In dev mode (DEV_AUTH_BYPASS=true), bypasses authentication
    and uses DEV_USER_ID instead.

    Usage:
        @app.route('/api/protected')
        @require_auth
        def protected_route():
            user_id = get_current_user_id()
            return {'user_id': user_id}
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        # Check for dev mode bypass
        if current_app.config.get('DEV_AUTH_BYPASS', False):
            g.user_id = current_app.config.get('DEV_USER_ID', 'dev_user_001')
            g.session_id = 'dev_session'
            current_app.logger.debug(f'Dev mode: using user_id={g.user_id}')
            return f(*args, **kwargs)

        # Normal authentication flow
        auth_header = request.headers.get('Authorization')

        if not auth_header or not auth_header.startswith('Bearer '):
            return jsonify({
                'success': False,
                'error': 'Missing or invalid authorization header'
            }), 401

        token = auth_header.split(' ')[1]

        try:
            clerk_secret = current_app.config.get('CLERK_SECRET_KEY')

            if not clerk_secret:
                current_app.logger.warning('CLERK_SECRET_KEY not configured')
                return jsonify({
                    'success': False,
                    'error': 'Authentication not configured. Set DEV_AUTH_BYPASS=true for local testing.'
                }), 500

            # Verify JWT with Clerk
            try:
                payload = verify_clerk_token(token, clerk_secret)

                if payload:
                    g.user_id = payload.get('sub')
                    g.session_id = payload.get('sid')
                else:
                    return jsonify({
                        'success': False,
                        'error': 'Invalid token'
                    }), 401

            except jwt.ExpiredSignatureError:
                return jsonify({
                    'success': False,
                    'error': 'Token has expired'
                }), 401
            except jwt.InvalidTokenError as e:
                current_app.logger.error(f'JWT validation error: {e}')
                return jsonify({
                    'success': False,
                    'error': 'Invalid token'
                }), 401

            return f(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f'Auth error: {e}')
            return jsonify({
                'success': False,
                'error': 'Authentication failed'
            }), 401

    return decorated_function


def verify_clerk_token(token: str, secret_key: str) -> dict:
    """
    Verify a Clerk JWT token.

    Clerk uses RS256 with JWKS in production. For local development,
    we can use the secret key for basic verification or skip verification
    and trust the token structure.

    Args:
        token: JWT token string
        secret_key: Clerk secret key

    Returns:
        dict: Decoded token payload or None if invalid
    """
    try:
        # For development: decode without verification
        # In production: use Clerk's JWKS endpoint
        # https://clerk.com/docs/backend-requests/handling/verifying-tokens

        # Decode without verification to get claims
        unverified = jwt.decode(token, options={"verify_signature": False})

        # Verify issuer is from Clerk
        issuer = unverified.get('iss', '')
        if 'clerk' not in issuer.lower():
            return None

        # Check expiration
        import time
        exp = unverified.get('exp', 0)
        if exp < time.time():
            return None

        return unverified

    except Exception as e:
        return None


def get_current_user_id() -> str:
    """
    Get the current authenticated user's ID from Flask g object.

    Returns:
        str: Clerk user ID or None if not authenticated
    """
    return getattr(g, 'user_id', None)


def get_current_session_id() -> str:
    """
    Get the current session ID from Flask g object.

    Returns:
        str: Clerk session ID or None if not authenticated
    """
    return getattr(g, 'session_id', None)
