"""
auth.py

Handles authentication-related requests e.g. `login`, `logout`
Exposes a blueprint that handles requests made to `/auth/*` endpoint

"""

from flask import Blueprint, render_template, request

bp = Blueprint("auth", __name__, url_prefix="")

@bp.route("/")
def index():
    """
    @GET Render the login page if the person isn't logged in, otherwise 
    redirect them to the home page.
    """
    if request.method == "GET":
        return render_template("/auth/login.html")

"""
Use CAS to login users. Resources:
https://www.cs.princeton.edu/courses/archive/fall18/cos333/lectures/14websecurity/PennyBottleCas/

The code written here should be able to set the username and make it available 
to the rest of the application.

"""

def check_user(username):
    """
    If the user is new, render a page that allows the user to submit details 
    for their account (name, netid, email, phonenumber, room). If the user has 
    logged in before (i.e. we have them in the database) redirect them to 
    `/league/`.

    db.py has a getUser() method that should be helpful

    @param `username`: Set to `None` if no valid user has logged in, otherwise 
    contains the netid of the logged in user.
    """
    return None