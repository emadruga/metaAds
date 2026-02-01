"""
MetAds Backend Application Factory
"""
import os
from flask import Flask, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()


def create_app(config_name=None):
    """
    Application factory for creating Flask app instance.
    """
    app = Flask(__name__)

    # Load configuration
    from app.config import Config
    app.config.from_object(Config)

    # Ensure data directory exists
    backend_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    data_dir = os.path.join(backend_dir, 'data')
    os.makedirs(data_dir, exist_ok=True)

    # Fix database path for SQLite - make relative paths absolute
    db_url = app.config.get('SQLALCHEMY_DATABASE_URI', '')
    if db_url.startswith('sqlite:///') and not db_url.startswith('sqlite:////'):
        # Extract relative path
        db_path = db_url.replace('sqlite:///', '')
        # Make it absolute relative to backend directory
        if not os.path.isabs(db_path):
            db_path = os.path.join(backend_dir, db_path)
        app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
        app.logger.info(f"Database path: {db_path}")

    # Initialize extensions
    db.init_app(app)

    # Configure CORS
    CORS(app,
         origins=app.config.get('CORS_ORIGINS', '*').split(','),
         supports_credentials=True)

    # Register blueprints
    from app.routes.auth import auth_bp
    from app.routes.niches import niches_bp
    from app.routes.ads import ads_bp
    from app.routes.saved import saved_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(niches_bp)
    app.register_blueprint(ads_bp)
    app.register_blueprint(saved_bp)

    # Register health check endpoint
    @app.route('/api/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'version': '0.1.0',
            'dev_mode': app.config.get('DEV_AUTH_BYPASS', False)
        })

    # Register stats endpoint
    @app.route('/api/stats')
    def global_stats():
        """Global database statistics."""
        from app.middleware.auth import require_auth, get_current_user_id
        from app.models import Niche, Ad

        @require_auth
        def _get_stats():
            user_id = get_current_user_id()

            # Get user's niches
            niches = Niche.query.filter_by(user_id=user_id, is_active=True).all()
            niche_ids = [n.niche_id for n in niches]

            # Get ads across all user's niches
            total_ads = Ad.query.filter(Ad.niche_id.in_(niche_ids)).count() if niche_ids else 0
            active_ads = Ad.query.filter(
                Ad.niche_id.in_(niche_ids),
                Ad.is_active == True
            ).count() if niche_ids else 0
            saved_ads = Ad.query.filter(
                Ad.niche_id.in_(niche_ids),
                Ad.is_saved == True
            ).count() if niche_ids else 0

            return jsonify({
                'success': True,
                'data': {
                    'total_niches': len(niches),
                    'total_ads': total_ads,
                    'active_ads': active_ads,
                    'saved_ads': saved_ads
                }
            })

        return _get_stats()

    # Error handlers
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({'success': False, 'error': 'Not found'}), 404

    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({'success': False, 'error': 'Internal server error'}), 500

    # Create tables
    with app.app_context():
        db.create_all()

    return app
