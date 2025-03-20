from flask import Flask, jsonify, request
from flask_cors import CORS
import logging
from logging.handlers import RotatingFileHandler
import os
from typing import Optional

from app.config import config
from app.extensions import db
from app.database import init_db

# PUBLIC_INTERFACE
def create_app(config_name: Optional[str] = None) -> Flask:
    """Create and configure the Flask application.
    
    Args:
        config_name: Name of the configuration to use (default: None, uses FLASK_ENV or 'default')
        
    Returns:
        Flask: Configured Flask application instance
    """
    app = Flask(__name__)
    
    # Load configuration based on environment
    if config_name is None:
        config_name = os.environ.get('FLASK_ENV', 'default')
    
    if config_name not in config:
        app.logger.error(f'Invalid configuration name: {config_name}')
        config_name = 'default'
    
    try:
        app.config.from_object(config[config_name])
        config[config_name].init_app(app)
        app.logger.info(f'Loaded configuration: {config_name}')
    except Exception as e:
        app.logger.error(f'Error loading configuration: {str(e)}')
        raise
    
    # Initialize CORS with security headers from configuration
    CORS(app, resources={
        r"/*": {
            "origins": app.config['CORS_ORIGINS'],
            "methods": app.config['CORS_METHODS'],
            "allow_headers": app.config['CORS_HEADERS']
        }
    })
    
    # Set security headers
    @app.after_request
    def add_security_headers(response):
        # Security headers based on OWASP recommendations
        response.headers['X-Content-Type-Options'] = 'nosniff'
        response.headers['X-Frame-Options'] = 'SAMEORIGIN'
        response.headers['X-XSS-Protection'] = '1; mode=block'
        response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
        response.headers['Content-Security-Policy'] = "default-src 'self'; script-src 'self'; object-src 'none'"
        response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
        response.headers['Permissions-Policy'] = 'geolocation=(), microphone=(), camera=()'
        
        # Remove sensitive headers
        response.headers.pop('Server', None)
        response.headers.pop('X-Powered-By', None)
        
        return response
    
    # Setup logging
    try:
        if not app.debug:
            if not os.path.exists('logs'):
                os.mkdir('logs')
            file_handler = RotatingFileHandler(
                app.config['LOG_FILE'],
                maxBytes=app.config['LOG_MAX_BYTES'],
                backupCount=app.config['LOG_BACKUP_COUNT']
            )
            file_handler.setFormatter(logging.Formatter(app.config['LOG_FORMAT']))
            file_handler.setLevel(getattr(logging, app.config['LOG_LEVEL']))
            app.logger.addHandler(file_handler)
            app.logger.setLevel(getattr(logging, app.config['LOG_LEVEL']))
    except Exception as e:
        app.logger.error(f'Error setting up logging: {str(e)}')
        raise
    
    app.logger.info('TicTacToe API startup')
    app.logger.info(f'Environment: {app.config["ENV"]}')
    app.logger.info(f'Debug: {app.config["DEBUG"]}')
    
    # Initialize extensions
    db.init_app(app)
    
    # Initialize database
    init_db(app)
    
    # Register blueprints
    from app.routes import main
    app.register_blueprint(main.bp)
    
    # Add health check endpoint
    @app.route('/health')
    def health_check():
        return jsonify({'status': 'healthy'}), 200
    
    # Register error handlers
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            'error': 'Bad Request',
            'message': str(error.description)
        }), 400

    @app.errorhandler(404)
    def not_found_error(error):
        return jsonify({
            'error': 'Not Found',
            'message': 'The requested resource was not found'
        }), 404

    @app.errorhandler(405)
    def method_not_allowed_error(error):
        return jsonify({
            'error': 'Method Not Allowed',
            'message': 'The method is not allowed for this endpoint'
        }), 405

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f'Server Error: {error}')
        return jsonify({
            'error': 'Internal Server Error',
            'message': 'An unexpected error has occurred'
        }), 500
    
    return app
