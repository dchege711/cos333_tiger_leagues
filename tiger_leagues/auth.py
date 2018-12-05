"""
auth.py

Handles authentication-related requests e.g. `login`, `logout`
Exposes a blueprint that handles requests made to `` endpoint

"""

from flask import Blueprint, render_template, session, redirect, url_for
from . import user

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
    @todo: Implement this

    Use CAS to log in users This method will probably need more URLs/methods. Resources:
    https://www.cs.princeton.edu/courses/archive/fall18/cos333/lectures/14websecurity/PennyBottleCas/

    At the end of the CAS-related stuff, the rest of the application expects to 
    find a user object set in the flask session. 
    http://flask.pocoo.org/docs/1.0/api/#flask.session

    Note that the contents of the session are public, but immutable. Please 
    exclude values that you would not like the world to see. If sensitive data 
    is needed, leave it to the caller to query the database themselves.

    The return value for the whole CAS dance should be a redirect:

    Unsuccessful CAS Login --> Redirect to login page
    Successful CAS & new user --> Redirect to user.display_user_profile
    Successful CAS & returning user --> Redirect to /league

    Potentially useful files: ./user.py

    """
    net_id_from_cas = "ixue"

    session["user"] = user.get_user(net_id_from_cas)
    if session.get("user") is not None: 
        return redirect(url_for("league.index"))
    return redirect(url_for("user.display_user_profile"))
