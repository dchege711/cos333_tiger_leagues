"""
config.py

The central source for variables that span the entire application. As a rule of 
thumb, if you find yourself using `os.environ`, you should probably include the 
variable here instead.

Expected environment variables: ``TIGER_LEAGUES_ENVIRONMENT``, 
``TIGER_LEAGUES_POSTGRESQL_DBNAME``, ``TIGER_LEAGUES_POSTGRESQL_USERNAME``, 
``TIGER_LEAGUES_POSTGRESQL_PASSWORD``

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
elif APP_ENV == "travis_ci":
    DATABASE_URL = "host=localhost dbname=travis_ci_test user=postgres"
else:
    raise RuntimeError(
        "Please set the `TIGER_LEAGUES_ENVIRONMENT` to either `development` or `production`"
    )
