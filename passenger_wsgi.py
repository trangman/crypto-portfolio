import os
import sys

# Add the application directory to the Python path
VENV_PATH = os.path.join(os.getcwd(), 'venv')
PYTHON_VERSION = '3.9'  # Change this to match your Python version
INTERP = os.path.join(VENV_PATH, 'bin', 'python')

if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

# Add your application directory to the Python path
sys.path.append(os.getcwd())

# Import the Flask application
from app import app as application

# This is the entry point for Passenger WSGI
application.secret_key = os.getenv('SECRET_KEY', 'your-secret-key-here') 