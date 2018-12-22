"""
player.py

Exposes a blueprint that handles requests made to `/user/*` endpoint

"""

from flask import Blueprint, render_template, session, request, flash
from . import decorators
from .models import user_model

bp = Blueprint("user", __name__, url_prefix="/user")

@bp.route("/profile/", methods=["GET"])
@decorators.login_required
def display_user_profile():
    """
    Render a template that contains user information. The user should be able to 
    request an update some of the displayed information. The userid will be in 
    the sessions object.
    
    Sample information might include:

    Read-Only: NetID
    Editables: Preferred Name, Preferred Email, Phone Number, Room Number
    Links to leagues that a user is involved in

    """
    return render_template("/user/user_profile.html", user=session.get("user"))

@bp.route("/profile/", methods=["POST"])
@decorators.login_required
def update_user_profile():
    """
    Update the information stored about a user. This method will most likely 
    receive POST requests from the template rendered by user.displayUserProfile

    """
    session["user"] = user_model.update_user_profile(
        session.get("user"), session.get("net_id"), request.form
    )
    flash("User profile updated!")
    return render_template("/user/user_profile.html", user=session.get("user"))
    