import os
import sys
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG)

# Add the application directory to the Python path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, BASE_DIR)

logging.debug(f"Base directory: {BASE_DIR}")
logging.debug(f"Python path: {sys.path}")

try:
    from main import wsgi_app as application
    logging.debug("Successfully imported application")
except Exception as e:
    logging.error(f"Failed to import application: {str(e)}")
    raise