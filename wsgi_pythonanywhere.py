"""
PythonAnywhere WSGI Configuration File for The E-Library

Instructions for PythonAnywhere:
1. Go to your PythonAnywhere Web tab: https://www.pythonanywhere.com/user/<username>/webapps/
2. Click on your WSGI configuration file link (e.g. /var/www/<username>_pythonanywhere_com_wsgi.py).
3. Delete the default content and paste the code below.
4. Replace 'YOUR_PYTHONANYWHERE_USERNAME' with your actual PythonAnywhere username.
5. Save the file and reload your web app!
"""

import sys
import os

# --- 1. Set Project Directory in Python Path ---
# Replace 'YOUR_PYTHONANYWHERE_USERNAME' with your actual PythonAnywhere account username
username = 'YOUR_PYTHONANYWHERE_USERNAME'
project_home = f'/home/{username}/E-Library'

if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Set the current working directory to the project directory
try:
    os.chdir(project_home)
except Exception:
    pass

# --- 2. Optional Environment Variables ---
# os.environ['SECRET_KEY'] = 'your-custom-secret-key-here'

# --- 3. Import Flask WSGI Callable ---
# PythonAnywhere requires a variable named 'application'
from app import app as application
