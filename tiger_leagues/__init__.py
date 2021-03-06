"""
__init__.py

Serves two functions:

* Contains the [application factory](http://flask.pocoo.org/docs/1.0/tutorial/factory/)
* Tells Python that the `tiger_leagues_app` directory should be treated as a package.

"""

import os
from flask import Flask, render_template
from .models.exception import TigerLeaguesException
from . import league, auth, user, admin, error

def create_app(test_config=None):
    """
    Create and configure the Flask application instance. Register the necessary 
    blueprints.

    :return: ``Flask`` 
    
    The Flask object acts as a central registry for the view functions, the URL 
    rules, template configuration, etc.

    """
    
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(SECRET_KEY='dev')

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass

    # Register blueprints
    app.register_blueprint(auth.bp)
    app.register_blueprint(league.bp) 
    app.register_blueprint(user.bp)
    app.register_blueprint(admin.bp)
    app.register_error_handler(TigerLeaguesException, error.report_error)
    
    return app
