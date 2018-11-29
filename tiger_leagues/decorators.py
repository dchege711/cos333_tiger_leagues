"""
decorators.py

Central point for all decorator functions.

"""

from functools import wraps
from flask import session, redirect, url_for, request

def login_required(f):
    """
    A decorator function that is used to confirm that a user is logged in before 
    viewing/using certain URLs.

    http://flask.pocoo.org/docs/1.0/patterns/viewdecorators/#login-required-decorator
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user") is None:
            return redirect(url_for("index", next=request.url))
        return f(*args, **kwargs)
    return decorated_function
