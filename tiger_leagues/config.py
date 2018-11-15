"""
config.py

The central source for variables that span the entire application. As a rule of 
thumb, if you find yourself using `os.environ`, you should probably include the 
variable here instead.

"""

from os import environ
import subprocess

APP_ENV = environ["TIGER_LEAGUES_ENVIRONMENT"]

DATABASE_URL = ""
if APP_ENV == "development":
    # ... then we're on our local machines and should ask Heroku for the URL
    results = subprocess.run(["heroku", "config:get", "DATABASE_URL"], capture_output=True)
    DATABASE_URL = results.stdout.decode("utf-8").strip()
elif APP_ENV == "production":
    # ... otherwise the app is running on Heroku and the URL is already set
    DATABASE_URL = environ["DATABASE_URL"]
else:
    raise RuntimeError(
        "Please set the `TIGER_LEAGUES_ENVIRONMENT` to either `development` or `production`"
    )

