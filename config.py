import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    # General Application Settings
    APP_ENV = os.getenv('APP_ENV', 'development')
    APP_DEBUG = os.getenv('APP_DEBUG', 'True') == 'True'

    # File Monitoring Configuration
    MONITOR_DIRECTORY = os.getenv('MONITOR_DIRECTORY')
    LOG_FILE_PATH = os.getenv('LOG_FILE_PATH')

    # Email Configuration for Notifications
    EMAIL_HOST = os.getenv('EMAIL_HOST')
    EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
    EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
    EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True') == 'True'
    EMAIL_USE_SSL = os.getenv('EMAIL_USE_SSL', 'False') == 'True'

    # Flask Application Settings
    FLASK_RUN_PORT = int(os.getenv('FLASK_RUN_PORT', 5000))
    FLASK_RUN_HOST = os.getenv('FLASK_RUN_HOST', '127.0.0.1')
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    SECRET_KEY = os.getenv('SECRET_KEY')

    # Database Configuration (if applicable)

    # API keys for external services

# You can then import this Config class in other modules as needed
