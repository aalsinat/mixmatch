"""
Mktinabox settings for extension project.

For more information on this file, see
https://docs.mktinabox.com/en/1.0/topics/settings/

For the full list of settings and their values, see
https://docs.mktinabox.com/en/1.0/ref/settings/
"""

import os
import sys

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = sys._MEIPASS if getattr(sys, 'frozen', False) else os.path.dirname(os.path.abspath(__file__))
# --------------------------------------------------
# This code is useful for onefile pyinstaller option
# --------------------------------------------------
# BASE_DIR = os.path.dirname(sys.executable)

# Use every particular section as a parameter for constructors
PROPERTIES_FILE = os.path.join(BASE_DIR, 'properties.ini')
