"""
auth.py

Handles authentication-related requests e.g. `login`, `logout`
Exposes a blueprint that handles requests made to `/auth/*` endpoint

"""

from flask import Blueprint, render_template, request

bp = Blueprint("auth", __name__, url_prefix="")

@bp.route("/")
def login():
    """
    @GET Render the login page if the person isn't logged in, otherwise 
    redirect them to the home page.
    """
    if request.method == "GET":
        return render_template("/auth/login.html")
