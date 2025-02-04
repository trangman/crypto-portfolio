import os
import sys

# Add the application directory to the Python path
INTERP = os.path.expanduser("/home/USERNAME/virtualenv/crypto_portfolio/3.13/bin/python")
if sys.executable != INTERP:
    os.execl(INTERP, INTERP, *sys.argv)

sys.path.append(os.getcwd())

from wsgi import app as application 