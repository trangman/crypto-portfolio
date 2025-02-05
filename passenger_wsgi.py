import os
import sys
import logging

# Set up logging
logging.basicConfig(
    filename='app_error.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Get the absolute path of the current directory
INTERP = os.path.dirname(os.path.abspath(__file__))

# Add the virtual environment site-packages
if os.path.exists(os.path.join(INTERP, 'venv')):
    VENV_PATH = os.path.join(INTERP, 'venv', 'Lib', 'site-packages')
else:
    VENV_PATH = os.path.join(INTERP, 'virtualenv', 'Lib', 'site-packages')

if os.path.exists(VENV_PATH):
    sys.path.insert(0, VENV_PATH)

# Add the application directory to the Python path
sys.path.insert(0, INTERP)

try:
    # Import the Flask application
    from app import app as application
    
    # Log environment variables (excluding sensitive ones)
    logging.info("Environment Configuration:")
    safe_vars = ['FLASK_ENV', 'SITE_URL', 'COMPANY_NAME']
    for key in safe_vars:
        if os.getenv(key):
            logging.info(f"{key}: {os.getenv(key)}")

except Exception as e:
    logging.error(f"Error in passenger_wsgi.py: {str(e)}", exc_info=True)
    raise 