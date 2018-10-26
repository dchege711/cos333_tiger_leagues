# Contents

1. [Setup Notes](#setup-notes)

## Setup Notes

* We modelled the application after this [tutorial](http://flask.pocoo.org/docs/1.0/tutorial/).
* Installing `Flask` usually installs `ItsDangerous` v1.0.0 as a prerequisite. However, Heroku cannot install v1.0.0. For this reason, `./requirements.txt` should have `ItsDangerous==0.24`.
* To run the application as it would on Heroku, run `$ heroku local web`.
* To run the application using the Flask server, run `$ ./run_flask_server`
