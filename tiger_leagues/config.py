"""
config.py

The central source for variables that span the entire application. As a rule of 
thumb, if you find yourself using `os.environ`, you should probably include the 
variable here instead.

"""

from os import environ
import subprocess

APP_ENV = environ["TIGER_LEAGUES_ENVIRONMENT"]

DATABASE_URL = environ["DATABASE_URL"]

