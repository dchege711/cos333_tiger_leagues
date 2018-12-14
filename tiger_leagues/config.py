"""
config.py

The central source for variables that span the entire application. As a rule of 
thumb, if you find yourself using `os.environ`, you should probably include the 
variable here instead.

"""

from os import environ

APP_ENV = environ["TIGER_LEAGUES_ENVIRONMENT"]

DATABASE_URL = ""
if APP_ENV == "development":
    DATABASE_URL = "host=localhost dbname={} user={} password={}".format(
        environ["TIGER_LEAGUES_POSTGRESQL_DBNAME"],
        environ["TIGER_LEAGUES_POSTGRESQL_USERNAME"],
        environ["TIGER_LEAGUES_POSTGRESQL_PASSWORD"]
    )
elif APP_ENV == "production":
    # ... otherwise the app is running on Heroku and the URL is already set
    DATABASE_URL = environ["DATABASE_URL"]
else:
    raise RuntimeError(
        "Please set the `TIGER_LEAGUES_ENVIRONMENT` to either `development` or `production`"
    )
