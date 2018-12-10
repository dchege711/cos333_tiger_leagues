"""
auth.py

Handles authentication-related requests e.g. `login`, `logout`
Exposes a blueprint that handles requests made to `` endpoint

"""

from flask import (
    Blueprint, render_template, session, redirect, url_for, request
)
from . import user, cas_client

cas = cas_client.CASClient()
bp = Blueprint("auth", __name__, url_prefix="")

@bp.route("/", methods=["GET"])
def index():
    """
    @GET Render the login page if the person isn't logged in, otherwise 
    transfer them to the `league.index()` method.

    """
    return render_template("/auth/login.html")

@bp.route("/cas", methods=["GET"])
def cas_login():
    """
    Log in users through CAS. At the end of the CAS-related stuff, the rest of 
    the application expects to find a user object set in the flask session. 
    http://flask.pocoo.org/docs/1.0/api/#flask.session

    Note that the contents of the session are public, but immutable. Please 
    exclude values that you would not like the world to see. If sensitive data 
    is needed, leave it to the caller to query the database themselves.

    @returns 302 Response: A redirect to the account creation page for new users 
    or the league homepage for returning users.

    """

    r = cas.authenticate(request, redirect, session)
    while not isinstance(r, str):
        return r

    user_data = user.get_user(r)
    session["user"] = user_data
    if user_data is not None:
        return redirect(url_for("league.index"))
    return redirect(url_for("user.display_user_profile"))
