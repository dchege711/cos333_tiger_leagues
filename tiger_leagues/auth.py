"""
auth.py

Handles authentication-related requests e.g. `login`, `logout`
Exposes a blueprint that handles requests made to `` endpoint

"""

import requests as python_requests
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

@bp.route("/cas", methods=["GET", "POST"])
def cas_login():
    """
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
    if request.method == "GET":

        if request.args.get("ticket"):
            print("Ticket:", request.url, "\n")
            cas_response = python_requests.get(
                "https://fed.princeton.edu/validate",
                params={
                    "service": url_for(".cas_login", _external=True),
                    "ticket": request.args.get("ticket")
                }
            )
            return cas_response.text

        else:
            print("Non-ticket URL:", request.url, "\n")
            return redirect(
                "https://fed.princeton.edu/cas/login?service={}".format(
                    url_for(".cas_login", _external=True)
                )
            )


    # cas.authenticate(request, redirect, session)

    # if session.get("username"):
    #     session["user"] = user.get_user(session.get("username"))
    
    # if session.get("user") is not None: 
    #     return redirect(url_for("league.index"))
    # return redirect(url_for("user.display_user_profile"))
