import os
from typing import Optional
import logging

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load environment variables
EMAIL_HOST: str = os.getenv('EMAIL_HOST', 'smtp.example.com')
logger.info(f"EMAIL_HOST set to: {EMAIL_HOST}")
"""
The SMTP server host for sending emails.
Default: 'smtp.example.com'
"""

EMAIL_PORT: int = int(os.getenv('EMAIL_PORT', 587))
logger.info(f"EMAIL_PORT set to: {EMAIL_PORT}")
"""
The SMTP server port for sending emails.
Default: 587
"""

EMAIL_USER: str = os.getenv('EMAIL_USER', 'user@example.com')
logger.info(f"EMAIL_USER set to: {EMAIL_USER}")
"""
The username for authenticating with the SMTP server.
Default: 'user@example.com'
"""

EMAIL_PASSWORD: str = os.getenv('EMAIL_PASSWORD', 'password')
logger.info(f"EMAIL_PASSWORD set to: {'*' * len(EMAIL_PASSWORD)}")
"""
The password for authenticating with the SMTP server.
Default: 'password'
"""

API_KEY: str = os.getenv('API_KEY', 'your_api_key_here')
logger.info(f"API_KEY set to: {'*' * len(API_KEY)}")
"""
The API key for accessing external services.
Default: 'your_api_key_here'
"""

# Add more settings as needed