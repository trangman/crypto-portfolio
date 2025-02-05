import os
import sys
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    filename='app_error.log',
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s'
)

# Get the username from the current path
current_path = Path(__file__).resolve()
username = current_path.parts[2]  # /home/username/...

# Set the correct Python interpreter path
INTERP = f"/home/{username}/virtualenv/app.barbicancapitalmanagement.com/3.9/bin/python"
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

cwd = os.path.dirname(os.path.abspath(__file__))

# Add the virtual environment site-packages
VENV_PATH = f'/home/{username}/virtualenv/app.barbicancapitalmanagement.com/3.9/lib/python3.9/site-packages'
if os.path.exists(VENV_PATH):
    sys.path.insert(0, VENV_PATH)

# Add the application directory to the Python path
sys.path.insert(0, cwd)

try:
    # Load environment variables from .env file if it exists
    env_path = os.path.join(cwd, '.env')
    if os.path.exists(env_path):
        from dotenv import load_dotenv
        load_dotenv(env_path)
        logging.info("Loaded environment variables from .env file")

    # Set critical environment variables if not already set
    if not os.getenv('DATABASE_URL'):
        logging.warning("DATABASE_URL not set in environment")
    
    # Import the Flask application
    from app import app as application
    
    # Log environment variables (excluding sensitive ones)
    logging.info("Environment Configuration:")
    safe_vars = ['FLASK_ENV', 'SITE_URL', 'COMPANY_NAME']
    for key in safe_vars:
        if os.getenv(key):
            logging.info(f"{key}: {os.getenv(key)}")

    # Log database configuration (without credentials)
    db_url = os.getenv('DATABASE_URL', '')
    if db_url:
        # Mask the password in the URL for logging
        from urllib.parse import urlparse
        parsed = urlparse(db_url)
        masked_url = f"{parsed.scheme}://{parsed.username}:****@{parsed.hostname}/{parsed.path.lstrip('/')}"
        logging.info(f"Database URL: {masked_url}")

except Exception as e:
    logging.error(f"Error in passenger_wsgi.py: {str(e)}", exc_info=True)
    raise 