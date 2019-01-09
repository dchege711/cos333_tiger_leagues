"""
decorators.py

A decorator is a function that wraps and replaces another function. If there's 
a functionality that you wish to extend to multiple functions, you should 
probably add the functionality as a decorator.

http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/

"""

from functools import wraps
from flask import session, redirect, url_for
from tiger_leagues.models import user_model

def login_required(f):
    """
    A decorator function that is used to confirm that a user is logged in before 
    viewing/using certain URLs.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/#login-required-decorator

    :param f: ``function``

    A function that should be accessed only by authenticated users.

    :return: ``flask.Response(code=302)``

    If the user isn't logged in, redirect them to the application's login page.

    :return: ``function``

    If the user is logged in, return a function that is equal to the one 
    that was passed as a parameter
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("net_id") is None:
            return redirect(url_for("auth.index"))
        return f(*args, **kwargs)
    return decorated_function

def refresh_user_profile(f):
    """
    A decorator function that is updates the user object stored in the session 
    object. This is helpful when keeping the user up to date.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/#login-required-decorator

    :param f: ``function``

    A function that would benefit from an updated user object

    :return: ``function``

    The incoming function is always returned as updating the user object is a 
    side effect.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        prev_user_profile = session.get("user")
        if prev_user_profile is not None:
            session["user"] = user_model.get_user(prev_user_profile["net_id"])
        return f(*args, **kwargs)
    return decorated_function
