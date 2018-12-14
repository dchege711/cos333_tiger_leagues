# Contents

1. [Setup Notes](#setup-notes)

## Setup Notes

* We modelled the application after this [tutorial](http://flask.pocoo.org/docs/1.0/tutorial/).
* Installing `Flask` usually installs `ItsDangerous` v1.0.0 as a prerequisite. However, Heroku cannot install v1.0.0. For this reason, `./requirements.txt` should have `ItsDangerous==0.24`.
* To run the application as it would on Heroku, run `$ heroku local web`.
* To run the application using the Flask server, run `$ ./run_flask_server`

## Setting Up a Local PostgreSQL Database

* Heroku can change the connection URI at anytime. We started by using `subprocess.run` to get the most current connection string. However, it seems that the child processes do not get terminated appropriately. Restarting the initialization script a couple of times leads to a shortage of I/O resources.

* We'll therefore use a local database for development purposes. I found this tutorial useful [https://www.codementor.io/engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb](https://www.codementor.io/engineerapart/getting-started-with-postgresql-on-mac-osx-are8jcopb) to set up PostgreSQL
