import os
from datetime import timedelta

class Config:
    """Base configuration class."""
    
    # Flask Settings
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'traffic-sim-secret-key-2025'
    DEBUG = False
    TESTING = False
    
    # Database Configuration
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/trafficDB'
    MONGODB_HOST = os.environ.get('MONGODB_HOST') or 'localhost'
    MONGODB_PORT = int(os.environ.get('MONGODB_PORT', 27017))
    MONGODB_DB = os.environ.get('MONGODB_DB') or 'trafficDB'
    
    # API Configuration
    API_VERSION = 'v1'
    API_PREFIX = f'/api/{API_VERSION}'
    
    # CORS Settings
    CORS_ORIGINS = [
        'http://localhost:3000',  # React development server
        'http://127.0.0.1:3000',
        'http://localhost:3001',  # Alternative React port
    ]
    
    # Traffic Simulation Settings
    SIMULATION_CONFIG = {
        'MAX_VEHICLES': 200,
        'DEFAULT_SPEED': 25.0,
        'GRID_SIZE': {'width': 6, 'height': 6},
        'CELL_SIZE': {'width': 180, 'height': 120},
        'UPDATE_INTERVAL': 0.1,  # seconds
        'SPAWN_RATE': 0.3,
        'EMERGENCY_PRIORITY': True,
        'COLLISION_DETECTION': True
    }
    
    # Traffic Signal Configuration
    SIGNAL_CONFIG = {
        'MIN_GREEN_TIME': 15,
        'MAX_GREEN_TIME': 60,
        'AMBER_TIME': 4,
        'ALL_RED_TIME': 2,
        'EMERGENCY_OVERRIDE_DURATION': 120,  # seconds
        'ADAPTIVE_TIMING': True
    }
    
    # Emergency Vehicle Settings
    EMERGENCY_CONFIG = {
        'AMBULANCE': {
            'max_speed': 60,
            'acceleration': 6.0,
            'priority': 10,
            'color': '#e74c3c'
        },
        'FIRE_TRUCK': {
            'max_speed': 55,
            'acceleration': 5.5,
            'priority': 9,
            'color': '#e67e22'
        },
        'POLICE': {
            'max_speed': 65,
            'acceleration': 6.5,
            'priority': 8,
            'color': '#3498db'
        }
    }
    
    # Vehicle Types Configuration
    VEHICLE_TYPES = {
        'car': {
            'max_speed': 35,
            'acceleration': 3.0,
            'length': 4.5,
            'spawn_probability': 0.7
        },
        'truck': {
            'max_speed': 25,
            'acceleration': 2.0,
            'length': 8.0,
            'spawn_probability': 0.2
        },
        'bus': {
            'max_speed': 22,
            'acceleration': 2.5,
            'length': 12.0,
            'spawn_probability': 0.1
        }
    }
    
    # Performance Settings
    PERFORMANCE = {
        'MAX_SIMULATION_FPS': 60,
        'DATABASE_POOL_SIZE': 10,
        'CACHE_TIMEOUT': 300,  # seconds
        'LOG_LEVEL': 'INFO'
    }
    
    # Logging Configuration
    LOG_CONFIG = {
        'version': 1,
        'disable_existing_loggers': False,
        'formatters': {
            'default': {
                'format': '[%(asctime)s] %(levelname)s in %(module)s: %(message)s',
            }
        },
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
                'level': 'INFO',
                'formatter': 'default',
                'stream': 'ext://sys.stdout'
            },
            'file': {
                'class': 'logging.FileHandler',
                'level': 'DEBUG',
                'formatter': 'default',
                'filename': 'logs/traffic_simulation.log',
                'mode': 'a'
            }
        },
        'root': {
            'level': 'DEBUG',
            'handlers': ['console', 'file']
        }
    }
    
    # Rate Limiting
    RATELIMIT_STORAGE_URL = 'memory://'
    RATELIMIT_DEFAULT = "100 per hour"
    
    # JWT Settings (if using authentication)
    JWT_SECRET_KEY = os.environ.get('JWT_SECRET_KEY') or 'jwt-secret-key'
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)
    
    # File Upload Settings (for importing traffic data)
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB
    UPLOAD_FOLDER = 'uploads/'
    ALLOWED_EXTENSIONS = {'json', 'csv', 'txt'}

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
    # Relaxed CORS for development
    CORS_ORIGINS = ['*']  # Allow all origins in development
    
    # More verbose logging
    LOG_CONFIG = Config.LOG_CONFIG.copy()
    LOG_CONFIG['root']['level'] = 'DEBUG'
    
    # Development-specific simulation settings
    SIMULATION_CONFIG = Config.SIMULATION_CONFIG.copy()
    SIMULATION_CONFIG.update({
        'MAX_VEHICLES': 100,  # Lower limit for development
        'UPDATE_INTERVAL': 0.2,  # Slower updates for easier debugging
    })

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Secure settings for production
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Production database (could be remote)
    MONGODB_URI = os.environ.get('MONGODB_URI') or 'mongodb://localhost:27017/trafficDB_prod'
    
    # Stricter CORS
    CORS_ORIGINS = [
        'https://your-domain.com',
        'https://www.your-domain.com'
    ]
    
    # Production logging
    LOG_CONFIG = Config.LOG_CONFIG.copy()
    LOG_CONFIG['root']['level'] = 'WARNING'
    LOG_CONFIG['handlers']['file']['filename'] = '/var/log/traffic_simulation.log'

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    
    # Use test database
    MONGODB_DB = 'trafficDB_test'
    
    # Disable rate limiting for tests
    RATELIMIT_ENABLED = False
    
    # Fast simulation for testing
    SIMULATION_CONFIG = Config.SIMULATION_CONFIG.copy()
    SIMULATION_CONFIG.update({
        'UPDATE_INTERVAL': 0.01,
        'MAX_VEHICLES': 50
    })

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """Get configuration based on environment variable."""
    env = os.environ.get('FLASK_ENV', 'development')
    return config.get(env, config['default'])

# Helper functions for accessing config values
def get_simulation_config():
    """Get simulation configuration."""
    return get_config().SIMULATION_CONFIG

def get_signal_config():
    """Get traffic signal configuration."""
    return get_config().SIGNAL_CONFIG

def get_emergency_config(vehicle_type=None):
    """Get emergency vehicle configuration."""
    emergency_config = get_config().EMERGENCY_CONFIG
    if vehicle_type:
        return emergency_config.get(vehicle_type.upper(), {})
    return emergency_config

def get_vehicle_config(vehicle_type=None):
    """Get vehicle type configuration."""
    vehicle_config = get_config().VEHICLE_TYPES
    if vehicle_type:
        return vehicle_config.get(vehicle_type, vehicle_config['car'])
    return vehicle_config

# Environment-specific settings
if os.environ.get('FLASK_ENV') == 'production':
    # Production-specific imports and setup
    import logging
    logging.basicConfig(level=logging.WARNING)
