"""
auth.py

Handles authentication-related requests e.g. ``login``, ``logout``.
Exposes a blueprint that handles requests made to the `auth` endpoint

"""

from flask import (
    Blueprint, render_template, session, redirect, url_for, request
)
from . import cas_client
from .models import user_model

cas = cas_client.CASClient()
bp = Blueprint("auth", __name__, url_prefix="")

@bp.route("/", methods=["GET"])
def index():
    """
    :return: ``flask.Response(mimetype='text/HTML')`` 
    
    Render the login page if the person isn't logged in, otherwise render a 
    homepage for any of the leagues that they're involved in.

    """
    if session.get("user") is not None: 
        return redirect(url_for("league.index"))
    return render_template("/auth/login.html")

@bp.route("/login/", methods=["GET"])
def cas_login():
    """
    Log in users through CAS. At the end of the CAS-related stuff, the rest of 
    the application expects to find a user object set in the session object.

    Note that the contents of the session are public, but immutable. Please 
    exclude values that you would not like the world to see. If sensitive data 
    is needed, leave it to the caller to query the database themselves.

    :return: ``flask.Response(code=302)`` 
    
    A redirect to the account creation page for new users or the homepage for 
    any of the leagues that a returning user is associated with.

    """

    r = cas.authenticate(request, redirect, session)
    while not isinstance(r, str):
        return r

    net_id = r
    user_data = user_model.get_user(net_id)
    session["user"] = user_data
    session["net_id"] = net_id
    if user_data is not None:
        return redirect(url_for("league.index"))
    return redirect(url_for("user.display_user_profile"))

@bp.route("/logout/", methods=["GET"])
def cas_logout():
    """
    Log out the currently logged in user. 

    :return: ``flask.Response(code=302)``
    
    Redirect to the login page.

    """
    session.clear()
    return redirect(url_for("auth.index"))
    