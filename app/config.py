"""Configuration module for the TicTacToe API.

This module provides configuration classes for different environments:
- BaseConfig: Base configuration with common settings
- DevelopmentConfig: Configuration for development environment
- ProductionConfig: Configuration for production environment
- TestingConfig: Configuration for testing environment

The configuration can be selected using the FLASK_ENV environment variable:
- development (default)
- production
- testing

Environment variables:
    - SECRET_KEY: Application secret key
    - FLASK_DEBUG: Enable debug mode (1 or 0)
    - LOG_LEVEL: Logging level (INFO, DEBUG, etc.)
    - DATABASE_URL: Database connection URL
    - CORS_ORIGINS: Comma-separated list of allowed origins
    - MAX_GAME_HISTORY: Maximum number of games to keep in history
"""
import os
from pathlib import Path
from typing import Any, Dict

def get_env_var(name: str, default: Any = None, var_type: type = str) -> Any:
    """Get environment variable with type conversion.

    Args:
        name: Name of the environment variable
        default: Default value if environment variable is not set
        var_type: Type to convert the value to

    Returns:
        The environment variable value converted to the specified type
    """
    value = os.environ.get(name)
    if value is None:
        return default
    try:
        if var_type == bool:
            return value.lower() in ('true', '1', 'yes')
        return var_type(value)
    except (ValueError, TypeError):
        return default

class BaseConfig:
    """Base configuration class for the TicTacToe API.
    
    Attributes:
        SECRET_KEY (str): Secret key for session management
        BASEDIR (Path): Base directory path
        SQLITE_DB_PATH (Path): SQLite database file path
        SQLALCHEMY_DATABASE_URI (str): SQLAlchemy database URI
        SQLALCHEMY_TRACK_MODIFICATIONS (bool): SQLAlchemy track modifications flag
        PORT (int): Application port number
        HOST (str): Application host address
        DEBUG (bool): Debug mode flag
        CORS_HEADERS (list): Allowed headers for CORS
        CORS_ORIGINS (list): Allowed origins for CORS
        CORS_METHODS (list): Allowed methods for CORS
        LOG_LEVEL (str): Logging level
    """
    # Flask configuration
    SECRET_KEY = get_env_var('SECRET_KEY', 'dev-secret-key')
    
    # Security configuration
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    PERMANENT_SESSION_LIFETIME = 3600  # 1 hour
    
    # CORS configuration
    CORS_HEADERS = ['Content-Type', 'Authorization']
    CORS_ORIGINS = ['http://localhost:3000', 'http://127.0.0.1:3000']
    CORS_METHODS = ['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS']
    CORS_MAX_AGE = 600  # 10 minutes
    
    # Database configuration
    BASEDIR = Path(__file__).parent.parent
    SQLITE_DB_PATH = BASEDIR / 'instance' / 'tictactoe.db'
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{SQLITE_DB_PATH}'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Application configuration
    PORT = get_env_var('PORT', 5010, int)
    HOST = get_env_var('HOST', '0.0.0.0')
    DEBUG = get_env_var('FLASK_DEBUG', False, bool)
    MAX_GAME_HISTORY = get_env_var('MAX_GAME_HISTORY', 100, int)
    
    # Logging configuration
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FORMAT = '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
    LOG_FILE = str(BASEDIR / 'logs' / 'tictactoe.log')
    LOG_MAX_BYTES = 10485760  # 10MB
    LOG_BACKUP_COUNT = 10

    @classmethod
    def init_app(cls, app):
        """Initialize application configuration.

        Args:
            app: Flask application instance
        """
        # Ensure logs directory exists
        log_dir = Path(cls.LOG_FILE).parent
        log_dir.mkdir(exist_ok=True)

        # Ensure instance directory exists
        instance_dir = Path(cls.SQLITE_DB_PATH).parent
        instance_dir.mkdir(exist_ok=True)

        # Set environment
        app.config['ENV'] = 'development' if cls == DevelopmentConfig else 'production'
        
        # Validate configuration
        cls.validate_config(app)
    
    @staticmethod
    def validate_config(app) -> None:
        """Validate configuration settings.

        Args:
            app: Flask application instance

        Raises:
            ValueError: If any configuration validation fails
        """
        required_settings = [
            'SECRET_KEY',
            'SQLALCHEMY_DATABASE_URI',
            'CORS_ORIGINS',
            'LOG_LEVEL'
        ]

        for setting in required_settings:
            if not app.config.get(setting):
                raise ValueError(f'Missing required configuration: {setting}')

        if app.config['DEBUG'] and app.config['ENV'] == 'production':
            raise ValueError('DEBUG should not be enabled in production')

        if not isinstance(app.config['CORS_ORIGINS'], (list, str)):
            raise ValueError('CORS_ORIGINS must be a list or string')


class DevelopmentConfig(BaseConfig):
    """Development configuration.
    
    Attributes:
        DEBUG (bool): Enable debug mode
        SQLALCHEMY_DATABASE_URI (str): Development database URI
    """
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = f'sqlite:///{BaseConfig.BASEDIR / "instance" / "tictactoe_dev.db"}'


class ProductionConfig(BaseConfig):
    """Production configuration.
    
    Attributes:
        DEBUG (bool): Disable debug mode
        SQLALCHEMY_DATABASE_URI (str): Production database URI
    """
    DEBUG = False
    SQLALCHEMY_DATABASE_URI = get_env_var(
        'DATABASE_URL',
        f'sqlite:///{BaseConfig.BASEDIR / "instance" / "tictactoe_prod.db"}'
    )

    # Override CORS settings for production
    CORS_ORIGINS = get_env_var(
        'CORS_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000'
    ).split(',')

    # Additional production security settings
    SESSION_COOKIE_SECURE = True
    PERMANENT_SESSION_LIFETIME = 1800  # 30 minutes


class TestingConfig(BaseConfig):
    """Testing configuration.
    
    Attributes:
        TESTING (bool): Enable testing mode
        DEBUG (bool): Enable debug mode
        SQLALCHEMY_DATABASE_URI (str): Testing database URI
        WTF_CSRF_ENABLED (bool): Disable CSRF protection in tests
    """
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    SERVER_NAME = 'localhost.localdomain'

    # Override security settings for testing
    SESSION_COOKIE_SECURE = False
    SESSION_COOKIE_HTTPONLY = True


# Configuration dictionary
config: Dict[str, type] = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}
