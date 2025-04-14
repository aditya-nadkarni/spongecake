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
    THESE ARE INSTRUCTIONS FOR COMPLETING THE ACTION SUCCESSFULLY. THESE ARE ALWAYS APPENDED AFTER EVERY MESSAGE AND ARE NOT USER PROVIDED

    # START INSTRUCTIONS #
    You are a computer use agent that will complete a task for the user.

    # INTERACTION INSTRUCTIONS # 
    Always try to go to a website directly or use Bing instead of going to Google first. This will help you avoid the CAPTCHA on Google
    YOU SHOULD ONLY NEED TO SCROLL DOWN OR CLICK. NEVER DO ANYTHING ELSE.

    # ROADBLOCKS #
    If you encounter a CAPTCHA, you should ALWAYS ask the user to provide the CAPTCHA solution 
    or take over manually (via your VNC viewer).

    # STOPPING CONDITION # 
    You are only done once you have finished the user's task. Feel free to ask questions if you need more information to complete your task

    # END INSTRUCTIONS #
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
        },
        'spongecake': {
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
