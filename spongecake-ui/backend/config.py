"""
Configuration settings for the Spongecake backend server.
"""
import os
import logging.config

# Configuration class
class Config:
    """Configuration settings for the Spongecake server."""
    NOVNC_BASE_PORT = 6080
    NOVNC_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "noVNC-1.6.0")
    VNC_HOST = "localhost"
    FLASK_PORT = 5000
    CONTAINER_NAME = "computer_use_agent"
    MAX_PORT_ATTEMPTS = 100
    DEFAULT_PROMPT_SUFFIX = """
    If a user mentioned going to a website, always start by trying to go directly to the URL or using Bing instead of going to Google first.
    """

# Logging configuration
LOGGING_CONFIG = {
    'version': 1,
    'formatters': {
        'standard': {
            'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'stream': 'ext://sys.stdout'
        },
        'file': {
            'class': 'logging.handlers.RotatingFileHandler',
            'level': 'INFO',
            'formatter': 'standard',
            'filename': os.path.join(os.path.dirname(os.path.abspath(__file__)), 'spongecake_server.log'),
            'maxBytes': 10485760,  # 10MB
            'backupCount': 5
        }
    },
    'loggers': {
        '': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True
        }
    }
}

def setup_logging():
    """Configure the logging system."""
    logging.config.dictConfig(LOGGING_CONFIG)
    return logging.getLogger(__name__)
